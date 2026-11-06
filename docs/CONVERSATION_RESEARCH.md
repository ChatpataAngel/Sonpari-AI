# Offline conversational AI research and Aiko v26 integration notes

**Research snapshot:** 15 October 2026. This is a broad, curated audit of representative open-source dialogue engines, companion-persona tools, memory frameworks, datasets, and local inference runtimes. It is not literally every GitHub repository or every online resource; the ecosystem is much too large and changes continuously.

## Summary: what fits Aiko's design

Aiko currently combines (1) deterministic, editable local rules; (2) a local JSON conversation library; (3) lightweight lexical retrieval over examples and keywords; (4) explicit local learned trigger-to-reply pairs and user memory; and (5) optional Groq-hosted generation for unmatched chat. This deliberately avoids a local language-model runtime and model-weight download. With Groq disabled, Aiko still responds to many common intents offline, but it is not a generative neural model and cannot invent an unlimited number of novel, contextually perfect responses.

The key lesson from the projects reviewed is that response coverage is not just a bigger text dump. It requires sensible intent priority, concise variants, contextual routing, character identity/persona separation, memory boundaries, and license-aware dataset handling.

## Dialogue engines and conversation architecture

| Project | What it contributes | Aiko decision | License/handling |
|---|---|---|---|
| [RiveScript Python](https://github.com/aichaos/rivescript-python) | Human-editable trigger/response scripting for chatterbots; good for deterministic personality and pattern coverage. | Reuse the general pattern/response design idea; Aiko keeps its existing Python rules and JSON format rather than adding a second runtime. | Reviewed as a project reference; no code or reply corpus copied. Check current upstream project files before integrating its code separately. |
| [AIML Python interpreter](https://github.com/ArtificialIntelligenceToolkit/aiml) | AIML category-based pattern/template responses and a way to load a saved rule “brain.” | Useful model for adding many auditable categories and testing patterns. | The interpreter is described as 2-clause BSD, but the repo notes separate LGPL terms for the Free ALICE AIML files. No interpreter or AIML pack is bundled. |
| [ChatScript](https://github.com/ChatScript/ChatScript) | Mature pattern/topic scripting approach, including topic-oriented dialogue. | Inspiration for keeping topic rules separate and avoiding one monolithic response file. | No ChatScript code, scripts, or data are copied. Review its live repository LICENSE before separately reusing files. |
| [ChatterBot](https://github.com/gunthercox/ChatterBot) | Retrieval-based conversational engine using collections of known conversations; its project says language-independent corpora can be used for training. | Aiko uses a much smaller, transparent local keyword/example retrieval step, without installing ChatterBot or a corpus. | ChatterBot code is BSD-3-Clause. The separate `chatterbot-corpus` has its own licensing and contribution terms; no upstream corpus text is included. |
| [Rasa](https://github.com/RasaHQ/rasa) | Intent/entities separated from dialogue actions, with rules and stories that model multi-turn paths. | Aiko keeps direct intents ahead of broad topic catch-alls and adds regression tests for ambiguous overlaps. | Rasa is Apache-2.0; no Rasa code, runtime, or model is bundled. |
| [SillyTavern documentation](https://github.com/SillyTavern/SillyTavern-Docs) | Character cards, lorebooks, context and persistent conversation prompts. The project documentation says SillyTavern is an interface and needs an LLM backend for generation. | Keep Bhawna's fictional persona distinct from learned user facts and dialogue triggers. | No SillyTavern code, downloadable community character cards, or chat logs are copied. |
| [Letta (formerly MemGPT)](https://github.com/letta-ai/letta) | Stateful agents with explicit memory/context management; memory is treated as a distinct system concern. | Keep local profile facts, conversation learning, and explicit response rules separate; no silent self-modification. | Letta's current repository is Apache-2.0; no Letta implementation is bundled. It is an LLM agent framework, not a ready-made offline dialogue corpus. |
| [ParlAI](https://github.com/facebookresearch/ParlAI) | Research framework with multiple dialogue tasks, retrieval and generative baselines. | Used as an index for understanding dataset categories and licensing; Aiko does not add a ParlAI dependency. | No ParlAI runtime/model is bundled. Dataset and code licences must be checked separately per task. |

The existing direct rules must remain in front of the supplemental router for clear moves such as stop/boundary requests, greeting, “what are you doing?”, affection, and flirt. The v26 router places specific supplementary topics before broad legacy catch-alls only when a protected direct intent does not match. Regression tests cover those collisions.

## Dialogue datasets and corpora reviewed

| Resource | Useful research signal | License / decision |
|---|---|---|
| [EmpatheticDialogues](https://github.com/facebookresearch/EmpatheticDialogues) | Research dataset of roughly 25,000 conversations grounded in emotional situations; project includes retrieval-based baselines and is archived. | The dataset and example turns are **not** copied into Aiko. Review the current repository LICENSE and original dataset terms before redistributing. |
| [DailyDialog](https://github.com/diixo/daily-dialogs-dataset) | Everyday dialogues with dialogue-act labels (e.g. inform/question/directive) and emotion labels (e.g. happiness/sadness/anger/fear/surprise). | The referenced dataset card identifies CC BY-NC-SA 4.0. Not bundled, because the non-commercial/share-alike conditions are not appropriate for indiscriminately merging into a general response pack. |
| [Wizard of Wikipedia task](https://github.com/facebookresearch/ParlAI/tree/main/parlai/tasks/wizard_of_wikipedia) | About 201k utterances across 22k knowledge-grounded dialogues on 1,300+ topics; demonstrates how knowledge retrieval can ground open-domain turns. | The task README identifies CC BY 4.0. No dialogue text or model is bundled. Attribution and licence requirements would need to be maintained if using it separately. |
| [ConvAI2 / PersonaChat](https://parl.ai/projects/convai2/) | Persona-conditioned chit-chat and examples of keeping a consistent persona across turns; the competition task is archived. | Dataset/task terms are distinct from the ParlAI code licence. Not copied into Aiko; check task-specific terms before use. |
| [Hinglish conversation dataset](https://github.com/skmanish/hinglish-conv-dataset) | A Hinglish-focused corpus generated for model training/evaluation and including lightly flirty conversations. It demonstrates that transliterated Hindi and English mixing needs direct coverage. | Its exact terms were not confidently verified in this research pass, so none of its conversation data is redistributed. Aiko's new responses are separately authored. |
| [ChatterBot Corpus](https://github.com/gunthercox/chatterbot-corpus) | Multi-language examples and guidance on writing short, natural conversational turns with response variation. | Its contribution guide says contributions should be original and not copied from books, movies, songs, proprietary sources or private conversations. Aiko's additions are original text; no corpus items are copied. |

### Why not simply merge the whole datasets?

Repository licences, model licences, and dataset licences can differ even inside a single project. A permissively licensed engine does not automatically grant permission to redistribute every conversation or model weight. Datasets may also be research-only, non-commercial, share-alike, or unclear about downstream redistribution. To keep this release auditable, it includes original Aiko-authored responses plus source links and notes—not raw third-party corpora or community character packs.

## Actual offline neural models and runtimes

These are different from rule-based dialogue libraries:

| Project/model | What it does | Aiko decision |
|---|---|---|
| [llama.cpp](https://github.com/ggml-org/llama.cpp) | Local CPU/GPU inference for compatible language models, including quantized GGUF models; its project is MIT-licensed. | Not installed. You still need to download a compatible model and comply with the model's own licence; the runtime licence does not cover every model's weights. |
| [KoboldCpp](https://github.com/LostRuins/KoboldCpp) | Desktop-friendly local server/UI for GGUF models; can expose an API endpoint for a separate chat application. | Not integrated because this Aiko build is meant to stay model-free and no Ollama/KoboldCpp-style runtime was requested. Its code is AGPL-3.0 unless a file states otherwise, with separately licensed components. |
| [Qwen3-4B model card](https://huggingface.co/Qwen/Qwen3-4B) | A downloadable instruction/chat model; its model card reports multilingual support and Apache-2.0 for this specific checkpoint. | Research reference only. Its weights and local inference dependencies are not included or downloaded. Hardware needs depend on quantization, context length, and runtime. |
| [Pygmalion-3 12B model card](https://huggingface.co/PygmalionAI/Pygmalion-3-12B) | Roleplay-oriented conversational model, released under Apache 2.0 according to this specific model card. | Research reference only. A 12B model is a different resource profile from Aiko's current rule engine and would require local weights/runtime. |
| [KoboldCpp model guidance](https://github.com/LostRuins/KoboldCpp) | Documents GGUF model downloads and roleplay-oriented choices; the project itself does not bundle a ready-to-run language model. | No model, weights, or executable is embedded in Aiko. |

Aiko is therefore **offline-capable local dialogue logic with optional hosted generation**, not a standalone generative offline LLM. If completely private free-form generation later becomes a requirement, a separate opt-in local-model adapter would be a new architectural choice—not something a conversation text pack can achieve by itself.

## What was added in Aiko v26

- `aiko/conversation_library.json`: **94 unique supplemental topics** with **567 original static response variants** across Hinglish, Hindi, and English. It includes the 23 previous entries plus 71 new topics. Added topic groups include friendship/family conflict, breakups/crushes/rejection, confidence and social anxiety, interview and exam preparation, career questions, focus/productivity, coding/technical help, writing/creative blocks, language learning, explanations, brainstorming, trip planning, pets, cooking, workouts, habit-building, boundaries/trust, opinions/disagreement, games/riddles/stories/roleplay, late-night/rain/weekend chat, preferences, accountability, feedback, budgeting, celebrations and emotional support.
- `aiko/conversation_hub.py`: keeps a local, data-driven pattern layer and lexical retrieval from topic keywords/examples. It has no network or embedding dependency. Ambiguous lexical matches fall through instead of pretending to understand confidently.
- `aiko/dialogue.py`: added a specific-topic pre-router, guarded by established direct-turn intents so it cannot replace clear commands, greetings, romance or boundaries. It runs before broad catch-all topics that might accidentally trigger because a word like “lunch” appears in a longer emotional sentence.
- Regression tests validate the schema, breadth/count, topic-specific paraphrases, language pools, and preservation of core flirt/greeting/boundary flows.

The 567 response strings are authored for this release, not copies from the datasets above. The supplemental library has finite responses; variation comes from several templates per intent, safe capture of selected user-provided options, and selection that avoids repeating the exact previous bot response when alternatives exist.

## How to add more replies

Add a new entry in `aiko/conversation_library.json` with a unique `intent`, narrow regex `patterns`, several original `examples`, useful `keywords`, and non-empty response lists for `hinglish`, `hi`, and `en`. Prefer narrow patterns and test overlaps against greetings, romance, comfort, commands and existing core topics. Never store private chats or API keys as training examples. Run:

```bash
python -m pytest -q --ignore=tests/test_database.py
python scripts/check_dialogue_rules.py
```

The database test is excluded above only because some development environments don't have the optional `aiosqlite` dependency installed; in a fully installed environment run the whole suite with `python -m pytest -q`.

## Limits and privacy

- No external project code or third-party dialogue dataset text is embedded in this v26 release; the response pack is original and linked research sources are documented.
- The lexical retrieval step is not semantic AI, and local rule responses cannot cover every imaginable sentence. Groq can generate more open-domain responses when enabled, but those fallback prompts go to a hosted service. Set `GROQ_ENABLED=false` for Aiko's response logic to remain local.
- Conversation text, local memory and user facts remain subject to Aiko's existing storage/privacy settings. Review `.env.example` and the README before enabling any hosted feature.
- Telegram itself still needs internet to communicate with Telegram, even if response logic is local.
