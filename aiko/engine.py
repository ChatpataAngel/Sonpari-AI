from __future__ import annotations
import random, re, string, time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml
from .utils import weighted_choice
from .text_style import normalize_for_matching

@dataclass
class CompiledRule:
    data: dict[str,Any]
    patterns: list[re.Pattern]
@dataclass
class MatchResult:
    rule_id: str
    priority: int
    weight: float
    response: str
    rule: dict[str,Any]
    score: float
    responses: list[str]  # language-specific pool used to pick the response

class SafeDict(dict):
    def __missing__(self,key): return "{"+key+"}"
class ResponseEngine:
    def __init__(self, persona: dict, rules_paths: str | Path | list[str], rng: random.Random | None = None):
        self.persona=persona; self.rng=rng or random.Random()
        self.rules=[]; self.reflections=[]; self.fallbacks=[]; self.proactive=[]
        self.cooldowns={}
        self.translations={}
        if isinstance(rules_paths,(str,Path)):
            rules_paths=[str(rules_paths)]
        else:
            rules_paths=[str(p) for p in rules_paths]
        self.rules_paths=rules_paths
        self.load_rules(rules_paths)

    def load_rules(self,paths:list[str]):
        compiled=[]; seen=set()
        primary_data=None
        for path in paths:
            try: data=yaml.safe_load(Path(path).read_text(encoding="utf-8"))
            except Exception as exc: raise ValueError(f"Unable to load rules file {path}: {exc}") from exc
            if not isinstance(data,dict) or not isinstance(data.get("rules"),list): raise ValueError(f"rules file {path} must contain a rules list")
            if primary_data is None:
                primary_data=data
            for raw in data["rules"]:
                if not isinstance(raw,dict) or not raw.get("id"): raise ValueError(f"Each rule must be a mapping with an id")
                rid=str(raw["id"])
                if rid in seen: raise ValueError(f"Duplicate rule id: {rid}")
                seen.add(rid)
                pats=raw.get("patterns",[])
                if not pats: raise ValueError(f"Rule {rid} has no patterns")
                try: regexes=[re.compile(p,re.IGNORECASE) for p in pats]
                except re.error as exc: raise ValueError(f"Invalid regex in rule {rid}: {exc}") from exc
                if not isinstance(raw.get("responses"),list) or not raw["responses"]: raise ValueError(f"Rule {rid} needs responses")
                compiled.append(CompiledRule(raw,regexes))
        self.rules=sorted(compiled,key=lambda r:int(r.data.get("priority",0)),reverse=True)
        # reflection_rules, fallbacks and proactive are taken from the primary (first) rules file only,
        # so multiple configured rule files do not repeat or silently drop metadata.
        self.reflections=[]
        for item in (primary_data or {}).get("reflection_rules",[]):
            try: self.reflections.append((re.compile(item["pattern"],re.I),item["responses"]))
            except (KeyError,re.error) as exc: raise ValueError(f"Invalid reflection rule: {exc}") from exc
        self.fallbacks=(primary_data or {}).get("fallbacks",[])
        self.proactive=(primary_data or {}).get("proactive",[])
        self.translations={}
        for lang in ("hi","hinglish"):
            for path in paths:
                p=Path(path)
                tpath=p.with_name(p.stem+"."+lang+p.suffix)
                if not tpath.is_file(): continue
                try: tdata=yaml.safe_load(tpath.read_text(encoding="utf-8"))
                except Exception as exc: raise ValueError(f"Unable to load translation file {tpath}: {exc}") from exc
                if not isinstance(tdata,dict): raise ValueError(f"Translation file {tpath} must contain a mapping")
                tr={}
                rules_map=tdata.get("rules") or {}
                if not isinstance(rules_map,dict): raise ValueError(f"Translation file {tpath}: 'rules' must be a mapping of id to responses")
                clean_rules={}
                for rid,resps in rules_map.items():
                    if not isinstance(resps,list) or not resps or not all(isinstance(x,str) for x in resps):
                        raise ValueError(f"Translation file {tpath}: rule '{rid}' must be a non-empty list of strings")
                    clean_rules[str(rid)]=resps
                tr["rules"]=clean_rules
                refl_map=tdata.get("reflection_rules") or {}
                if not isinstance(refl_map,dict): raise ValueError(f"Translation file {tpath}: 'reflection_rules' must be a mapping")
                clean_refl={}
                for pat,resps in refl_map.items():
                    if not isinstance(resps,list) or not resps or not all(isinstance(x,str) for x in resps):
                        raise ValueError(f"Translation file {tpath}: reflection '{pat}' must be a non-empty list of strings")
                    clean_refl[str(pat)]=resps
                tr["reflection_rules"]=clean_refl
                fallbacks=tdata.get("fallbacks") or []
                if not isinstance(fallbacks,list) or not all(isinstance(x,str) for x in fallbacks):
                    raise ValueError(f"Translation file {tpath}: 'fallbacks' must be a list of strings")
                tr["fallbacks"]=fallbacks
                proactive=tdata.get("proactive") or []
                if not isinstance(proactive,list) or not all(isinstance(x,str) for x in proactive):
                    raise ValueError(f"Translation file {tpath}: 'proactive' must be a list of strings")
                tr["proactive"]=proactive
                self.translations[lang]=tr

    def _state_ok(self, rule, state):
        req=rule.get("requires_state",{})
        return state.get("affection",0)>=int(req.get("affection_min",0)) and state.get("affection",0)<=int(req.get("affection_max",100))
    def match(self,message:str,user_state:dict|None=None,user_id:int|None=None,now:float|None=None,lang:str="en")->MatchResult|None:
        state=user_state or {}; now=now or time.time(); matches=[]
        # Keep source text untouched at the call site; only normalize the matcher
        # view so YAML rules can understand short forms and stretched letters too.
        match_message = normalize_for_matching(message)

        for item in self.rules:
            rule=item.data; rid=rule["id"]
            if not self._state_ok(rule,state): continue
            cd=float(rule.get("cooldown_seconds",0))
            last=self.cooldowns.get((user_id,rid),0)
            if user_id is not None and cd and now-last<cd: continue
            match=next((m for p in item.patterns if (m:=p.search(match_message))),None)
            if match:
                captures=match.groups()
                matches.append((item,match,captures))
        if not matches: return None
        top=max(int(x[0].data.get("priority",0)) for x in matches)
        tier=[x for x in matches if int(x[0].data.get("priority",0))==top]
        chosen=weighted_choice(tier,[float(x[0].data.get("weight",1.0)) for x in tier],self.rng)
        item,match,captures=chosen; rule=item.data
        if user_id is not None: self.cooldowns[(user_id,rule["id"])]=now
        pool=self._responses_for(rule["id"],rule["responses"],lang)
        response=self.rng.choice(pool)
        thing=captures[0] if captures else ""
        return MatchResult(rule["id"],int(rule.get("priority",0)),float(rule.get("weight",1.0)),response,rule,float(top)+float(rule.get("weight",1.0)),pool)

    def _responses_for(self,rule_id:str,default:list[str],lang:str)->list[str]:
        tr=self.translations.get(lang)
        if tr:
            pool=tr["rules"].get(rule_id)
            if pool: return pool
        return default

    def _fallbacks_for(self,lang:str)->list[str]:
        tr=self.translations.get(lang)
        if tr and tr["fallbacks"]: return tr["fallbacks"]
        return self.fallbacks or ["hmm, tell me more~"]

    def _proactive_for(self,lang:str)->list[str]:
        tr=self.translations.get(lang)
        if tr and tr["proactive"]: return tr["proactive"]
        return self.proactive or ["hey {pet}~ just thinking of you 💗"]

    def render(self,template:str,context:dict[str,Any]|None=None,lang:str="en")->str:
        ctx=dict(context or {})
        style=self.persona.get("speech_style",{})
        pet_pool=self._pet_names_for(lang)
        ctx.setdefault("pet",self.rng.choice(pet_pool))
        ctx.setdefault("name",ctx.get("stored_name") or ctx["pet"])

        ctx.setdefault("mood","neutral"); ctx.setdefault("time_of_day","evening")
        try: result=template.format_map(SafeDict(ctx))
        except (ValueError,AttributeError): result=template
        if style.get("lowercase",True): result=result.lower()
        freq=style.get("emoji_frequency","medium")
        emojis=style.get("signature_emojis",[])
        if emojis and freq=="high" and not any(e in result for e in emojis) and self.rng.random()<0.28:
            result += " " + self.rng.choice(emojis)
        elif emojis and freq=="medium" and self.rng.random()<0.12 and not any(e in result for e in emojis):
            result += " " + self.rng.choice(emojis)
        if style.get("uses_tildes",True) and not result.endswith(("~","!","?","…")) and self.rng.random()<0.12: result += "~"
        return result.strip()
    def _pet_names_for(self,lang:str)->list[str]:
        style=self.persona.get("speech_style",{})
        if lang=="hi" and style.get("pet_names_hi"): return style["pet_names_hi"]
        if lang=="hinglish" and style.get("pet_names_hinglish"): return style["pet_names_hinglish"]
        return style.get("pet_names",["love"])
    def get_fallback(self,context=None,lang:str="en")->str:
        return self.render(self.rng.choice(self._fallbacks_for(lang)),context,lang)
    def apply_reflection(self,message:str,context:dict|None=None,lang:str="en")->str|None:
        tr=self.translations.get(lang)
        tr_refl=tr["reflection_rules"] if tr else {}
        match_message = normalize_for_matching(message)
        for pattern,responses in self.reflections:
            m=pattern.search(match_message)
            if m:
                ctx=dict(context or {}); ctx["thing"]=m.group(1).strip()
                pool=tr_refl.get(pattern.pattern) or responses
                return self.render(self.rng.choice(pool),ctx,lang)
        return None
    def debug_match(self,message,user_state=None,user_id=None,lang:str="en"):
        # Do not consume cooldowns or alter state during debugging.
        result=self.match(message,user_state,user_id=None,lang=lang)
        return result
