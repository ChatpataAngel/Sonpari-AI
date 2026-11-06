# GitHub release checklist

- [ ] Confirm the Telegram bot token previously present in the v29 archive has been rotated in BotFather.
- [ ] Review every file for credentials, private identifiers, user messages, and personal data.
- [ ] Create public repository `chatpataangel/Sonpari-AI`.
- [ ] Push this clean source tree (not the original v29 ZIP).
- [ ] Confirm GitHub secret scanning reports no exposed credentials.
- [ ] Add a release tag only after running the complete test suite in a clean environment.
- [ ] Do not claim full test coverage until all tests pass.
