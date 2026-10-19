# Pixel Home — Lawnchair-based edition

This edition builds from the **official open-source Lawnchair 16** source, not from the earlier 44 KB proof-of-concept launcher. It is an **unofficial derivative** and is not endorsed by the Lawnchair team.

Upstream: https://github.com/LawnchairLauncher/lawnchair (branch `16-dev`). Lawnchair source remains subject to its own copyright and open-source license (see upstream LICENSE).

## What carries over from Lawnchair
- Native Launcher3 drag/drop, app-on-app folder creation and drag into folders
- Android widgets, resize handles, home-page animations and app icon menus
- Material You/Pixel appearance, theme support and built-in font picker
- Lawnchair's **Deck** mode — no visible app drawer; apps live on home screens

## Additional customizations from patch_lawnchair.py
- Folder icon **previews** display up to 9 icons in a 3×3 grid (the opened folder grid is Lawnchair's native grid).
- Home-screen columns: 3–6; rows: 3–12.
- Deck option and the font picker are visible by default in settings.
- Search bar visibility continues to use Lawnchair's native dock settings.

## Install and setup
1. Back up your existing Lawnchair layout and settings. Deck is still experimental upstream.
2. In GitHub Actions, run **Build Lawnchair-based Pixel Home**, or use the already-triggered build if it succeeds.
3. Download the APK from the Actions build **Artifacts**.
4. This build uses an independent debug signature and **cannot upgrade an official Lawnchair installation in place**; it may need to be installed separately depending on upstream application ID.
5. Open Home settings → Home screen → select **Deck** once to populate all installed apps on the workspace. This intentional user-controlled first-run step avoids silently changing/deleting an existing layout.
6. In Home settings → Home screen grid, set your preferred 3–12 rows and 3–6 columns. Set Google Sans Medium (if available on the device) and size 15 in Lawnchair's font/icon-label settings.

## Important limitations
- This is a **source-based port**, not a binary modification of the specific `Lawnchair.Debug.16-dev.Nightly-CI_5230-85335d9.apk` previously uploaded in a separate conversation. That binary is not mounted in the current workspace.
- The 3×3 preview changes affect multiple upstream animation paths and must be tested on an actual device; Gradle success alone does **not** guarantee fluid animations.
- Google Sans Medium is not bundled; whether it is selectable depends on fonts installed on your device. Google Sans 15 is not yet an enforced default.
- Deck may have known issues (duplicated/missing apps, frozen transitions).
- Do not uninstall the working Lawnchair before the replacement is successfully tested and layout backup is secured.

## Build
The workflow checks out Lawnchair 16 `16-dev` and applies [patch_lawnchair.py](./patch_lawnchair.py), then runs Lawnchair's upstream `assembleLawnWithQuickstepGithubDebug` task. It uploads the resulting APK if compilation succeeds. No APK is claimed unless GitHub Actions confirms success.
