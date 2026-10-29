# Personal macOS distribution

All Developer ID build, signing, notarization and GitHub release orchestration runs here on `macos-signing`.
The upstream repository never calls or waits for this workflow and receives no credentials or DMG uploads.

The schedule checks the newest upstream tag every 30 minutes. Run **Signed macOS distribution** manually with an upstream tag to select a specific version. Tags must belong to upstream main or preview. Existing published personal releases are skipped; failed runs can be rerun independently.

Source is checked out from the exact upstream tag commit. Signing code, entitlements and `.github/macos-signing.json` come from this branch. Update the explicit Mac version/build here before a Mac version change. The unsigned compile job gets no signing credentials. The sign job uses the seven repository secrets, verifies signature and notarization, and publishes `macos-<upstream-tag>` only here. Both staple and validate retry three times, waiting 10 and 20 seconds. No unsigned fallback is published.

Downloads: https://github.com/wjlfish/Bugaoshan-macos/releases
