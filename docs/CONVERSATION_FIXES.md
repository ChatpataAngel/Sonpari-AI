<div align="center">

# 🐛 Conversation Regression Fixes

**Recent sample-transcript fixes and why they were needed.**

</div>

---

## 🔍 Root Cause

A phrase that didn't match a direct intent **fell through** to broad keyword rules or a rotating generic fallback. A few rules also treated **all emoji reactions as laughter**.

---

## ✅ Fixed Cases

| Input | Intent now selected | Behavior |
| :-- | :-- | :-- |
| `Hinglish me baat kro na` | `language_preference` | Sets explicit language preference. Telegram stores it in SQLite; terminal mode stores it in a local JSON preferences file |
| `Acha hi hu ji` | `status_good` | Acknowledges status — no longer mistaken for a greeting because of the word `hi` |
| `Kha` | `short_unclear` | Asks whether it was a typo instead of picking a random topic |
| `Hmm` | `thinking_reaction` | Allows time to think or offers topic choices instead of repeating "go on" |
| `Acha ji` (after affection) | `acknowledgement` | Reacts to the previous affectionate reply |
| `Yes` (after a kiss) | `affirmative_followup` | Keeps the answer in the playful kiss context |
| `I wanna eat you out` / `I wanna eat your pussy` | `sexual_flirt` | Acknowledges the flirt explicitly; offers **suggestive, non-graphic** banter rather than pretending not to understand |
| `🌚😚` | `flirty_emoji` | Treated as flirtation — **not** a joke needing explanation |
| `😭😭` | `cry_reaction` | Acknowledges emotion; asks whether comfort is needed |
| `Are you sexual?` / `18+ or not` | `adult_mode_question` | Direct, honest description of the bot's **non-graphic** flirting boundaries |

---

## 🚧 Limits

> This is a **deterministic rule-based system, not a language model.**

Each intent has hand-written patterns and curated response pools. It will handle these tested phrases and similar variations better, but **unexpected wording still needs new examples and tests**. Conversation history used for context lives **in memory** during the running session — it is not a model's semantic understanding.

---

<div align="center">
<sub>See <code>DIALOGUE_RULES.md</code> for how to add new intents and reply packs.</sub>
</div>
