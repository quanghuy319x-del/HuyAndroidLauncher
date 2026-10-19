#!/usr/bin/env python3
"""Customize official Lawnchair 16-dev source for Huy android launcher 2.

Pinned upstream commit: fc100ae9095a83b8b51c447a3b0a4ce2b399ad59
Changes: 3x3 folder icon preview, app label and isolated ID,
and the exact privacy permission reductions confirmed on Launcher 1.
No APK/Dex binary rewriting.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()


def change(path, old, new):
    target = root / path
    body = target.read_text(encoding="utf-8")
    count = body.count(old)
    if count != 1:
        raise RuntimeError(f"Expected one match ({count} found) for {path}: {old[:95]!r}")
    target.write_text(body.replace(old, new, 1), encoding="utf-8")
    print("Modified", path)

layout = "src/com/android/launcher3/folder/ClippedFolderIconLayoutRule.java"
organizer = "src/com/android/launcher3/folder/FolderGridOrganizer.java"

change(layout,
       "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 4;",
       "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 9;")

# Preserve Lawnchair's 1-4 icon positions. For 5-9, use three equally spaced
# rows/columns with 17% outer padding and smaller icons, as in iOS folder previews.
# The rounded/circular corners must be respected, not merely the square bounds.
change(layout,
       "        // The case of two items is homomorphic to the case of one.\n",
       """        if (curNumItems > 4 && index >= 0) {
            final float inset = mAvailableSpace * 0.17f;
            final float cellSize = (mAvailableSpace - inset * 2f) / 3f;
            final float drawnSize = mIconSize * scaleForItem(curNumItems, 0);
            final int row = index / 3;
            final int col = mIsRtl ? 2 - (index % 3) : index % 3;
            result[0] = inset + (col + 0.5f) * cellSize - drawnSize / 2f;
            result[1] = inset + (row + 0.5f) * cellSize - drawnSize / 2f;
            return;
        }
        // The case of two items is homomorphic to the case of one.
""")

# Legacy circular layout is for 1-4 items only.
change(layout,
       """                    / (MAX_NUM_ITEMS_IN_PREVIEW - MIN_NUM_ITEMS_IN_PREVIEW));""",
       """                    / (4 - MIN_NUM_ITEMS_IN_PREVIEW));""")
change(layout,
       "        } else if (numItems == MAX_NUM_ITEMS_IN_PREVIEW) {",
       "        } else if (numItems == 4) {")

# Use small 3-across previews without changing the size for 1-4.
change(layout,
       """        } else if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;""",
       """        } else if (numItems > 4) {
            scale = 0.18f; // Smaller icons with safe gaps and rounded-corner clearance.
        } else if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;""")

# Keep 3x3 icons strictly inside the actual themed folder background.
# The default clip path is deliberately oversized for Lawnchair's old overlap
# effect; use a tighter, shape-aware path only for 5-9 icon previews.
change("src/com/android/launcher3/folder/PreviewBackground.java",
       "    public Path getClipPath() {",
       """    public Path getInnerPreviewClipPath() {
        mPath.reset();
        final float inset = previewSize * 0.02f;
        getShape().addToPath(mPath, getOffsetX() + inset,
                getOffsetY() + inset, Math.max(0f, getScaledRadius() - inset));
        return mPath;
    }

    public Path getClipPath() {""")

change("src/com/android/launcher3/folder/PreviewItemManager.java",
       """        Path clipPath = bg.getClipPath();
        PointF firstPageOffset = new PointF(bg.basePreviewOffsetX, bg.basePreviewOffsetY);
        drawParams(canvas, mFirstPageParams, firstPageOffset, /* shouldClipPath */ false, clipPath);""",
       """        boolean isThreeByThreePreview = mFirstPageParams.size() > 4;
        Path clipPath = isThreeByThreePreview
                ? bg.getInnerPreviewClipPath() : bg.getClipPath();
        PointF firstPageOffset = new PointF(bg.basePreviewOffsetX, bg.basePreviewOffsetY);
        drawParams(canvas, mFirstPageParams, firstPageOffset,
                /* shouldClipPath */ isThreeByThreePreview, clipPath);""")

# Geometry sanity check: the far corners of the 3x3 icon squares lie within
# a circle of radius 0.45*previewSize, leaving room for a folder border.
import math
inset = 0.17
icon_width = 0.18
cell = (1 - 2 * inset) / 3
outer = inset + 0.5 * cell - 0.5 * icon_width
assert cell > icon_width, "3x3 icons overlap"
assert math.hypot(0.5 - outer, 0.5 - outer) < 0.45, "3x3 corner icons are too large"

change(organizer, "private static final int PREVIEW_MAX_ROWS = 2;",
       "private static final int PREVIEW_MAX_ROWS = 3;")
change(organizer, "private static final int PREVIEW_MAX_COLUMNS = 2;",
       "private static final int PREVIEW_MAX_COLUMNS = 3;")

# Match the successful Huy Launcher 1 privacy fix: no notification listener,
# accessibility service, or ACCESS_RESTRICTED_SETTINGS in the merged manifest.
change("AndroidManifest-common.xml",
       """        <service
            android:name="com.android.launcher3.notification.NotificationListener"
            android:label="@string/notification_dots_service_title"
            android:exported="true"
            android:permission="android.permission.BIND_NOTIFICATION_LISTENER_SERVICE">
            <intent-filter>
                <action android:name="android.service.notification.NotificationListenerService" />
            </intent-filter>
        </service>""", "")
change("lawnchair/AndroidManifest.xml",
       """        <service
            android:name="app.lawnchair.LawnchairAccessibilityService"
            android:exported="false"
            android:label="@string/derived_app_name"
            android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">
            <intent-filter>
                <action android:name="android.accessibilityservice.AccessibilityService" />
            </intent-filter>
            <meta-data
                android:name="android.accessibilityservice"
                android:resource="@xml/accessibility_service_config" />
        </service>""", "")
change("AndroidManifest-common.xml",
       '    <uses-permission android:name="android.permission.ACCESS_RESTRICTED_SETTINGS" />',
       "")

# Blur the home-screen icons and dock behind an open folder, without
# blurring the folder contents. Works with classic and expressive animations.
folder_source = "src/com/android/launcher3/folder/Folder.java"
change(folder_source,
       "import android.animation.AnimatorSet;",
       "import android.animation.AnimatorSet;\nimport android.animation.ValueAnimator;")
change(folder_source,
       "import android.graphics.Rect;",
       "import android.graphics.Rect;\nimport android.graphics.RenderEffect;\nimport android.graphics.Shader;")
change(folder_source,
       """        AnimatorSet animatorSet = getFolderAnimationManager()
                .createAnimatorSet(/* isOpening */ true);""",
       """        AnimatorSet animatorSet = getFolderAnimationManager()
                .createAnimatorSet(/* isOpening */ true);
        addHuyFolderBackgroundBlur(animatorSet, true);""")
change(folder_source,
       """        AnimatorSet animatorSet = getFolderAnimationManager()
                .createAnimatorSet(/* isOpening */ false);""",
       """        AnimatorSet animatorSet = getFolderAnimationManager()
                .createAnimatorSet(/* isOpening */ false);
        addHuyFolderBackgroundBlur(animatorSet, false);""")

# RenderEffect is supported on Android 12+. Leave stock dimming untouched on
# older Android. Reuse the launcher's blur targets instead of affecting folder UI.
change(folder_source,
       "    private void restoreLauncherAfterFolderDismissed() {",
       """    /**
     * Huy Launcher 2: background blur while a folder is open.
     * The folder stays sharp; the workspace and dock blur together.
     * closeComplete() already restores the targets after dismissal.
     */
    private void addHuyFolderBackgroundBlur(AnimatorSet folderAnimator, boolean isOpening) {
        if (!Utilities.ATLEAST_S || !(mActivityContext instanceof Launcher launcher)) {
            return;
        }
        if (launcher.getStateManager().getState().getDepth(launcher) != 0f) {
            return; // Do not interfere with depth blur during state transitions.
        }
        final float radiusPx = 14f * getResources().getDisplayMetrics().density;
        final ValueAnimator blur = ValueAnimator.ofFloat(
                isOpening ? 0f : radiusPx, isOpening ? radiusPx : 0f);
        blur.setDuration(isOpening ? 230 : 190);
        blur.addUpdateListener(animation -> {
            final float radius = (float) animation.getAnimatedValue();
            final RenderEffect effect = radius < 0.5f
                    ? null
                    : RenderEffect.createBlurEffect(radius, radius, Shader.TileMode.CLAMP);
            for (View target : launcher.getDepthBlurTargets()) {
                target.setRenderEffect(effect);
            }
        });
        folderAnimator.play(blur);
    }

    private void restoreLauncherAfterFolderDismissed() {""")

change("build.gradle", 'applicationId "app.lawnchair.play"',
       'applicationId "app.huy.androidlauncher2"')
# The first installed Launcher 2 is app.huy.androidlauncher2.debug and was signed
# with a disposable GitHub-runner debug key. We cannot upgrade it in place.
# Keep its data untouched during backup/migration by using app.huy.androidlauncher2
# (no debug suffix) for the permanently signed installation. Future APKs from
# the same signing key and package will update in place.
change("build.gradle", 'applicationIdSuffix ".debug"',
       'applicationIdSuffix ""')

# GitHub Actions run_number monotonically increases on each build. This helps
# Android recognize future releases as updates, not downgrades.
change("build.gradle", "versionCode 16_00_02_01_00",
       'versionCode (16_00_02_01_00 + (System.getenv("GITHUB_RUN_NUMBER") ?: "0").toInteger())')

change("build.gradle", 'resValue("string", "derived_app_name", "Lawnchair (Debug)")',
       'resValue("string", "derived_app_name", "Huy android launcher 2")')
change("build.gradle", 'resValue("string", "derived_app_name", "Lawnchair")',
       'resValue("string", "derived_app_name", "Huy android launcher 2")')

print("Ready to build: ./gradlew assembleLawnWithQuickstepPlayDebug")
print("Expected package: app.huy.androidlauncher2")
