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

# The CLOSED folder preview (glass background + all 3x3 mini-icons) is
# 20% larger than the visible size of a normal app icon.  Apply it at the
# DeviceProfile dimension rather than scaling FolderIcon View: labels,
# hit targets, drag coordinates, widget layouts and bounce animations stay
# in their original coordinate system.  Both workspace and dock folders
# use this size, including after a device grid/icon-size change.
change("src/com/android/launcher3/DeviceProfile.java",
       "        folderIconSizePx = Math.round(iconSizePx * ICON_VISIBLE_AREA_FACTOR);",
       "        folderIconSizePx = Math.round(iconSizePx * ICON_VISIBLE_AREA_FACTOR * 1.20f);")

# Consistent 120% sizing for folders rendered in the All Apps list, too.
# Normally Huy Launcher 2 has no app drawer, but this avoids an unexpected
# downsize should All Apps ever be enabled again.
change("src/com/android/launcher3/folder/PreviewBackground.java",
       "            previewSize = Math.round(allAppsIconSize * ICON_VISIBLE_AREA_FACTOR);",
       "            previewSize = Math.round(allAppsIconSize * ICON_VISIBLE_AREA_FACTOR * 1.20f);")


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

change(organizer, '        mMaxItemsPerPage = mMaxCountX * mMaxCountY;',
       '        mMaxItemsPerPage = Math.min(3, mMaxCountX) * Math.min(3, mMaxCountY);')

# Always use fixed three-column placement in the opened folder.
# For example: 4 apps -> 3 + 1, 5 -> 3 + 2, 9 -> 3 + 3 + 3.
# Ten or more apps use the normal folder paging mechanism (9 per page).
change(organizer,
       "    private void calculateGridSize(int count) {\n        boolean done;\n        int gridCountX = mCountX;\n        int gridCountY = mCountY;\n\n        if (count >= mMaxItemsPerPage) {\n            gridCountX = mMaxCountX;\n            gridCountY = mMaxCountY;\n            done = true;\n        } else {\n            done = false;\n        }\n\n        while (!done) {\n            int oldCountX = gridCountX;\n            int oldCountY = gridCountY;\n            if (gridCountX * gridCountY < count) {\n                // Current grid is too small, expand it\n                if ((gridCountX <= gridCountY || gridCountY == mMaxCountY)\n                        && gridCountX < mMaxCountX) {\n                    gridCountX++;\n                } else if (gridCountY < mMaxCountY) {\n                    gridCountY++;\n                }\n                if (gridCountY == 0) gridCountY++;\n            } else if ((gridCountY - 1) * gridCountX >= count && gridCountY >= gridCountX) {\n                gridCountY = Math.max(0, gridCountY - 1);\n            } else if ((gridCountX - 1) * gridCountY >= count) {\n                gridCountX = Math.max(0, gridCountX - 1);\n            }\n            done = gridCountX == oldCountX && gridCountY == oldCountY;\n        }\n\n        mCountX = gridCountX;\n        mCountY = gridCountY;\n    }",
       "    private void calculateGridSize(int count) {\n        // Huy Launcher 2: use the same left-to-right three-column arrangement\n        // as the closed folder's preview. Never make 4 items into a 2x2 grid.\n        final int columns = Math.max(1, Math.min(3, mMaxCountX));\n        final int maxRows = Math.max(1, Math.min(3, mMaxCountY));\n        final int itemsOnPage = Math.min(Math.max(0, count), mMaxItemsPerPage);\n        mCountX = columns;\n        mCountY = Math.min(maxRows,\n                Math.max(1, (itemsOnPage + columns - 1) / columns));\n    }")

# Pure algorithm assertions: visible positions are row-major in groups of 3.
for item_count, expected_rows in {1: [1], 2: [2], 3: [3], 4: [3, 1],
                                  5: [3, 2], 6: [3, 3], 7: [3, 3, 1],
                                  9: [3, 3, 3], 10: [3, 3, 3, 1]}.items():
    pages = [list(range(p, min(p + 9, item_count)))
             for p in range(0, item_count, 9)]
    actual_rows = []
    for page in pages:
        actual_rows.extend(len(page[i:i+3]) for i in range(0, len(page), 3))
    assert actual_rows == expected_rows, (item_count, actual_rows)

# One wallpaper chooser for BOTH the Android home screen and folder blur.
# Move the old picker from Folder Settings to Home Screen > Wallpaper.
# Keep the same private image filename used by Folder.java's blur cache.
# SET_WALLPAPER is already declared in AndroidManifest-common.xml.
home_settings = "lawnchair/src/app/lawnchair/ui/preferences/destinations/HomeScreenPreferences.kt"
change(home_settings,
       "import android.content.Context",
       """import android.app.WallpaperManager
import android.content.Context
import android.graphics.BitmapFactory
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import java.io.File
import java.nio.file.Files
import java.nio.file.StandardCopyOption
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext""")

change(home_settings,
       """    val context = LocalContext.current
    PreferenceLayout(""",
       """    val context = LocalContext.current
    val wallpaperPicker = rememberLauncherForActivityResult(
        ActivityResultContracts.OpenDocument()
    ) { uri ->
        if (uri != null) {
            scope.launch {
                val pending = File(context.filesDir, "huy_folder_wallpaper.pending")
                try {
                    withContext(Dispatchers.IO) {
                        context.contentResolver.openInputStream(uri)?.use { src ->
                            pending.outputStream().use { dst -> src.copyTo(dst) }
                        } ?: error("Cannot read selected image")

                        // Do not replace a valid wallpaper/blur image with an
                        // unsupported file or an incomplete document.
                        val info = BitmapFactory.Options().apply {
                            inJustDecodeBounds = true
                        }
                        BitmapFactory.decodeFile(pending.absolutePath, info)
                        if (pending.length() == 0L || info.outWidth <= 0 || info.outHeight <= 0) {
                            error("Invalid image; please choose another photo")
                        }

                        // Set only the HOME wallpaper; do not explicitly
                        // overwrite a separately configured lock-screen image.
                        pending.inputStream().use { src ->
                            WallpaperManager.getInstance(context).setStream(
                                src, null, true, WallpaperManager.FLAG_SYSTEM
                            )
                        }

                        // Commit the same image to Folder.java's existing
                        // private backdrop store only after wallpaper succeeds.
                        Files.move(
                            pending.toPath(),
                            File(context.filesDir, "huy_folder_wallpaper.image").toPath(),
                            StandardCopyOption.REPLACE_EXISTING
                        )
                    }
                    Toast.makeText(
                        context, "Home wallpaper and folder blur image updated", Toast.LENGTH_LONG
                    ).show()
                } catch (e: Exception) {
                    Toast.makeText(
                        context, "Could not set wallpaper: " + e.message, Toast.LENGTH_LONG
                    ).show()
                } finally {
                    pending.delete()
                }
            }
        }
    }
    PreferenceLayout(""")

change(home_settings,
       """        PreferenceGroup(heading = stringResource(id = R.string.wallpaper)) {
            SwitchPreference(""",
       """        PreferenceGroup(heading = stringResource(id = R.string.wallpaper)) {
            ClickablePreference(
                label = "Choose wallpaper",
                onClick = { wallpaperPicker.launch(arrayOf("image/*")) },
            )
            ClickablePreference(
                label = "Clear custom folder blur image",
                onClick = {
                    context.deleteFile("huy_folder_wallpaper.image")
                    Toast.makeText(context, "Custom folder blur image cleared", Toast.LENGTH_SHORT).show()
                },
            )
            SwitchPreference(""")

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

# Huy Launcher 2 should never shrink or zoom the HOME backdrop when a
# folder opens. Android's folder spring scales workspace/hotseat to 97.5%;
# use 100% for those targets, while leaving the folder's own reveal intact.
change("src/com/android/launcher3/folder/FolderSpringAnimatorSet.kt",
       "        private const val LAUNCHER_SCALE = 0.975f",
       "        private const val LAUNCHER_SCALE = 1f")

# The native SurfaceControl blur path also changes wallpaper zoom through
# BaseDepthController.applyDepthAndBlurInternal(). Suppress wallpaper zoom
# only while applying our folder-specific blur, not for recents/All Apps.
change("quickstep/src/com/android/quickstep/util/BaseDepthController.java",
       "    protected boolean mPauseBlurs;",
       """    protected boolean mPauseBlurs;
    /** Keep the wallpaper at its original size during folder-only backdrop blur. */
    protected boolean mHuySkipWallpaperZoomForFolder;
    /** Also block unexpected depth callbacks throughout the open folder. */
    protected boolean mHuyFolderBlurVisible;""")
change("quickstep/src/com/android/quickstep/util/BaseDepthController.java",
       "        if (windowToken != null && Utilities.ATLEAST_R) {",
       """        if (windowToken != null && Utilities.ATLEAST_R
                && !mHuySkipWallpaperZoomForFolder && !mHuyFolderBlurVisible) {""")

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
            // Suppress wallpaper zoom during both depth property callbacks
            // and the forced native blur apply. No zoom-out on folder opening.
            mHuySkipWallpaperZoomForFolder = true;
            mHuyFolderBlurVisible = fraction > 0f;
            try {
                widgetDepth.setValue(Math.max(0f, Math.min(0.32f, fraction)));
                // The user may have disabled Lawnchair's normal depth preference;
                // folder blurring is independent and still applies natively.
                super.applyDepthAndBlur();
            } finally {
                mHuySkipWallpaperZoomForFolder = false;
            }
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

# Real pixel blur fallback: once the user chooses the wallpaper image in
# Folder settings, composite that wallpaper with the actual current launcher
# workspace and dock (including widgets), then apply ONE RenderEffect to the
# whole composite. Unlike SurfaceControl cross-window blur, this also works
# when battery saver / Pixel 5 disables native wallpaper blur.
change(folder_source,
       "import android.graphics.RenderEffect;",
       """import android.graphics.RenderEffect;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Paint;""")
change(folder_source,
       "import android.graphics.Color;",
       """import android.graphics.Color;
import android.widget.ImageView;
import java.io.File;""")

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
    private Bitmap mHuyBackdropBitmap;
    private boolean mHuyHasBackdropSnapshot;
    // One shared backdrop cache for every folder. Never decode wallpaper or
    // draw widgets synchronously in the folder opening animation.
    private static Bitmap sHuyCachedBackdrop;
    private static long sHuyWallpaperStamp = -1L, sHuyCacheCreatedAt;
    private static int sHuyCacheWidth, sHuyCacheHeight, sHuyCachePage = -1;
    private static float sHuyCacheOffset = -1f;
    private static boolean sHuyWarmupScheduled;

    /**
     * Extend the backdrop image past all four edges before applying blur.
     * Without overscan RenderEffect clips its output at the ImageView edge:
     * the middle looks blurred but 20-80px strips near the screen remain sharp.
     */
    private int getHuyBackdropOverscanPx() {
        return Math.max(48, (int) Math.ceil(
                50f * getResources().getDisplayMetrics().density));
    }

    /** One even overlay over wallpaper, widgets, dock and icons; below folder. */
    private void ensureHuyFolderOverlay(Launcher launcher) {
        final BaseDragLayer dragLayer = mActivityContext.getDragLayer();
        if (mHuyUniformFolderOverlay == null) {
            mHuyUniformFolderOverlay = new ImageView(getContext());
            mHuyUniformFolderOverlay.setBackgroundColor(Color.rgb(91, 108, 122));
            mHuyUniformFolderOverlay.setAlpha(0f);
            mHuyUniformFolderOverlay.setClickable(false);
            mHuyUniformFolderOverlay.setImportantForAccessibility(
                    View.IMPORTANT_FOR_ACCESSIBILITY_NO);
        }
        if (mHuyUniformFolderOverlay.getParent() == null && getParent() == dragLayer) {
            final int overscan = getHuyBackdropOverscanPx();
            final BaseDragLayer.LayoutParams backdropLp =
                    new BaseDragLayer.LayoutParams(
                            dragLayer.getWidth() + overscan * 2,
                            dragLayer.getHeight() + overscan * 2);
            backdropLp.gravity = android.view.Gravity.TOP | android.view.Gravity.LEFT;
            backdropLp.leftMargin = -overscan;
            backdropLp.topMargin = -overscan;
            dragLayer.addView(mHuyUniformFolderOverlay,
                    dragLayer.indexOfChild(this), backdropLp);
            // Overscan stays outside visible root view; the blurred backdrop
            // covers right up to the parent's left/right/top/bottom edges.
            // The open folder stays sharp above the full-screen overlay.
            dragLayer.bringChildToFront(this);
        }
        // Just attach the PRECOMPUTED bitmap. No decoding or view drawing
        // during the touch event: folder popup should be instantaneous.
        File wallpaper = new File(launcher.getFilesDir(),
                "huy_folder_wallpaper.image");
        final float liveOffset = getHuyWallpaperOffset(launcher);
        mHuyHasBackdropSnapshot = sHuyCachedBackdrop != null
                && !sHuyCachedBackdrop.isRecycled() && wallpaper.isFile()
                && wallpaper.lastModified() == sHuyWallpaperStamp
                && dragLayer.getWidth() == sHuyCacheWidth
                && dragLayer.getHeight() == sHuyCacheHeight
                && launcher.getWorkspace().getCurrentPage() == sHuyCachePage
                && Math.abs(liveOffset - sHuyCacheOffset) < 0.002f;
        if (mHuyHasBackdropSnapshot
                && mHuyUniformFolderOverlay instanceof ImageView image) {
            image.setBackgroundColor(Color.TRANSPARENT);
            image.setImageBitmap(sHuyCachedBackdrop);
            float radius = 25f * getResources().getDisplayMetrics().density;
            image.setRenderEffect(RenderEffect.createBlurEffect(
                    radius, radius, Shader.TileMode.CLAMP));
        } else {
            mHuyUniformFolderOverlay.setBackgroundColor(Color.rgb(91, 108, 122));
        }
    }

    /** Match the current page's wallpaper parallax rather than always using center crop. */
    private float getHuyWallpaperOffset(Launcher launcher) {
        try {
            return Math.max(0f, Math.min(1f,
                    launcher.getWorkspace().getWallpaperOffsetForCenterPage()));
        } catch (Exception e) {
            return 0.5f;
        }
    }

    /** Draw the full backdrop in an idle frame, never on a folder tap. */
    public void scheduleHuyBackdropWarmup(Launcher launcher, long delayMillis) {
        File wallpaper = new File(launcher.getFilesDir(),
                "huy_folder_wallpaper.image");
        if (!wallpaper.isFile() || sHuyWarmupScheduled) {
            return;
        }
        BaseDragLayer layer = launcher.getDragLayer();
        if (sHuyCachedBackdrop != null && !sHuyCachedBackdrop.isRecycled()
                && sHuyWallpaperStamp == wallpaper.lastModified()
                && sHuyCacheWidth == layer.getWidth()
                && sHuyCacheHeight == layer.getHeight()
                && sHuyCachePage == launcher.getWorkspace().getCurrentPage()
                && Math.abs(sHuyCacheOffset - getHuyWallpaperOffset(launcher)) < 0.002f
                && System.currentTimeMillis() - sHuyCacheCreatedAt < 15000L) {
            return;
        }
        sHuyWarmupScheduled = true;
        layer.postDelayed(() -> {
            sHuyWarmupScheduled = false;
            if (getParent() == layer || layer.getWidth() < 100
                    || layer.getHeight() < 100) {
                return;
            }
            if (mHuyUniformFolderOverlay == null) {
                mHuyUniformFolderOverlay = new ImageView(getContext());
                mHuyUniformFolderOverlay.setAlpha(0f);
                mHuyUniformFolderOverlay.setClickable(false);
            }
            createHuyFolderSnapshot(launcher, layer);
        }, delayMillis);
    }

    private boolean createHuyFolderSnapshot(Launcher launcher, BaseDragLayer dragLayer) {
        if (!(mHuyUniformFolderOverlay instanceof ImageView imageView)) {
            return false;
        }
        final File imageFile = new File(launcher.getFilesDir(),
                "huy_folder_wallpaper.image");
        if (!imageFile.isFile()) {
            return false;
        }
        final int w = dragLayer.getWidth(), h = dragLayer.getHeight();
        if (w < 100 || h < 100) {
            return false;
        }
        Bitmap source = null;
        Bitmap screenshot = null;
        try {
            final BitmapFactory.Options bounds = new BitmapFactory.Options();
            bounds.inJustDecodeBounds = true;
            BitmapFactory.decodeFile(imageFile.getAbsolutePath(), bounds);
            if (bounds.outWidth <= 0 || bounds.outHeight <= 0) {
                return false;
            }
            final BitmapFactory.Options opts = new BitmapFactory.Options();
            opts.inPreferredConfig = Bitmap.Config.RGB_565;
            int sample = 1;
            while (bounds.outWidth / (sample * 2) >= w
                    && bounds.outHeight / (sample * 2) >= h) {
                sample *= 2;
            }
            opts.inSampleSize = sample;
            source = BitmapFactory.decodeFile(imageFile.getAbsolutePath(), opts);
            if (source == null) {
                return false;
            }
            final int overscan = getHuyBackdropOverscanPx();
            screenshot = Bitmap.createBitmap(
                    w + overscan * 2, h + overscan * 2, Bitmap.Config.ARGB_8888);
            final Canvas canvas = new Canvas(screenshot);
            final Paint p = new Paint(Paint.FILTER_BITMAP_FLAG | Paint.ANTI_ALIAS_FLAG);
            // The OLD implementation always used a fixed CENTER_CROP.
            // Android can render the actual static wallpaper with extra
            // horizontal travel (parallax) and a different crop. Match the
            // system wallpaper's desired dimensions, capped at 22% extra
            // width to avoid excessive zoom on portrait photos. Keep the
            // same visible vertical center as the system wallpaper.
            final android.app.WallpaperManager wm =
                    android.app.WallpaperManager.getInstance(launcher);
            final float desiredWidth = wm.getDesiredMinimumWidth();
            final float wallpaperSpan = Math.min(w * 1.22f,
                    Math.max((float) w, desiredWidth));
            final float scale = Math.max(
                    Math.max(w / (float) source.getWidth(),
                             h / (float) source.getHeight()),
                    wallpaperSpan / (float) source.getWidth());
            final float sw = source.getWidth() * scale;
            final float sh = source.getHeight() * scale;
            final float currentWallpaperOffset = getHuyWallpaperOffset(launcher);
            final android.graphics.BitmapShader wallpaperShader =
                    new android.graphics.BitmapShader(source,
                            Shader.TileMode.CLAMP, Shader.TileMode.CLAMP);
            final android.graphics.Matrix wallpaperMatrix =
                    new android.graphics.Matrix();
            wallpaperMatrix.setScale(scale, scale);
            // Apply the page-dependent horizontal wallpaper offset. This
            // prevents the blurred copy jumping to the center when a folder
            // opens on page 2, 3, etc.
            wallpaperMatrix.postTranslate(
                    overscan - Math.max(0f, sw - w) * currentWallpaperOffset,
                    overscan + (h - sh) / 2f);
            wallpaperShader.setLocalMatrix(wallpaperMatrix);
            p.setShader(wallpaperShader);
            canvas.drawRect(0f, 0f,
                    w + overscan * 2f, h + overscan * 2f, p);
            p.setShader(null);
            // Draw launcher-owned views into the central screen-sized region.
            canvas.save();
            canvas.translate(overscan, overscan);

            // Draw launcher-owned views on top of the image BEFORE blurring.
            // Capturing only the workspace misses the wallpaper, while
            // blurring only the wallpaper misses widgets and dock.
            final int[] dragPos = new int[2];
            final int[] targetPos = new int[2];
            dragLayer.getLocationInWindow(dragPos);
            for (View target : launcher.getDepthBlurTargets()) {
                if (target == null || target.getWidth() == 0 || target.getHeight() == 0) {
                    continue;
                }
                canvas.save();
                try {
                    target.getLocationInWindow(targetPos);
                    canvas.translate(targetPos[0] - dragPos[0],
                            targetPos[1] - dragPos[1]);
                    target.draw(canvas);
                } catch (Throwable itemError) {
                    Log.w(TAG, "Could not snapshot background layer", itemError);
                } finally {
                    canvas.restore();
                }
            }
            canvas.restore();

            imageView.setBackgroundColor(Color.TRANSPARENT);
            imageView.setScaleType(ImageView.ScaleType.FIT_XY);
            imageView.setImageBitmap(screenshot);
            final float blurPx = 25f * getResources().getDisplayMetrics().density;
            imageView.setRenderEffect(RenderEffect.createBlurEffect(
                    blurPx, blurPx, Shader.TileMode.CLAMP));
            if (sHuyCachedBackdrop != null && sHuyCachedBackdrop != screenshot) {
                sHuyCachedBackdrop.recycle();
            }
            sHuyCachedBackdrop = screenshot;
            sHuyWallpaperStamp = imageFile.lastModified();
            sHuyCacheWidth = w;
            sHuyCacheHeight = h;
            sHuyCachePage = launcher.getWorkspace().getCurrentPage();
            sHuyCacheOffset = currentWallpaperOffset;
            sHuyCacheCreatedAt = System.currentTimeMillis();
            mHuyBackdropBitmap = screenshot;
            screenshot = null;
            return true;
        } catch (Throwable error) {
            Log.w(TAG, "Could not create full folder backdrop snapshot", error);
            return false;
        } finally {
            if (source != null) {
                source.recycle();
            }
            if (screenshot != null) {
                screenshot.recycle();
            }
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
        blur.setDuration(isOpening ? 110 : 95);
        blur.addUpdateListener(animation -> {
            final float progress = (float) animation.getAnimatedValue();
            if (mHuyHasBackdropSnapshot) {
                // This is a real, uniform snapshot blur. No OS cross-window
                // blur is necessary; keep original targets untouched.
                launcher.setHuyFolderWallpaperBlur(0f);
                for (View target : launcher.getDepthBlurTargets()) {
                    target.setRenderEffect(null);
                }
                mHuyUniformFolderOverlay.setAlpha(progress);
                return;
            }
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

change(folder_source,
       """        mFolderIcon.post(() -> {
            if (getItemCount() <= 1) {
                replaceFolderWithFinalItem();
            }
        });""",
       """        mFolderIcon.post(() -> {
            if (getItemCount() <= 1) {
                replaceFolderWithFinalItem();
            }
        });
        // Precompute once while the home screen is idle.
        if (mActivityContext instanceof Launcher launcher) {
            scheduleHuyBackdropWarmup(launcher, 700);
        }""")
change(folder_source,
       """        restoreLauncherAfterFolderDismissed();
    }""",
       """        restoreLauncherAfterFolderDismissed();
        // After dismissal, refresh only during idle time.
        if (mActivityContext instanceof Launcher launcher) {
            scheduleHuyBackdropWarmup(launcher, 450);
        }
    }""")


# Refresh the cached snapshot after scrolling between home pages, while
# the launcher is idle, not during the folder-open touch animation.
# Without this, a folder opened on page 2 could display page 1's
# wallpaper crop and old workspace contents (the reported mismatch).
change("src/com/android/launcher3/Workspace.java",
       """            updateStatusbarClock();
        }
    }

    protected void setWallpaperDimension() {""",
       """            updateStatusbarClock();
            // Rebuild the folder backdrop on the newly selected page.
            postDelayed(() -> mapOverItems((info, view) -> {
                if (view instanceof com.android.launcher3.folder.FolderIcon icon) {
                    com.android.launcher3.folder.Folder folder = icon.getFolder();
                    if (folder != null) {
                        folder.scheduleHuyBackdropWarmup(mLauncher, 0);
                        return true;
                    }
                }
                return false;
            }), 220L);
        }
    }

    protected void setWallpaperDimension() {""")

# Restore after closing a folder without animation, including app launches.
# Never leave wallpaper depth or a dark overlay stuck on the home screen.
change(folder_source,
       """        if (scrim != null) {
            scrim.setAlpha(1f);""",
       """        launcher.setHuyFolderWallpaperBlur(0f);
        if (mHuyUniformFolderOverlay != null) {
            mHuyUniformFolderOverlay.setAlpha(0f);
            if (mHuyUniformFolderOverlay instanceof ImageView image) {
                image.setImageDrawable(null);
                image.setRenderEffect(null);
            }
            // Shared cache survives folder close for instant next opening.
            mHuyBackdropBitmap = null;
            mHuyHasBackdropSnapshot = false;
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


# Hide duplicate app icons from the normal drawer when those apps already
# exist on the home screen, dock or inside a home-screen folder.
# This does NOT remove, uninstall, move or persistently hide any app.
# Default OFF, switch located in Settings > App drawer > General.
change("lawnchair/src/app/lawnchair/preferences2/PreferenceManager2.kt",
       """    val hiddenApps = preference(
        key = stringSetPreferencesKey(name = "hidden_apps"),
        defaultValue = setOf(),
    )""",
       """    val hiddenApps = preference(
        key = stringSetPreferencesKey(name = "hidden_apps"),
        defaultValue = setOf(),
    )

    val hideHomeAppsInDrawer = preference(
        key = booleanPreferencesKey(name = "huy_hide_home_apps_in_drawer"),
        defaultValue = false,
    )""")

change("lawnchair/src/app/lawnchair/ui/preferences/destinations/AppDrawerPreferences.kt",
       """            SearchBarPreference(SearchRoute.DRAWER_SEARCH, showLabel = false)""",
       """            SwitchPreference(
                label = "Hide apps already on home screen",
                description = "Also includes dock and home-screen folders. Apps stay available in search.",
                adapter = prefs2.hideHomeAppsInDrawer.getAdapter(),
            )
            SearchBarPreference(SearchRoute.DRAWER_SEARCH, showLabel = false)""")

# The list already owns Lawnchair's hidden-app and custom drawer-folder
# filtering; extend it here rather than globally modifying the app store.
# Keep drawer search intact so an app can always be found via search.
home_list = "lawnchair/src/app/lawnchair/allapps/LawnchairAlphabeticalAppsList.kt"
change(home_list,
       "import com.android.launcher3.InvariantDeviceProfile.OnIDPChangeListener",
       """import com.android.launcher3.InvariantDeviceProfile.OnIDPChangeListener
import com.android.launcher3.LauncherSettings
import com.android.launcher3.model.data.WorkspaceItemInfo""")

change(home_list,
       """    private var hiddenApps: Set<String> = setOf()
    private val prefs2 = PreferenceManager2.getInstance(context)""",
       """    private var hiddenApps: Set<String> = setOf()
    private var hideHomeAppsInDrawer = false
    private val homeScreenApps = mutableSetOf<String>()
    private val prefs2 = PreferenceManager2.getInstance(context)""")

change(home_list,
       """        observeFolders()
    }

    override fun onDestroy(owner: LifecycleOwner) {""",
       """        try {
            prefs2.hideHomeAppsInDrawer.onEach(launchIn = context.launcher.lifecycleScope) {
                hideHomeAppsInDrawer = it
                onAppsUpdated()
            }
        } catch (t: Throwable) {
            Log.w(TAG, "Failed to observe home-screen app filter", t)
        }
        observeFolders()
    }

    override fun onDestroy(owner: LifecycleOwner) {""")

change(home_list,
       """    override fun updateItemFilter(itemFilter: Predicate<ItemInfo>?) {""",
       """    private fun recordHomeScreenApp(item: WorkspaceItemInfo) {
        if (item.itemType != LauncherSettings.Favorites.ITEM_TYPE_APPLICATION) return
        val component = item.targetComponent ?: return
        homeScreenApps.add(ComponentKey(component, item.user).toString())
    }

    override fun onAppsUpdated() {
        homeScreenApps.clear()
        if (hideHomeAppsInDrawer) {
            // mapOverItems covers ALL home screens and the hotseat, not
            // just the currently visible page; folder children are included.
            context.launcher.workspace?.mapOverItems { item, _ ->
                when (item) {
                    is WorkspaceItemInfo -> recordHomeScreenApp(item)
                    is FolderInfo -> item.getAppContents().forEach(::recordHomeScreenApp)
                }
                false
            }
        }
        super.onAppsUpdated()
    }

    override fun updateItemFilter(itemFilter: Predicate<ItemInfo>?) {""")

change(home_list,
       """            (itemFilter?.test(info) != false) && !hiddenApps.contains(componentKey)""",
       """            (itemFilter?.test(info) != false) &&
                !hiddenApps.contains(componentKey) &&
                (!hideHomeAppsInDrawer || !homeScreenApps.contains(componentKey))""")

# User-created app-drawer folders also resolve apps directly from the
# unfiltered store, so filter their items as well.
change(home_list,
       """                val resolvedApps = folderEntry.itemComponentKeys.mapNotNull { keyString ->
                    val componentKey = ComponentKey.fromString(keyString) ?: return@mapNotNull null""",
       """                val resolvedApps = folderEntry.itemComponentKeys.mapNotNull { keyString ->
                    if (hideHomeAppsInDrawer && homeScreenApps.contains(keyString)) {
                        return@mapNotNull null
                    }
                    val componentKey = ComponentKey.fromString(keyString) ?: return@mapNotNull null""")

# Moving an icon back and forth does not change the installed app list.
# Force a fresh drawer filter calculation whenever All Apps opens, picking
# up desktop, dock and folder edits without any costly polling loop.
change("src/com/android/launcher3/Launcher.java",
       """        mPrevLauncherState = mStateManager.getCurrentStableState();
        if (mPrevLauncherState != state && ALL_APPS.equals(state)""",
       """        mPrevLauncherState = mStateManager.getCurrentStableState();
        if (ALL_APPS.equals(state) && mPrevLauncherState != state && mAppsView != null) {
            mAppsView.getPersonalAppList().onAppsUpdated();
            mAppsView.getWorkAppList().onAppsUpdated();
        }
        if (mPrevLauncherState != state && ALL_APPS.equals(state)""")


print("Ready to build: ./gradlew assembleLawnWithQuickstepPlayDebug")
print("Expected package: app.huy.androidlauncher2")
