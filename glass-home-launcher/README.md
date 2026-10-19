# Pixel Home v4 — no app drawer

A native Android home launcher with Pixel-inspired styling and behavior, except **all apps remain on home-screen pages; there is no app drawer**.

Features: system wallpaper, circular icons, uncluttered dock, bottom app-search pill (show/hide), At a Glance date, 3×3 folder previews, drag app onto app to make folders or onto existing folders to add apps, page-edge drag navigation, and native **Android AppWidgetHost** support for live widgets (add, resize, remove).

Grid: 3–6 columns, 3–12 rows. App-label fonts selectable (default Google Sans Medium at 15sp, fallback where unavailable). App text size 8–24sp. Layout and widgets persist locally.

## Download APK
Open [Actions → Build Glass Home APK](../../actions/workflows/glass-home-apk.yml), select the newest successful run, then download the **PixelHome-v4-debug-apk** artifact and extract `app-debug.apk`.

## Source code
Download `source.tar.xz` from this folder and extract with `tar -xJf source.tar.xz`. The source includes full editable Android Studio project and `PREVIEW.html` (illustrative interactive web preview). The build workflow unpacks and builds this archive.

Minimum Android 8.0 (API 26). Debug-signed APK. The Android widget provider permissions are requested by Android as needed. Proprietary Google feed/special provider integrations are not provided. Device behavior and third-party widget compatibility have not yet been tested.
