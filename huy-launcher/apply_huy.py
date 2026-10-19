#!/usr/bin/env python3
"""Source-only changes for Huy android launcher based on Lawnchair 15 Beta 3.

Upstream revision: v15.0.0-beta3.0 / 505dbc40e6154c05158b5d0271c45f6a885a411b.
Use official Android Gradle Plugin to build and sign; do not repack APK binaries.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(".").resolve()


def change(path, old, new):
    file = root / path
    source = file.read_text(encoding="utf-8")
    matches = source.count(old)
    if matches != 1:
        raise RuntimeError(f"Expected 1 match for {path} but found {matches}: {old[:90]!r}")
    file.write_text(source.replace(old, new, 1), encoding="utf-8")
    print("Modified:", path)


layout = "src/com/android/launcher3/folder/ClippedFolderIconLayoutRule.java"
organizer = "src/com/android/launcher3/folder/FolderGridOrganizer.java"

# The folder *icon* shows up to nine icons, without altering the open folder's grid.
change(layout,
       "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 4;",
       "public static final int MAX_NUM_ITEMS_IN_PREVIEW = 9;")

# Keep Lawnchair's 1-4 preview positions unchanged. Position items 5-9 in
# equal 3x3 cells, using RTL ordering when appropriate.
change(layout,
       "        if (index == EXIT_INDEX) {",
       """        if (curNumItems > 4 && index >= 0 && index < MAX_NUM_ITEMS_IN_PREVIEW) {
            final float cellSize = mAvailableSpace / 3f;
            final float drawnIconSize = mIconSize * totalScale;
            final int row = index / 3;
            final int col = mIsRtl ? 2 - (index % 3) : index % 3;
            mTmpPoint[0] = (col + 0.5f) * cellSize - drawnIconSize / 2f;
            mTmpPoint[1] = (row + 0.5f) * cellSize - drawnIconSize / 2f;
        } else if (index == EXIT_INDEX) {""")

# The legacy radius formula must keep its old denominator for 1-4 icons.
change(layout,
       """                MIN_NUM_ITEMS_IN_PREVIEW) / (MAX_NUM_ITEMS_IN_PREVIEW - MIN_NUM_ITEMS_IN_PREVIEW));""",
       """                MIN_NUM_ITEMS_IN_PREVIEW) / (4 - MIN_NUM_ITEMS_IN_PREVIEW));""")

change(layout,
       """        if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;
        }
""",
       """        if (numItems > 4) {
            scale = 0.30f; // Three icons per row and column.
        } else if (numItems <= 3) {
            scale = MAX_SCALE;
        } else {
            scale = MIN_SCALE;
        }
""")

# Select the top-left 3x3 preview items from large folders.
change(organizer, "private static final int PREVIEW_MAX_ROWS = 2;",
       "private static final int PREVIEW_MAX_ROWS = 3;")
change(organizer, "private static final int PREVIEW_MAX_COLUMNS = 2;",
       "private static final int PREVIEW_MAX_COLUMNS = 3;")
change(organizer, "@return True iff the icon is in the 2x2 upper left quadrant of the Folder.",
       "@return True iff the icon is in the 3x3 upper left area of the Folder.")
change(organizer, "// First page items are laid out such that the first 4 items are always in the upper",
       "// First page items are laid out such that the first 9 items are always in the upper")
change(organizer, "// If we have less than 4 items do this",
       "// If we have fewer than 9 items do this")

# Build a separately installable Play-flavor debug app so existing Lawnchair
# stays installed. Android Gradle Plugin handles packaging and signing.
change("build.gradle", 'applicationId "app.lawnchair.play"',
       'applicationId "app.huy.androidlauncher"')
change("build.gradle", 'resValue("string", "derived_app_name", "Lawnchair (Debug)")',
       'resValue("string", "derived_app_name", "Huy android launcher")')
change("build.gradle", 'resValue("string", "derived_app_name", "Lawnchair")',
       'resValue("string", "derived_app_name", "Huy android launcher")')

print("Ready: ./gradlew assembleLawnWithQuickstepPlayDebug")
print("Package: app.huy.androidlauncher.debug")
