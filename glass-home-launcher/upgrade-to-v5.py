#!/usr/bin/env python3
"""Apply Pixel Home v5 behavior improvements to the original v4 native Java project."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
p = root/"app/src/main/java/dev/glasshome/launcher/MainActivity.java"
s = p.read_text()
def edit(old, new):
    global s
    count = s.count(old)
    if count != 1:
        raise RuntimeError("Unexpected Pixel Home base (matches=%s): %s" % (count, old[:100]))
    s = s.replace(old, new, 1)
def section(start, end, replacement):
    global s
    a = s.index(start)
    b = s.index(end, a)
    s = s[:a] + replacement + s[b:]
edit("import android.app.Activity;", "import android.app.Activity;\nimport android.graphics.Rect;")
edit("import android.view.DragEvent;", "import android.view.DragEvent;\nimport android.view.HapticFeedbackConstants;")
edit("import android.widget.LinearLayout;", "import android.widget.LinearLayout;\nimport android.widget.ListView;\nimport android.widget.BaseAdapter;")
edit("    private boolean reduceMotion = false;", """    private boolean reduceMotion = false;
    private boolean showDateHeader = true, swipeDownSearch = true, folderSpring = true;
    private int wallpaperDim = 18;""")
edit('        reduceMotion = prefs.getBoolean("reduce_motion", false);', """        reduceMotion = prefs.getBoolean("reduce_motion", false);
        showDateHeader = prefs.getBoolean("show_date_header", true);
        swipeDownSearch = prefs.getBoolean("swipe_down_search", true);
        folderSpring = prefs.getBoolean("folder_spring", true);
        wallpaperDim = Math.max(0, Math.min(75, prefs.getInt("wallpaper_dim", 18)));""")
edit('        int availableDp = (int) heightDp - 46 - 62 - 30 - 92 - (showSearchBar ? 64 : 0);',
     '        int availableDp = (int) heightDp - 46 - (showDateHeader ? 62 : 0) - 30 - 92 - (showSearchBar ? 64 : 0);')
edit('        body.addView(header, new LinearLayout.LayoutParams(-1, dp(62)));',
     '        body.addView(header, new LinearLayout.LayoutParams(-1, dp(showDateHeader ? 62 : 0)));')
edit('        header.addView(date, new LinearLayout.LayoutParams(-1, dp(46)));',
     '        if (showDateHeader) header.addView(date, new LinearLayout.LayoutParams(-1, dp(46)));')

section("    private void showHomeOptions() {", "    private boolean fits(", """    private interface HomeChoice { void choose(int index); }

    private void showActionSheet(String title, String[] actions, HomeChoice action) {
        LinearLayout panel = new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20), dp(16), dp(20), dp(25));
        TextView heading = text(title, 17, 0xFF202124, true);
        heading.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        panel.addView(heading, new LinearLayout.LayoutParams(-1, dp(45)));
        AlertDialog dialog = new AlertDialog.Builder(this).setView(panel).create();
        for (int i = 0; i < actions.length; i++) {
            final int selected = i;
            TextView entry = text(actions[i], 15, 0xFF202124, false);
            entry.setGravity(Gravity.CENTER_VERTICAL | Gravity.START);
            entry.setPadding(dp(18), 0, dp(10), 0);
            entry.setBackground(rounded(0xFFF0F2F5, 20));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, dp(54));
            lp.topMargin = dp(6);
            panel.addView(entry, lp);
            entry.setOnClickListener(v -> { dialog.dismiss(); action.choose(selected); });
        }
        dialog.setOnShowListener(ignored -> {
            if (dialog.getWindow() != null) {
                dialog.getWindow().setGravity(Gravity.BOTTOM);
                dialog.getWindow().setLayout(-1, -2);
                dialog.getWindow().setBackgroundDrawable(rounded(0xFFFAFBFF, 25));
            }
            if (!reduceMotion) {
                panel.setTranslationY(dp(72)); panel.setAlpha(0f);
                panel.animate().translationY(0).alpha(1f).setDuration(240).start();
            }
        });
        dialog.show();
    }

    private void showHomeOptions() {
        showActionSheet("Home screen", new String[]{
                "Wallpaper & style", "Widgets", "Home settings", "Edit home screen"
        }, choice -> {
            if (choice == 0) showWallpaperPicker();
            else if (choice == 1) showWidgetPicker();
            else if (choice == 2) showSettings();
            else changeEditing(true);
        });
    }

    private void showWallpaperPicker() {
        try { startActivity(new Intent(Intent.ACTION_SET_WALLPAPER)); }
        catch (Exception error) {
            try { startActivity(new Intent("android.settings.WALLPAPER_SETTINGS")); }
            catch (Exception other) { toast("No wallpaper picker installed"); }
        }
    }

""")

edit("""        tile.setOnLongClickListener(v -> {
            if (!editing) changeEditingWithoutRebuild(true);
            ClipData data = ClipData.newPlainText("launcher-id", key);
            View.DragShadowBuilder shadow = new View.DragShadowBuilder(iconBox);
            tile.startDragAndDrop(data, shadow, null, 0);
            return true;
        });""", """        tile.setOnLongClickListener(v -> {
            v.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
            if (!editing) changeEditingWithoutRebuild(true);
            ClipData data = ClipData.newPlainText("launcher-id", key);
            View.DragShadowBuilder shadow = new View.DragShadowBuilder(iconBox) {
                @Override public void onProvideShadowMetrics(android.graphics.Point size,
                                                                 android.graphics.Point touch) {
                    int enlarged = (int)(iconSize * 1.17f);
                    size.set(enlarged, enlarged); touch.set(enlarged / 2, enlarged / 2);
                }
                @Override public void onDrawShadow(Canvas canvas) {
                    canvas.save(); canvas.scale(1.17f, 1.17f);
                    iconBox.draw(canvas); canvas.restore();
                }
            };
            if (tile.startDragAndDrop(data, shadow, null, 0))
                tile.animate().alpha(.30f).scaleX(.93f).scaleY(.93f)
                        .setDuration(reduceMotion ? 0 : 115).start();
            return true;
        });""")
edit("""            if (event.getAction() == DragEvent.ACTION_DRAG_ENTERED) {
                view.animate().scaleX(1.09f).scaleY(1.09f).setDuration(100).start();""",
     """            if (event.getAction() == DragEvent.ACTION_DRAG_ENTERED) {
                iconBox.animate().scaleX(1.18f).scaleY(1.18f)
                        .setDuration(reduceMotion ? 0 : 155)
                        .setInterpolator(new OvershootInterpolator(.75f)).start();""")
edit("""            } else if (event.getAction() == DragEvent.ACTION_DRAG_EXITED ||
                    event.getAction() == DragEvent.ACTION_DRAG_ENDED) {
                view.animate().scaleX(1f).scaleY(1f).setDuration(130).start();""",
     """            } else if (event.getAction() == DragEvent.ACTION_DRAG_EXITED ||
                    event.getAction() == DragEvent.ACTION_DRAG_ENDED) {
                iconBox.animate().scaleX(1f).scaleY(1f).setDuration(145).start();
                view.animate().scaleX(1f).scaleY(1f).alpha(1f).setDuration(160).start();""")
edit("""                view.animate().scaleX(1f).scaleY(1f).setDuration(130).start();
                String dragged = readDrag(event);
                if (dragged != null) dropOnTile(dragged, key);""",
     """                iconBox.animate().scaleX(1f).scaleY(1f).setDuration(145).start();
                String dragged = readDrag(event);
                if (dragged != null) {
                    float midX = iconBox.getLeft() + iconBox.getWidth() / 2f;
                    float midY = iconBox.getTop() + iconBox.getHeight() / 2f;
                    boolean center = Math.abs(event.getX()-midX) < iconSize*.44f &&
                            Math.abs(event.getY()-midY) < iconSize*.44f;
                    dropOnTile(dragged, key, center);
                }""")
edit("    private void dropOnTile(String from, String target) {",
     "    private void dropOnTile(String from, String target, boolean makeFolder) {")
edit("            if (!a.isFolder() && !a.isWidget() && !b.isWidget()) {",
     "            if (!a.isFolder() && !a.isWidget() && !b.isWidget() && (makeFolder || b.isFolder())) {")
edit("            } else if(!b.isWidget()) {", "            } else if(!b.isWidget() && makeFolder) {")
edit('            } else {toast("Drop apps on an app or folder");return;}\n        } else return;',
     """            } else if (!b.isWidget()) {
                dock.remove(sourceDock);
                home.add(targetHome, new Item(dragged));
            } else {toast("Drop apps on an app or folder");return;}
        } else return;""")
edit("                    if(key!=null) moveToPage(key,targetPage);",
     """                    if (key != null) {
                        int col = Math.max(0, Math.min(columns - 1,
                                (int)((event.getX() - dp(12))/Math.max(1,tileWidth))));
                        int row = Math.max(0, Math.min(rows - 1,
                                (int)((event.getY() - dp(6))/Math.max(1,homeTileHeightPx))));
                        moveToCell(key,targetPage,row,col);
                    }""")
edit("    private void removeHomeApp(String id) {", """    private void moveToCell(String key,int page,int row,int col) {
        int old = homeIndex(key);
        if (old < 0) return;
        Item item = home.get(old);
        int insertion = home.size();
        for (Placement cell : placements) {
            if (cell.item == item) continue;
            if (cell.page > page || (cell.page == page &&
                    (cell.row > row || (cell.row == row && cell.col >= col)))) {
                insertion = cell.index; break;
            }
        }
        home.remove(old);
        if (old < insertion) insertion--;
        home.add(Math.max(0,Math.min(home.size(),insertion)),item);
        currentPage=page; editing=false;
        saveLayout(); refreshScreen();
    }

    private void removeHomeApp(String id) {""")
section("    // Real Android AppWidgetHost:", "    private void requestWidget(", """    /** Search installed real Android widgets and request bind/configure via AppWidgetHost. */
    private void showWidgetPicker() {
        List<AppWidgetProviderInfo> providers = widgetManager.getInstalledProviders();
        if (providers == null || providers.isEmpty()) { toast("No widgets installed"); return; }
        providers.sort(Comparator.comparing(x -> String.valueOf(x.loadLabel(getPackageManager())),
                String.CASE_INSENSITIVE_ORDER));
        ArrayList<AppWidgetProviderInfo> filtered = new ArrayList<>(providers);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(dp(12), dp(8), dp(12), dp(8));
        EditText input = new EditText(this);
        input.setSingleLine(true); input.setHint("Search widgets");
        content.addView(input, new LinearLayout.LayoutParams(-1, dp(55)));
        ListView list = new ListView(this);
        content.addView(list, new LinearLayout.LayoutParams(-1, dp(430)));
        BaseAdapter adapter = new BaseAdapter() {
            public int getCount() { return filtered.size(); }
            public Object getItem(int i) { return filtered.get(i); }
            public long getItemId(int i) { return i; }
            public View getView(int i, View old, ViewGroup parent) {
                AppWidgetProviderInfo widget = filtered.get(i);
                LinearLayout row = new LinearLayout(MainActivity.this);
                row.setGravity(Gravity.CENTER_VERTICAL); row.setPadding(dp(9),dp(7),dp(9),dp(7));
                ImageView icon = new ImageView(MainActivity.this);
                try { icon.setImageDrawable(getPackageManager().getApplicationIcon(
                        widget.provider.getPackageName())); } catch(Exception ignored) { }
                row.addView(icon,new LinearLayout.LayoutParams(dp(40),dp(40)));
                LinearLayout labels = new LinearLayout(MainActivity.this);
                labels.setPadding(dp(13),0,0,0);
                labels.setOrientation(LinearLayout.VERTICAL);
                TextView name = text(String.valueOf(widget.loadLabel(getPackageManager())),15,0xFF202124,true);
                name.setGravity(Gravity.START);
                labels.addView(name);
                TextView packageName = text(widget.provider.getPackageName(),12,0xFF666B73,false);
                packageName.setGravity(Gravity.START);
                labels.addView(packageName);
                row.addView(labels);
                return row;
            }
        };
        list.setAdapter(adapter);
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Widgets")
                .setView(content).setNegativeButton("Cancel",null).create();
        list.setOnItemClickListener((parent, view, i, id) -> {
            AppWidgetProviderInfo chosen = filtered.get(i);
            dialog.dismiss(); requestWidget(chosen);
        });
        input.addTextChangedListener(new TextWatcher() {
            public void beforeTextChanged(CharSequence s,int start,int count,int after) { }
            public void onTextChanged(CharSequence s,int start,int before,int count) {
                String query=s.toString().toLowerCase(Locale.ROOT);
                filtered.clear();
                for (AppWidgetProviderInfo p:providers)
                    if (String.valueOf(p.loadLabel(getPackageManager())).toLowerCase(Locale.ROOT).contains(query)
                            || p.provider.getPackageName().toLowerCase(Locale.ROOT).contains(query))
                        filtered.add(p);
                adapter.notifyDataSetChanged();
            }
            public void afterTextChanged(Editable e) { }
        });
        dialog.show();
    }

""")
edit('                if (!editing && dy > dp(115) && Math.abs(dx) < dp(55)) {',
     '                if (!editing && swipeDownSearch && dy > dp(115) && Math.abs(dx) < dp(55)) {')
edit('            canvas.drawColor(0x12000000);','            canvas.drawColor(Color.argb(wallpaperDim,0,0,0));')
edit('            // Pixel-style page motion uses simple horizontal snapping without parallax scaling.',
     """            if (!reduceMotion) for (int i=0;i<pageViews.size();i++) {
                float distance=Math.min(1f,Math.abs(x/(float)width-i));
                View page=pageViews.get(i);
                page.setScaleX(1f-distance*.035f);
                page.setScaleY(1f-distance*.035f);
                page.setAlpha(1f-distance*.18f);
            }""")
section("    private void showSettings() {", "    private void showGridSettings() {", """    /** Lawnchair-inspired sections using the existing Pixel Home settings and data. */
    private void showSettings() {
        showActionSheet("Pixel Home settings",new String[]{
                "Home screen", "Dock & search", "Folders", "Appearance & fonts",
                "Gestures & animations", "Widgets", "Default Home app", "Reset layout"
        },i -> {
            switch (i) {
                case 0: showActionSheet("Home screen",new String[]{
                    "Grid · "+columns+"×"+rows,
                    "Show date · "+(showDateHeader?"On":"Off"),"Edit home screen"},j->{
                        if(j==0)showGridSettings();
                        else if(j==1)saveToggle("show_date_header",showDateHeader=!showDateHeader);
                        else changeEditing(true);
                    }); break;
                case 1: showActionSheet("Dock & search",new String[]{
                    "Show search bar · "+(showSearchBar?"On":"Off"),"Search apps"},j->{
                        if(j==0)saveToggle("show_search_bar",showSearchBar=!showSearchBar);
                        else showSearch();
                    }); break;
                case 2: showActionSheet("Folders",new String[]{
                    "Folder previews · 3×3",
                    "Spring animation · "+(folderSpring?"On":"Off")},j->{
                        if(j==1)saveToggle("folder_spring",folderSpring=!folderSpring);
                    }); break;
                case 3: showActionSheet("Appearance & fonts",new String[]{
                    "Choose label font · "+labelFont+" "+labelSizeSp+" sp",
                    "Wallpaper & style","Wallpaper dim · "+wallpaperDim+"%"},j->{
                        if(j==0)showFontSettings();
                        else if(j==1)showWallpaperPicker();
                        else showDimSetting();
                    }); break;
                case 4: showActionSheet("Gestures & animations",new String[]{
                    "Swipe down search · "+(swipeDownSearch?"On":"Off"),
                    "Reduce motion · "+(reduceMotion?"On":"Off"),"Edit mode"},j->{
                        if(j==0)saveToggle("swipe_down_search",swipeDownSearch=!swipeDownSearch);
                        else if(j==1)saveToggle("reduce_motion",reduceMotion=!reduceMotion);
                        else changeEditing(true);
                    }); break;
                case 5: showWidgetPicker(); break;
                case 6: openHomeSettings(); break;
                case 7: confirmResetLayout(); break;
            }
        });
    }

    private void saveToggle(String key,boolean enabled) {
        prefs.edit().putBoolean(key,enabled).apply();
        refreshScreen();
    }

    private void showDimSetting() {
        final int[] chosen={wallpaperDim};
        LinearLayout panel=new LinearLayout(this);
        panel.setOrientation(LinearLayout.VERTICAL);
        panel.setPadding(dp(20),dp(12),dp(20),dp(12));
        TextView caption=text("Wallpaper darkness · "+wallpaperDim+"%",15,Color.DKGRAY,false);
        panel.addView(caption);
        android.widget.SeekBar seek=new android.widget.SeekBar(this);
        seek.setMax(75); seek.setProgress(wallpaperDim);
        panel.addView(seek);
        seek.setOnSeekBarChangeListener(new android.widget.SeekBar.OnSeekBarChangeListener(){
            public void onProgressChanged(android.widget.SeekBar b,int n,boolean fromUser) {
                chosen[0]=n; caption.setText("Wallpaper darkness · "+n+"%");
            }
            public void onStartTrackingTouch(android.widget.SeekBar b){}
            public void onStopTrackingTouch(android.widget.SeekBar b){}
        });
        new AlertDialog.Builder(this).setTitle("Wallpaper & style").setView(panel)
                .setNegativeButton("Cancel",null)
                .setPositiveButton("Apply",(d,w)->{
                    wallpaperDim=chosen[0];
                    prefs.edit().putInt("wallpaper_dim",wallpaperDim).apply();
                    if(backdrop!=null)backdrop.invalidate();
                }).show();
    }

    private void confirmResetLayout() {
        new AlertDialog.Builder(this).setTitle("Reset arrangement?")
                .setMessage("This removes your folders and widgets and restores alphabetical apps.")
                .setNegativeButton("Cancel",null)
                .setPositiveButton("Reset",(d,w)->{
                    for(Item old:new ArrayList<>(home)) if(old.isWidget())
                        try{widgetHost.deleteAppWidgetId(old.widgetId());}catch(Exception ignored){}
                    home.clear(); dock.clear();
                    for(String id:installed.keySet()) home.add(new Item(id));
                    chooseInitialDock(); currentPage=0;
                    saveLayout();refreshScreen();
                }).show();
    }

""")
edit('        ref[0].show();\n    }\n\n    /** Search installed real Android widgets',
     '''        ref[0].show();
        if (folderSpring && !reduceMotion) {
            container.setScaleX(.9f);container.setScaleY(.9f);container.setAlpha(.5f);
            container.animate().scaleX(1f).scaleY(1f).alpha(1f)
                    .setDuration(250).setInterpolator(new OvershootInterpolator(.7f)).start();
        }
    }

    /** Search installed real Android widgets''')
p.write_text(s)
b = root/"app/build.gradle"
b.write_text(b.read_text().replace("versionCode 4","versionCode 5").replace("versionName '1.3'","versionName '1.4'"))
print("Pixel Home v5 behavior upgrades applied")
