# Glass Home v3
Native Android launcher with **no app drawer**: installed apps live on home pages.

- 3×3 folder previews; editable columns 3–6 and rows 3–12.
- Default **Google Sans Medium 15sp** icon labels, selectable font list, font size 8–24sp (platform fallbacks for unavailable fonts).
- Show/hide search bar, swipe search, iPhone-inspired translucent dock, motion effects, themes, app folders and rearranging.
- Very dense 8–12-row home pages scroll vertically instead of cropping labels.

## Get the APK
1. Open **[GitHub Actions – Build Glass Home APK](../../actions/workflows/glass-home-apk.yml)**.
2. Open the latest successful run (or choose **Run workflow**).
3. Under **Artifacts**, download **GlassHome-v3-debug-apk** and extract `app-debug.apk`.
4. Install it on your Android device; then select Glass Home in **Settings → Default apps → Home app**.

## Source
`source.tar.xz` contains the full editable Android project and the interactive `PREVIEW.html`. Extract with `tar -xJf source.tar.xz`; or download **GlassHome-v3-source-preview** from the Actions artifact for the preview and README. The workflow extracts this source and builds it using Gradle 8.9, JDK 17 and Android SDK 35. Java source is editable, no external font files are distributed.

This is an unsigned-for-release **debug APK**, signed using Android's normal debug key and suitable for sideloading. It has not been device-tested.