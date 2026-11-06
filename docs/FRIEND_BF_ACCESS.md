# Friend / BF access model

- The configured `OWNER_ID` is the original owner and always receives BF-style companion replies.
- Everyone else can chat in Friend mode without a pass.
- `/pass <code>` in a private chat compares the supplied code to `OWNER_CODE`. A successful verification stores only `bf_access=1`; the shared code itself is not saved to the user's profile.
- `/unpass` returns a pass holder to Friend mode.
- `/role` shows the current chat tier; `/bfusers` lists BF-tier profiles for the original owner only; `/checkin 1-10` saves a mood score as a mood category.
- BF access changes companion tone only. It does not grant owner-only admin commands or access to another user's private data.

## Configuration

Set `OWNER_ID` to the original owner's numeric Telegram user ID. Set `OWNER_CODE` in the hosting provider's private environment settings. The sample `.env.example` carries the requested initial value `bubuiloveyou`; change it before publishing the archive to anyone who should not know the pass. Send `/pass <code>` only in a private chat with the bot, never in a group.

`SINGLE_USER_MODE` remains in configuration for older installations, but chat availability now follows the Friend/BF model: everyone may chat as a Friend; the owner/pass only changes relationship tone. Administrative commands remain restricted to `OWNER_ID`.
