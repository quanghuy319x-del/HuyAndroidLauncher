# Huy android launcher 2 — permanent, layout-preserving updates

## Current features

- Pinned Lawnchair 16 source with iOS-style 3x3 folder previews, three-column opened folders, glass dock/folder, and optional real backdrop blur.
- Original Lawnchair 2 package ID: `app.huy.androidlauncher2`.
- Permanent signing certificate SHA-256: `36758c6fe2a6cee38c81f2b42f868119b29a5f173e8015cb03ab440c467751d0`.
- Unsafe Accessibility/NotificationListener declarations remain excluded.
- `GITHUB_RUN_NUMBER` increases the app version code for in-place updates.

## Faster GitHub builds (October 2026)

**Default workflow:** [Build Huy Launcher 2 optimized APK](https://github.com/quanghuy319x-del/branchline/actions/workflows/build-huy2-backup-restore.yml).

1. On every `huy-launcher-2/apply_huy2.py` change, only **one** automatic compile workflow runs. The old full source check is manual-only. Earlier running builds are cancelled on superseding commits.
2. The pinned Lawnchair source is still checked out fresh, but `actions/cache@v4` restores the `upstream-lawnchair/.gradle` incremental state and `upstream-lawnchair/build` outputs from the last successful run.
3. Gradle is started with `--build-cache --parallel --max-workers=4`, and `gradle/actions/setup-gradle` also caches dependency and task artifacts.
4. **If permanent GitHub Actions repository secrets exist**, the workflow signs the APK with `HUY2_KEYSTORE_BASE64` and `HUY2_KEYSTORE_PASSWORD`, verifies the expected SHA-256 **certificate** fingerprint, then uploads `Huy-Launcher-2-PERMANENT-SIGNED-APK`.
5. **If the secrets are missing**, the output is explicitly named `Huy-Launcher-2-DEBUG-INTERMEDIATE-APK` and **must not be installed** over an existing permanently signed app. The private key stays outside the repository; sign the intermediate offline instead.

**Performance baseline:** Three previous successful Gradle builds took 168s, 291s and 306s (entire GitHub runs around 4–6 minutes). Cache warming can take one full run, and cache upload/download consumes time. Measure at least one later run before making performance claims.

**Important:** GitHub cache is an optimization, not a substitute for correct version code, package ID, signatures or integrity checks. Builds still verify the merged APK manifest and restrictions. APKs are not declared installable until verification passes.

## IMPORTANT: One-time migration from the original debug app

The originally installed Launcher 2 is `app.huy.androidlauncher2.debug` and was signed using an **ephemeral GitHub runner debug key**. Android cannot update that installation without its original signing key. The old app and its data cannot be reliably copied directly to the new app programmatically. **Keep the original installed and back up its data before trying the new APK.**

1. On the phone, open the **original Huy android launcher 2**, go to Lawnchair **Settings > Backup/Restore**, and export a backup of **both layout and settings**. The exact wording varies with the Lawnchair version. Keep another copy of the backup in safe storage.
2. Download the private signing key (`HuyLauncher2_permanent_signing_key.p12`) and the secret-values text file from the ChatGPT conversation; back up both privately. **NEVER commit either file or secret text to this public repository.**
3. On GitHub, open [Repository Actions secrets](https://github.com/quanghuy319x-del/branchline/settings/secrets/actions). Add two repository secrets, copying values from the private file:
   - `HUY2_KEYSTORE_BASE64`: the full *single-line* base64 string after this header.
   - `HUY2_KEYSTORE_PASSWORD`: the password on the line after this header.
4. Open [Build Huy Launcher 2 optimized APK](https://github.com/quanghuy319x-del/branchline/actions/workflows/build-huy2-backup-restore.yml) > **Run workflow**.
5. Wait for all checks to pass and download the **Huy-Launcher-2-PERMANENT-SIGNED-APK** artifact. Extract its verified APK.
6. Install it normally (without SAI), alongside the old debug build. Open the new launcher and import the backup from Step 1.
7. Verify folders, app positions, gestures, settings, and widgets. Android may require re-adding or granting some widgets/permissions after moving between package IDs. Only uninstall the old app when everything is working.

## All later updates

Once you have switched to the stable app (`app.huy.androidlauncher2`), build all new versions using the **same two GitHub Actions secrets and package ID**. Android will recognize subsequent APKs as updates and keep local launcher data, assuming you do not uninstall the app or reset its data. **Back up before major source-version upgrades.**

Signing key files/values are deliberately not included in this repository. The optimized workflow runs automatically on changes and can also be started manually. Without secrets, it outputs a **debug intermediate**, not an update-ready APK.
