#!/usr/bin/env python3
"""Apply the small Pixel Home customizations to Lawnchair 16 upstream source.

Target checkout: https://github.com/LawnchairLauncher/lawnchair (16-dev)
Copyright remains with the respective upstream copyright holders.
Changes: 3x3 folder PREVIEWS, max home grid 12 rows / 6 columns,
and making the Lawnchair Deck + font options visible.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()

def change(path, old, new):
    target = root / path
    text = target.read_text(encoding="utf-8-sig")
    if old not in text:
        raise SystemExit(f"Upstream source changed; refusing unsafe patch: {path}: {old[:70]}")
    text = text.replace(old, new, 1)
    target.write_text(text, encoding="utf-8")
    print("Patched", path)

layout = "src/com/android/launcher3/folder/ClippedFolderIconLayoutRule.java"
change(layout, "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 4;",
       "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 9;")
change(layout,
    "    private void getPosition(int index, int curNumItems, float[] result) {",
    """    private void getPosition(int index, int curNumItems, float[] result) {
        // Nine-icon folder badge, kept distinct from the opened folder's grid.
        if (curNumItems > 4 && index >= 0) {
            float size = mIconSize * scaleForItem(curNumItems, 0);
            float cell = mAvailableSpace / 3f;
            int col = mIsRtl ? 2 - (index % 3) : index % 3;
            int row = index / 3;
            result[0] = col * cell + (cell - size) / 2f;
            result[1] = row * cell + (cell - size) / 2f;
            return;
        }""")
change(layout,
    "    public float scaleForItem(int numItems, int page) {",
    """    public float scaleForItem(int numItems, int page) {
        // Fit three mini icons across each preview dimension.
        if (numItems > 4 && page == 0) return 0.29f * mBaselineIconScale;""")

organizer = "src/com/android/launcher3/folder/FolderGridOrganizer.java"
change(organizer, "private static final int PREVIEW_MAX_ROWS = 2;",
       "private static final int PREVIEW_MAX_ROWS = 3;")
change(organizer, "private static final int PREVIEW_MAX_COLUMNS = 2;",
       "private static final int PREVIEW_MAX_COLUMNS = 3;")

grid = "lawnchair/src/app/lawnchair/ui/preferences/destinations/HomeScreenGridPreferences.kt"
change(grid, "val maxGridSize = if (increaseMaxGridSize.state.value) 20 else 10",
       "val maxGridSize = 12")
text = (root / grid).read_text()
if "valueRange = 3..maxGridSize" not in text:
    raise SystemExit("Grid slider no longer matches upstream")
# The slider for columns gets an upper limit of six, while row sliders remain twelve.
# Do not force hotseat dimensions: keep upstream's independent dock options.
lines = text.splitlines(keepends=True)
for i, line in enumerate(lines):
    if "label = stringResource(id = R.string.columns)" in line:
        for j in range(i, min(i + 7, len(lines))):
            if "valueRange = 3..maxGridSize" in lines[j]:
                lines[j] = lines[j].replace("3..maxGridSize", "3..6")
                break
(root / grid).write_text("".join(lines))

prefs = "lawnchair/src/app/lawnchair/preferences2/PreferenceManager2.kt"
change(prefs,
    'key = booleanPreferencesKey(name = "show_deck_layout"),\n        defaultValue = false,',
    'key = booleanPreferencesKey(name = "show_deck_layout"),\n        defaultValue = true,')
change(prefs,
    'key = booleanPreferencesKey(name = "enable_font_selection"),\n        defaultValue = context.resources.getBoolean(R.bool.config_default_enable_font_selection),',
    'key = booleanPreferencesKey(name = "enable_font_selection"),\n        defaultValue = true,')

# Build against the stable Android 16 (API 36) SDK available on GitHub runners.
# Lawnchair upstream currently requests an unreleased 37.2 platform.
gradle = "build.gradle"
change(gradle, 'buildToolsVersion "37.0.0"', 'buildToolsVersion "36.0.0"')
change(gradle, 'compileSdk {\\n                version = release(37) {\\n                    minorApiLevel = 2\\n                }\\n            }', 'compileSdk 36')
change(gradle, 'targetSdk = 37', 'targetSdk = 36')

print("Complete. Select Deck once in Settings > Home screen to populate all apps.")
