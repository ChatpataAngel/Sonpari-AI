<div align="center">

# 🔬 Offline Conversational AI — Research & Aiko v26 Integration

**Research snapshot:** 15 October 2026

</div>

> A **broad, curated audit** of representative open-source dialogue engines, companion-persona tools, memory frameworks, datasets, and local inference runtimes. This is not every GitHub repository or online resource — the ecosystem is much too large and changes continuously.

---

## 🎯 Summary — What Fits Aiko's Design

Aiko currently combines:

1. **Deterministic, editable local rules**
2. A **local JSON conversation library**
3. **Lightweight lexical retrieval** over examples and keywords
4. **Explicit local learned trigger-to-reply pairs** and user memory
5. **Optional Groq-hosted generation** for unmatched chat

This deliberately avoids a local language-model runtime and model-weight download. With Groq disabled, Aiko still responds to many common intents offline — but it is **not** a generative neural model and cannot invent an unlimited number of novel, contextually perfect responses.

> 💡 **Key lesson:** response coverage is not just a bigger text dump. It requires sensible intent priority, concise variants, contextual routing, character identity/persona separation, memory boundaries, and license-aware dataset handling.

---

## 🧩 Dialogue Engines & Conversation Architecture

| Project | Contribution | Aiko decision | License / handling |
| :-- | :-- | :-- | :-- |
| [RiveScript Python](https://github.com/aichaos/rivescript-python) | Human-editable trigger/response scripting for chatterbots; good for deterministic personality and pattern coverage | Reuse the general pattern/response idea; keep Aiko's existing Python rules and JSON format rather than adding a second runtime | Reviewed as reference; **no code or reply corpus copied**. Check current upstream project files before integrating separately |
| [AIML Python interpreter](https://github.com/ArtificialIntelligenceToolkit/aiml) | AIML category-based pattern/template responses, and loading a saved rule "brain" | Useful model for adding many auditable categories and testing patterns | Interpreter is 2-clause BSD; repo notes **separate LGPL terms for Free ALICE AIML files**. No interpreter or AIML pack bundled |
| [ChatScript](https://github.com/ChatScript/ChatScript) | Mature pattern/topic scripting approach, including topic-oriented dialogue | Inspiration for keeping topic rules separate and avoiding one monolithic response file | **No ChatScript code, scripts, or data copied.** Review live repository LICENSE before separately reusing files |
| [ChatterBot](https://github.com/gunthercox/ChatterBot) | Retrieval-based engine using collections of known conversations; language-independent corpora can be used for training | Aiko uses a **much smaller, transparent** local keyword/example retrieval step, without installing ChatterBot or a corpus | ChatterBot is BSD-3-Clause. Separate `chatterbot-corpus` has its own licensing; **no upstream corpus text included** |
| [Rasa](https://github.com/RasaHQ/rasa) | Intent/entities separated from dialogue actions, with rules and stories modeling multi-turn paths | Keep direct intents ahead of broad topic catch-alls, plus regression tests for ambiguous overlaps | Apache-2.0; **no Rasa code, runtime, or model bundled** |
| [SillyTavern docs](https://github.com/SillyTavern/SillyTavern-Docs) | Character cards, lorebooks, context, persistent conversation prompts. Docs state SillyTavern needs an LLM backend for generation | Keep Bhawna's fictional persona distinct from learned user facts and dialogue triggers | **No SillyTavern code, community character cards, or chat logs copied** |
| [Letta (formerly MemGPT)](https://github.com/letta-ai/letta) | Stateful agents with explicit memory/context management; memory treated as a distinct system concern | Keep local profile facts, conversation learning, and explicit response rules **separate**; no silent self-modification | Apache-2.0; **no Letta implementation bundled**. It's an LLM agent framework, not a ready-made offline corpus |
| [ParlAI](https://github.com/facebookresearch/ParlAI) | Research framework with multiple dialogue tasks, retrieval, and generative baselines | Used as an **index** for dataset categories and licensing; no ParlAI dependency | **No runtime/model bundled.** Dataset and code licenses must be checked separately per task |

> 🧠 The existing direct rules must remain **in front of** the supplemental router for clear moves — stop/boundary requests, greeting, "what are you doing?", affection, and flirt. The v26 router places specific supplementary topics **before** broad legacy catch-alls only when no protected direct intent matches. Regression tests cover those collisions.

---

## 📊 Dialogue Datasets & Corpora Reviewed

| Resource | Useful research signal | License / decision |
| :-- | :-- | :-- |
| [EmpatheticDialogues](https://github.com/facebookresearch/EmpatheticDialogues) | ~25,000 conversations grounded in emotional situations; includes retrieval baselines; archived | **Not copied.** Review current repo LICENSE and original dataset terms before redistributing |
| [DailyDialog](https://github.com/diixo/daily-dialogs-dataset) | Everyday dialogues with dialogue-act labels (inform/question/directive) and emotion labels (happiness/sadness/anger/fear/surprise) | CC BY-NC-SA 4.0. **Not bundled** — non-commercial / share-alike conditions aren't appropriate for a general response pack |
| [Wizard of Wikipedia](https://github.com/facebookresearch/ParlAI/tree/main/parlai/tasks/wizard_of_wikipedia) | ~201k utterances across 22k knowledge-grounded dialogues on 1,300+ topics; shows knowledge retrieval grounding open-domain turns | CC BY 4.0. **No dialogue text or model bundled.** Attribution and license requirements would need to be maintained if used separately |
| [ConvAI2 / PersonaChat](https://parl.ai/projects/convai2/) | Persona-conditioned chit-chat; keeping consistent persona across turns; archived | Dataset/task terms distinct from ParlAI code license. **Not copied.** Check task-specific terms |
| [Hinglish conversation dataset](https://github.com/skmanish/hinglish-conv-dataset) | Hinglish-focused corpus for training/eval, including lightly flirty conversations. Shows transliterated Hindi/English mixing needs direct coverage | Terms not confidently verified. **None redistributed.** Aiko's new responses are separately authored |
| [ChatterBot Corpus](https://github.com/gunthercox/chatterbot-corpus) | Multi-language examples; guidance on writing short, natural turns with variation | Contribution guide says contributions should be original, not copied from books, movies, songs, proprietary sources, or private conversations. **No corpus items copied** |

### ⚠️ Why not merge the whole datasets?

Repository, model, and dataset licenses can differ **even inside a single project**. A permissively-licensed engine does not grant permission to redistribute every conversation or model weight. Datasets may be research-only, non-commercial, share-alike, or unclear about downstream redistribution. To keep this release auditable, Aiko ships **original-authored responses plus source links and notes — not raw third-party corpora or community character packs**.

---

## 🖥️ Actual Offline Neural Models & Runtimes

Different from rule-based libraries:

| Project / Model | What it does | Aiko decision |
| :-- | :-- | :-- |
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Local CPU/GPU inference for compatible language models, including quantized GGUF; MIT-licensed | **Not installed.** You still need a compatible model and must comply with the model's own license — the runtime license does not cover every model's weights |
| [KoboldCpp](https://github.com/LostRuins/KoboldCpp) | Desktop-friendly local server/UI for GGUF models; can expose an API endpoint | **Not integrated** — this build is meant to stay model-free and no Ollama/KoboldCpp-style runtime was requested. AGPL-3.0 unless a file states otherwise, with separately-licensed components |
| [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B) | Downloadable instruction/chat model; multilingual; Apache-2.0 for this checkpoint | **Research reference only.** Weights and local inference dependencies not included or downloaded. Hardware needs depend on quantization, context length, runtime |
| [Pygmalion-3 12B model card](https://huggingface.co/PygmalionAI/Pygmalion-3-12B) | Roleplay-oriented conversational model, Apache-2.0 per this specific model card | **Research reference only.** A 12B model is a different resource profile from Aiko's rule engine — would require local weights/runtime |
| [KoboldCpp model guidance](https://github.com/LostRuins/KoboldCpp) | Documents GGUF downloads and roleplay-oriented choices; the project does not bundle a ready-to-run model | **No model, weights, or executable embedded** |

> 🎯 **Aiko is offline-capable local dialogue logic with optional hosted generation — not a standalone generative offline LLM.** If completely private free-form generation later becomes a requirement, a separate opt-in local-model adapter would be a **new architectural choice** — not something a conversation text pack can achieve by itself.

---

## 🆕 What Was Added in v26

### `aiko/conversation_library.json`

- **94 unique supplemental topics**
- **567 original static response variants** across Hinglish, Hindi, and English
- Includes the 23 previous entries plus **71 new topics**

**Added topic groups:**

> Friendship/family conflict · breakups/crushes/rejection · confidence & social anxiety · interview & exam preparation · career questions · focus/productivity · coding/technical help · writing/creative blocks · language learning · explanations · brainstorming · trip planning · pets · cooking · workouts · habit-building · boundaries/trust · opinions/disagreement · games/riddles/stories/roleplay · late-night/rain/weekend chat · preferences · accountability · feedback · budgeting · celebrations · emotional support

### `aiko/conversation_hub.py`

Local, data-driven pattern layer and lexical retrieval from topic keywords/examples. **No network or embedding dependency.** Ambiguous lexical matches fall through instead of pretending to understand confidently.

### `aiko/dialogue.py`

Added a specific-topic pre-router, guarded by established direct-turn intents so it cannot replace clear commands, greetings, romance, or boundaries. Runs **before** broad catch-alls that might accidentally trigger on a word like "lunch" appearing inside a longer emotional sentence.

### Regression tests

Validate the schema, breadth/count, topic-specific paraphrases, language pools, and preservation of core flirt/greeting/boundary flows.

> ✍️ The 567 response strings are **authored for this release**, not copies from the datasets above. The supplemental library has finite responses; variation comes from several templates per intent, safe capture of selected user-provided options, and selection that avoids repeating the exact previous bot response when alternatives exist.

---

## ➕ How to Add More Replies

Add a new entry in `aiko/conversation_library.json` with:

- A unique `intent`
- Narrow regex `patterns`
- Several original `examples`
- Useful `keywords`
- Non-empty response lists for `hinglish`, `hi`, and `en`

### Guidelines

- **Prefer narrow patterns.**
- **Test overlaps** against greetings, romance, comfort, commands, and existing core topics.
- **Never** store private chats or API keys as training examples.

### Run checks

```bash
python -m pytest -q --ignore=tests/test_database.py
python scripts/check_dialogue_rules.py
```

> The database test is excluded above **only** because some dev environments lack the optional `aiosqlite` dependency. In a fully installed environment, run the whole suite with `python -m pytest -q`.

---

## 🛡️ Limits & Privacy

- **No external project code** or **third-party dialogue dataset text** is embedded. The response pack is original; linked research sources are documented.
- The lexical retrieval step is **not** semantic AI. Local rule responses cannot cover every imaginable sentence. Groq can generate more open-domain responses when enabled, but **those fallback prompts go to a hosted service**. Set `GROQ_ENABLED=false` for response logic to remain local.
- Conversation text, local memory, and user facts remain subject to Aiko's existing storage/privacy settings. Review `.env.example` and the README before enabling any hosted feature.
- **Telegram still needs internet** to communicate with Telegram, even if response logic is local.

---

<div align="center">
<sub>See <code>PRIVACY.md</code> for what data leaves the host and how to disable it.</sub>
</div>
