# Huy android launcher 2 — permanent, layout-preserving updates

## What changes

- Official Lawnchair 16 development source pinned to `fc100ae9095a83b8b51c447a3b0a4ce2b399ad59`.
- Folder icon preview: 3x3, smaller icons, 17% edge inset, themed-shape clipping.
- No AccessibilityService/NotificationListener service declarations or `ACCESS_RESTRICTED_SETTINGS` permission, matching the user's Play Protect-tested launcher.
- **Permanent final application ID:** `app.huy.androidlauncher2`.
- **Permanent signing certificate SHA-256:** `36758c6fe2a6cee38c81f2b42f868119b29a5f173e8015cb03ab440c467751d0`.
- APK version codes automatically increase from a fixed base with `GITHUB_RUN_NUMBER`; repeat builds can update in place.
- Workflow refuses builds without a stable signing key, and rejects an unexpected APK signer.

## IMPORTANT: One-time migration from the original debug app

The originally installed Launcher 2 is `app.huy.androidlauncher2.debug` and was signed using an **ephemeral GitHub runner debug key**. Android cannot update that installation without its original signing key. The old app and its data cannot be reliably copied directly to the new app programmatically. **Keep the original installed and back up its data before trying the new APK.**

1. On the phone, open the **original Huy android launcher 2**, go to Lawnchair **Settings > Backup/Restore**, and export a backup of **both layout and settings**. The exact wording varies with the Lawnchair version. Keep another copy of the backup in safe storage.
2. Download the private signing key (`HuyLauncher2_permanent_signing_key.p12`) and the secret-values text file from the ChatGPT conversation; back up both privately. **NEVER commit either file or secret text to this public repository.**
3. On GitHub, open [Repository Actions secrets](https://github.com/quanghuy319x-del/branchline/settings/secrets/actions). Add two repository secrets, copying values from the private file:
   - `HUY2_KEYSTORE_BASE64`: the full *single-line* base64 string after this header.
   - `HUY2_KEYSTORE_PASSWORD`: the password on the line after this header.
4. Open [Build Huy android launcher 2](https://github.com/quanghuy319x-del/branchline/actions/workflows/build-huy-launcher-2.yml) > **Run workflow**.
5. Wait for all GitHub Actions checks to pass. Download **Huy-android-launcher-2-STABLE-APK** from the successful workflow's Artifacts section. Extract `Huy_android_launcher_2_stable.apk`.
6. Install it normally (without SAI), alongside the old debug build. Open the new launcher and import the backup from Step 1.
7. Verify folders, app positions, gestures, settings, and widgets. Android may require re-adding or granting some widgets/permissions after moving between package IDs. Only uninstall the old app when everything is working.

## All later updates

Once you have switched to the stable app (`app.huy.androidlauncher2`), build all new versions using the **same two GitHub Actions secrets and package ID**. Android will recognize subsequent APKs as updates and keep local launcher data, assuming you do not uninstall the app or reset its data. **Back up before major source-version upgrades.**

Signing key files/values are deliberately not included in this repository. GitHub Actions is **manual-only** to avoid building with missing secrets.
