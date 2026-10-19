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

# Use one fixed iOS-style 3x3 grid for EVERY folder size (1 through 9+).
# Small folders fill slots from the top-left, never inflate or center 1-4 icons.
change(layout,
       "        // The case of two items is homomorphic to the case of one.\n",
       """        if (index >= 0 && index < MAX_NUM_ITEMS_IN_PREVIEW) {
            final float inset = mAvailableSpace * 0.08f;
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

# Fixed preview size for any number of items, including 1/2/3/4.
change(layout,
       """        } else if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;""",
       """        } else {
            scale = 0.23f; // Same size for 1, 2, ... 9 or more items.
        }""")

# Keep ALL 3x3 mini-icons inside the folder border, even for 1-4 apps.
# The original Lawnchair clip path intentionally allows icons to overflow.
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
       """        boolean isThreeByThreePreview = !mFirstPageParams.isEmpty();
        Path clipPath = isThreeByThreePreview
                ? bg.getInnerPreviewClipPath() : bg.getClipPath();
        PointF firstPageOffset = new PointF(bg.basePreviewOffsetX, bg.basePreviewOffsetY);
        drawParams(canvas, mFirstPageParams, firstPageOffset,
                /* shouldClipPath */ isThreeByThreePreview, clipPath);""")

# iOS screenshot: icon 23%, outer margin 10.5%, inter-icon gap 5%.
# Enforce sizes so icons fit within the rounded folder.
import math
inset = 0.08
icon_width = 0.23
cell = (1 - 2 * inset) / 3
outer = inset + 0.5 * cell - 0.5 * icon_width
assert cell + 1e-6 >= icon_width, "3x3 icons overlap"
assert abs(outer - 0.105) < 0.005, "3x3 edge spacing differs from reference"
assert abs((cell - icon_width) - 0.05) < 0.005, "3x3 gap differs from reference"
assert math.hypot(0.5 - outer, 0.5 - outer) < 0.56, "3x3 corner icons are too large"

# Translucent glass background on CLOSED folder previews: a gentle
# two-stop highlight, consistent 1dp rim, and the original selected folder
# shape. Icons and clipping remain unchanged.
change("src/com/android/launcher3/folder/PreviewBackground.java",
       "import android.graphics.Matrix;",
       "import android.graphics.Matrix;\nimport android.graphics.LinearGradient;")
change("src/com/android/launcher3/folder/PreviewBackground.java",
       """        mPaint.setColor(getBgColor());

        getShape().drawShape(canvas, getOffsetX(), getOffsetY(), getScaledRadius(), mPaint);
        drawShadow(canvas);""",
       """        final float top = getOffsetY();
        final float bottom = top + getScaledRadius() * 2f;
        mPaint.setColor(Color.WHITE);
        mPaint.setShader(new LinearGradient(0f, top, 0f, bottom,
                Color.argb(205, 255, 255, 255),
                Color.argb(125, 232, 241, 251), Shader.TileMode.CLAMP));
        getShape().drawShape(canvas, getOffsetX(), getOffsetY(), getScaledRadius(), mPaint);
        mPaint.setShader(null);
        mPaint.setStyle(Paint.Style.STROKE);
        mPaint.setStrokeWidth(Math.max(1f, mStrokeWidth));
        mPaint.setColor(Color.argb(190, 255, 255, 255));
        getShape().drawShape(canvas, getOffsetX() + mStrokeWidth,
                getOffsetY() + mStrokeWidth,
                getScaledRadius() - mStrokeWidth, mPaint);
        mPaint.setStyle(Paint.Style.FILL);
        drawShadow(canvas);""")

# The OPEN folder uses a semi-transparent glass panel instead of opaque cream.
# Both animation implementations must preserve the translucent end color.
folderGlassColor = "Color.argb(206, 247, 250, 255)"
change("src/com/android/launcher3/folder/Folder.java",
       """        mBackground.setColor(LawnchairUtilsKt.resolveFolderBackgroundColor(getContext()));
        var alpha = LawnchairUtilsKt.getFolderBackgroundAlpha(getContext());
        mBackground.setAlpha(alpha);""",
       """        mBackground.setColor(Color.argb(206, 247, 250, 255));
        mBackground.setAlpha(255);
        mBackground.setStroke(Math.max(1,
                Math.round(getResources().getDisplayMetrics().density)),
                Color.argb(180, 255, 255, 255));""")
change("src/com/android/launcher3/folder/FolderAnimationManager.java",
       "int finalColor = LawnchairUtilsKt.resolveFolderBackgroundColor(mContext);",
       "int finalColor = android.graphics.Color.argb(206, 247, 250, 255);")
change("src/com/android/launcher3/folder/FolderSpringAnimatorSet.kt",
       "val finalColor = app.lawnchair.util.resolveFolderBackgroundColor(context)",
       "val finalColor = Color.argb(206, 247, 250, 255)")

# Lawnchair's helper initially calculates 2x2 grid spacing from items 0
# and 3. For our 3x3 position logic, items 0 and 4 are diagonal neighbours.
# This also fixes the destination of icons entering/leaving a small folder.
change(layout,
       "        getPosition(3, 4, result);",
       "        getPosition(4, 4, result);")

# Apply exactly the same 3x3 size even when page > 0; drag animations
# don't cause tiny folders to temporarily switch to larger 2x2 icons.
change(layout,
       """        if (page > 0) {
            scale = MIN_SCALE;
        } else if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;
        }
        return scale * mBaselineIconScale;""",
       """        scale = 0.23f;
        return scale * mBaselineIconScale;""")

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

# Huy Launcher 2: soft glass capsule BEHIND dock icons, without moving,
# reordering, or changing existing dock icons or folders. Frosted look uses a
# translucent light/dark gradient, fine light border and subtle elevation.
# Avoid blurring individual widgets (which caused the patchy blur screenshot).
change("src/com/android/launcher3/Hotseat.java",
       "import android.graphics.Color;",
       "import android.graphics.Color;\nimport android.content.res.Configuration;")
change("src/com/android/launcher3/Hotseat.java",
       """    private void setUpBackground() {
        if(!preferenceManager.getHotseatBG().get()) return;""",
       """    private void setUpBackground() {
        // Glass dock is enabled by default in Huy Launcher 2. Only the
        // icon grid's background is changed; layout, drop targets and
        // touch handling stay exactly as in stock Lawnchair.
        final float density = getResources().getDisplayMetrics().density;
        final boolean night = (getResources().getConfiguration().uiMode
                & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        final int[] gradient = night
                ? new int[]{Color.argb(105, 245, 247, 255),
                            Color.argb(65, 210, 222, 240)}
                : new int[]{Color.argb(145, 255, 255, 255),
                            Color.argb(83, 245, 250, 255)};
        GradientDrawable glass = new GradientDrawable(
                GradientDrawable.Orientation.TOP_BOTTOM, gradient);
        glass.setCornerRadius(32f * density);
        glass.setStroke(Math.max(1, Math.round(density)),
                Color.argb(night ? 125 : 170, 255, 255, 255));
        // Stretch the pill to fit the widest supported dock grid. In particular,
        // a 6-icon dock must not spill out of the background at either end.
        // Negative insets expand only the drawable (not the icon hit boxes).
        final int slots = mActivity.getDeviceProfile().numShownHotseatIcons;
        final int horizontalGlassInset = Math.round(
                (slots >= 6 ? -12f : slots >= 5 ? -7f : -2f) * density);
        mIconsContainer.setBackground(new InsetDrawable(glass,
                horizontalGlassInset, Math.round(1f * density),
                horizontalGlassInset, Math.round(1f * density)));
        mIconsContainer.setElevation(2f * density);
        // This new glass preset takes precedence over the legacy solid dock
        // background so there is no opaque box hiding the translucent effect.
        setBackground(null);
    }

    private void setUpOldBackground() {
        if(!preferenceManager.getHotseatBG().get()) return;""")
# Explicitly handle orientation change; portrait dock stays glass, vertical
# docks retain the existing container without extra overlays.

# One uniform folder backdrop. This removes FLAG_BLUR_BEHIND: that API blurred
# only patches on Pixel 5 (sharp wallpaper + extremely blurred widgets).
# Instead ask Lawnchair's own DepthController to blur the wallpaper surface,
# blur the workspace/dock modestly, and use one even translucent overlay.
# No wallpaper-reading permissions are needed (Android 14 forbids reading it).
change("src/com/android/launcher3/Launcher.java",
       "    /** @return list of View targets to be blurred based on changes to depth. */",
       """    /** Blur the wallpaper below an open folder, if supported by this launcher. */
    public boolean setHuyFolderWallpaperBlur(float fraction) {
        return false;
    }

    /** @return list of View targets to be blurred based on changes to depth. */""")

change("quickstep/src/com/android/launcher3/uioverrides/QuickstepLauncher.java",
       "    public DepthController getDepthController() {",
       """    @Override
    public boolean setHuyFolderWallpaperBlur(float fraction) {
        return mDepthController != null
                && mDepthController.setHuyFolderDepth(fraction);
    }

    public DepthController getDepthController() {""")

# The public widgetDepth multiproperty is used for workspace/recents transitions.
# Reuse that existing wallpaper-surface blur path for folders rather than relying
# on FLAG_BLUR_BEHIND or trying to read protected wallpaper pixels.
change("quickstep/src/com/android/launcher3/statehandlers/DepthController.java",
       "    private void onLauncherDraw() {",
       """    /**
     * Apply folder wallpaper blur through the existing SurfaceControl depth pipeline.
     * May return false if Android's cross-window blur setting is disabled.
     */
    public boolean setHuyFolderDepth(float fraction) {
        if (!Utilities.ATLEAST_S) {
            return false;
        }
        try {
            ensureDependencies();
            mCrossWindowBlursEnabled =
                    CrossWindowBlurListeners.getInstance().isCrossWindowBlurEnabled();
            widgetDepth.setValue(Math.max(0f, Math.min(0.32f, fraction)));
            // The user may have disabled Lawnchair's normal depth preference;
            // folder blurring is a separate opt-in feature, so apply directly.
            super.applyDepthAndBlur();
            // mCurrentBlur alone does not prove wallpaper blur is drawn.
            // On some devices the SurfaceControl is absent/invalid, leaving
            // the wallpaper sharp while only widgets are blurred.
            return fraction <= 0f || (mCurrentBlur > 0
                    && mBaseSurface != null && mBaseSurface.isValid());
        } catch (Throwable t) {
            return false;
        }
    }

    private void onLauncherDraw() {""")

folder_source = "src/com/android/launcher3/folder/Folder.java"
change(folder_source,
       "import android.animation.AnimatorSet;",
       "import android.animation.AnimatorSet;\nimport android.animation.ValueAnimator;")
change(folder_source,
       "import android.graphics.Rect;",
       "import android.graphics.Rect;\nimport android.graphics.RenderEffect;\nimport android.graphics.Shader;")
change(folder_source,
       "import android.view.View;",
       "import android.view.View;\nimport android.graphics.Color;")

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

change(folder_source,
       "    private void restoreLauncherAfterFolderDismissed() {",
       """    private View mHuyUniformFolderOverlay;

    /** One even overlay over wallpaper, widgets, dock and icons; below folder. */
    private void ensureHuyFolderOverlay(Launcher launcher) {
        final BaseDragLayer dragLayer = mActivityContext.getDragLayer();
        if (mHuyUniformFolderOverlay == null) {
            mHuyUniformFolderOverlay = new View(getContext());
            mHuyUniformFolderOverlay.setBackgroundColor(Color.rgb(91, 108, 122));
            mHuyUniformFolderOverlay.setAlpha(0f);
            mHuyUniformFolderOverlay.setClickable(false);
            mHuyUniformFolderOverlay.setImportantForAccessibility(
                    View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        }
        if (mHuyUniformFolderOverlay.getParent() == null && getParent() == dragLayer) {
            dragLayer.addView(mHuyUniformFolderOverlay,
                    dragLayer.indexOfChild(this),
                    new BaseDragLayer.LayoutParams(
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT,
                            android.view.ViewGroup.LayoutParams.MATCH_PARENT));
            // The open folder stays sharp above the full-screen overlay.
            dragLayer.bringChildToFront(this);
        }
    }

    /**
     * Uniform backdrop: wallpaper blurred via Lawnchair's native
     * DepthController (when Android supports it), workspace/dock blurred with
     * RenderEffect, and the SAME gentle dark overlay over the entire screen.
     * The opened folder is drawn above the overlay and stays sharp.
     */
    private void addHuyFolderBackgroundBlur(AnimatorSet folderAnimator, boolean isOpening) {
        if (!Utilities.ATLEAST_S || !(mActivityContext instanceof Launcher launcher)) {
            return;
        }
        // Always draw the uniform backdrop, even when wallpaper-depth blur
        // cannot be enabled or the launcher is mid-transition.
        ensureHuyFolderOverlay(launcher);
        final float maxRadius = 8f * getResources().getDisplayMetrics().density;
        final ValueAnimator blur = ValueAnimator.ofFloat(
                isOpening ? 0f : 1f, isOpening ? 1f : 0f);
        blur.setDuration(isOpening ? 220 : 180);
        blur.addUpdateListener(animation -> {
            final float progress = (float) animation.getAnimatedValue();
            // Blur wallpaper underneath the window, not just individual widgets.
            // Native wallpaper blur may be disabled by Android, power saving,
            // or the wallpaper compositor. Never blur just widgets heavily
            // when the wallpaper remains clear.
            final boolean wallpaperBlurActive =
                    launcher.setHuyFolderWallpaperBlur(0.32f * progress);
            final float radius = wallpaperBlurActive ? maxRadius * progress : 0f;
            final RenderEffect effect = radius < 0.5f ? null
                    : RenderEffect.createBlurEffect(
                            radius, radius, Shader.TileMode.CLAMP);
            for (View target : launcher.getDepthBlurTargets()) {
                target.setRenderEffect(effect);
            }
            if (mHuyUniformFolderOverlay != null) {
                mHuyUniformFolderOverlay.setAlpha((wallpaperBlurActive ? 0.22f : 0.56f) * progress);
            }
        });
        folderAnimator.play(blur);
    }

    private void restoreLauncherAfterFolderDismissed() {""")

# Restore after closing a folder without animation, including app launches.
# Never leave wallpaper depth or a dark overlay stuck on the home screen.
change(folder_source,
       """        if (scrim != null) {
            scrim.setAlpha(1f);""",
       """        launcher.setHuyFolderWallpaperBlur(0f);
        if (mHuyUniformFolderOverlay != null) {
            mHuyUniformFolderOverlay.setAlpha(0f);
            if (mHuyUniformFolderOverlay.getParent() instanceof
                    android.view.ViewGroup group) {
                group.removeView(mHuyUniformFolderOverlay);
            }
        }
        if (scrim != null) {
            scrim.setAlpha(1f);""")

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
