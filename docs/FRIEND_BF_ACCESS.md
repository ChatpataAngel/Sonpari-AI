<div align="center">

# 👥 Friend / BF Access Model

**Everyone can chat. The owner — or a pass holder — gets a warmer tone.**

</div>

---

## 🎭 Tiers at a Glance

| Tier | How you get it | What changes |
| :-- | :-- | :-- |
| **Friend** | Default for everyone | Standard companion replies |
| **BF** | You are the configured `OWNER_ID`, **or** you enter the correct `OWNER_CODE` | BF-style companion tone |

> BF access changes **companion tone only**. It does not grant owner-only admin commands or access to another user's private data.

---

## 🔑 Commands

| Command | Effect |
| :-- | :-- |
| `/pass <code>` | In a private chat, compares code to `OWNER_CODE`. On success, stores `bf_access=1` only — the code itself is **never saved** to the profile |
| `/unpass` | Returns a pass holder to Friend mode |
| `/role` | Shows current chat tier |
| `/bfusers` | Lists BF-tier profiles — **original owner only** |
| `/checkin 1-10` | Saves a mood score as a mood category |

---

## ⚙️ Configuration

| Variable | Purpose |
| :-- | :-- |
| `OWNER_ID` | Original owner's numeric Telegram user ID. Always receives BF-style replies |
| `OWNER_CODE` | Shared pass code for BF access — set in the hosting provider's **private** environment settings |

> ⚠️ The sample `.env.example` carries the requested initial value `bubuiloveyou`. **Change it before publishing** the archive to anyone who should not know the pass.

> 🔒 Send `/pass <code>` **only in a private chat** with the bot — **never in a group**.

---

## 🗂️ A Note on `SINGLE_USER_MODE`

`SINGLE_USER_MODE` remains in configuration for older installations, but chat availability now follows the Friend / BF model:

- **Everyone** may chat as a Friend.
- The owner or a valid pass only **changes relationship tone**.
- **Administrative commands remain restricted to `OWNER_ID`.**

---

<div align="center">
<sub>See <code>PRIVACY.md</code> for how <code>OWNER_CODE</code> and <code>bf_access</code> are stored.</sub>
</div>
