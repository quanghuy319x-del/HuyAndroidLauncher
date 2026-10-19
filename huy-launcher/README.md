# Huy android launcher — source-based Lawnchair 15 Beta 3

This independent build is based on the official Lawnchair source at tag `v15.0.0-beta3.0` (commit `505dbc40e6154c05158b5d0271c45f6a885a411b`). The project is an unofficial derivative and is not endorsed by Lawnchair.

## Exact changes

- Android app label: **Huy android launcher**
- Folder **icon** preview: 3 columns × 3 rows, up to 9 items; 1–4 item behavior follows the existing Lawnchair code.
- Original open-folder grid, app dragging, widgets, settings, dock and other upstream features are not intentionally changed.
- Separate package ID: `app.huy.androidlauncher.debug`, so it can coexist with official Lawnchair.
- APK built and signed by the Android Gradle Plugin, not by manually editing APK/Dex/ZIP signatures.

## Build an APK on GitHub

Open [Huy android launcher Actions](https://github.com/quanghuy319x-del/branchline/actions/workflows/build-huy-launcher.yml) and select **Run workflow** if an automatic build is not already running.

Once the run succeeds: **Artifacts → Huy-android-launcher-APK → download ZIP → extract APK → install on phone**. You do **not** need SAI to install this source-built APK.

The GitHub job checks the correct pinned Lawnchair source revision, installs Android SDK 36.1 and Build Tools 36.1.0, applies `huy-launcher/apply_huy.py`, calls the official `./gradlew assembleLawnWithQuickstepPlayDebug`, and verifies the output APK package name and v2/v3 Android signatures.

### Keep updates installable

By default, a GitHub Actions debug build uses an ephemeral debug signing key. **Such APKs might not update one another**. For stable updates, add Actions repository secrets `HUY_KEYSTORE_BASE64` (base64 of your private PKCS12 keystore) and `HUY_KEYSTORE_PASSWORD` (its password), before building the version you intend to keep.

The workflow expects a PKCS12 key alias `huylauncher`. Never commit your keystore/password to a public Git repository.

## Safety / limitations

Your original Lawnchair installation and its layout should remain untouched. The new app starts with its own layout and settings; import your backup only if the launcher's backup format supports it.

**Not tested on a phone.** A successful CI build verifies compilation and APK signing, but does not prove that folder rendering or installation works on the Pixel 5. Do not uninstall your current launcher until the replacement is tested.

For attribution, source code and licensing, see [Lawnchair](https://github.com/LawnchairLauncher/lawnchair).
