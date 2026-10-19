#!/usr/bin/env python3
"""Pixel Home v6 patch over the reproducible v5 source in this repository."""
from pathlib import Path
import sys
p=Path(sys.argv[1])/"app/src/main/java/dev/glasshome/launcher/MainActivity.java"
s=p.read_text()
def replace(a,b):
 global s
 if a not in s: raise SystemExit("v6 upstream mismatch: "+a[:90])
 s=s.replace(a,b,1)
def block(a,b,contents):
 global s
 i=s.find(a); j=s.find(b,i)
 if i<0 or j<0: raise SystemExit("v6 block mismatch: "+a)
 s=s[:i]+contents+s[j:]

replace('private final ArrayList<String> dock = new ArrayList<>();',
'''private final ArrayList<String> dock = new ArrayList<>();
    private final LinkedHashMap<String, Item> dockFolders = new LinkedHashMap<>();
    private final HashSet<String> hiddenApps = new HashSet<>();
    private int dockSlots = 5;
    private String dockStyle = "Pixel";''')
replace('wallpaperDim = Math.max(0, Math.min(75, prefs.getInt("wallpaper_dim", 18)));',
'''wallpaperDim = Math.max(0, Math.min(100, prefs.getInt("wallpaper_dim", 18)));
        dockSlots = Math.max(3, Math.min(9, prefs.getInt("dock_slots", 5)));
        dockStyle = prefs.getString("dock_style", "Pixel");
        hiddenApps.clear();
        hiddenApps.addAll(prefs.getStringSet("hidden_apps", Collections.emptySet()));''')
replace('home.clear(); dock.clear();\n        if (!prefs.contains(KEY_HOME))',
        'home.clear(); dock.clear(); dockFolders.clear();\n        if (!prefs.contains(KEY_HOME))')
replace('for (int i = 0; i < dockArray.length(); i++) dock.add(dockArray.optString(i));',
'''for (int i = 0; i < dockArray.length(); i++) {
                    JSONObject json = dockArray.optJSONObject(i);
                    if (json != null && json.has("folder")) {
                        Item f = new Item(json.optString("folder"));
                        f.name = json.optString("name","Folder");
                        JSONArray apps = json.optJSONArray("apps");
                        if (apps != null) for (int j=0;j<apps.length();j++) f.children.add(apps.optString(j));
                        dockFolders.put(f.id,f); dock.add(f.id);
                    } else {
                        String id = dockArray.optString(i);
                        if (!id.isEmpty()) dock.add(id);
                    }
                }''')
s=s.replace('if (dock.size() == 4) break;', 'if (dock.size() == Math.min(dockSlots, 4)) break;')
replace('''        dock.removeIf(id -> !installed.containsKey(id) || !seen.add(id));''',
'''        dock.removeIf(id -> {
            Item f=dockFolders.get(id);
            if(f!=null) {
                f.children.removeIf(app -> hiddenApps.contains(app) || !installed.containsKey(app) || !seen.add(app));
                if(f.children.isEmpty()) { dockFolders.remove(id); return true; }
                return false;
            }
            return hiddenApps.contains(id) || !installed.containsKey(id) || !seen.add(id);
        });''')
replace('item.children.removeIf(id -> !installed.containsKey(id) || !seen.add(id));',
        'item.children.removeIf(id -> hiddenApps.contains(id) || !installed.containsKey(id) || !seen.add(id));')
replace('!installed.containsKey(item.id) || !seen.add(item.id)',
        'hiddenApps.contains(item.id) || !installed.containsKey(item.id) || !seen.add(item.id)')
replace('if (!seen.contains(id)) { home.add(new Item(id)); seen.add(id); }',
        'if (!hiddenApps.contains(id) && !seen.contains(id)) { home.add(new Item(id)); seen.add(id); }')
replace('''        prefs.edit().putString(KEY_HOME, homeJson.toString())
                .putString(KEY_DOCK, new JSONArray(dock).toString()).apply();''',
'''        JSONArray dockJson = new JSONArray();
        for(String id:dock) {
            Item f=dockFolders.get(id);
            if(f==null) dockJson.put(id); // Old v5 dock format is still supported.
            else {
                JSONObject obj=new JSONObject();
                try { obj.put("folder",f.id); obj.put("name",f.name);
                      obj.put("apps",new JSONArray(f.children)); dockJson.put(obj); }
                catch(JSONException ignored){}
            }
        }
        prefs.edit().putString(KEY_HOME,homeJson.toString())
            .putString(KEY_DOCK,dockJson.toString())
            .putStringSet("hidden_apps",new HashSet<>(hiddenApps)).apply();''')
replace('homeTileHeightPx = dp(Math.max(68, availableDp / rows));',
        'homeTileHeightPx = dp(Math.max(103, availableDp / rows));')
replace('int maxIconDp = inDock ? 60 : (columns >= 6 ? 43',
        'int maxIconDp = inDock ? (dockSlots >= 7 ? 40 : dockSlots >= 6 ? 47 : 60) : (columns >= 6 ? 43')
replace('int iconSize = inDock ? dp(60) : Math.max(dp(28), Math.min(dp(maxIconDp), homeTileHeightPx - dp(30)));',
        'int iconSize = inDock ? dp(maxIconDp) : Math.max(dp(28), Math.min(dp(maxIconDp), homeTileHeightPx - dp(50)));')
replace('''label.setSingleLine(true);
        label.setEllipsize(TextUtils.TruncateAt.END);''',
'''label.setSingleLine(false); label.setMaxLines(3);
        label.setEllipsize(null); label.setHorizontallyScrolling(false);
        label.setAutoSizeTextTypeUniformWithConfiguration(8,labelSizeSp,1,
                android.util.TypedValue.COMPLEX_UNIT_SP);''')
replace('new LinearLayout.LayoutParams(-1, dp(28));\n            labelParams.topMargin = dp(homeTileHeightPx < dp(73) ? 2 : 5);',
        'new LinearLayout.LayoutParams(-1, dp(51));\n            labelParams.topMargin = dp(3);')
replace('tile.setContentDescription(item.isFolder() ? "Folder " + item.name : appName(item.id));',
'''tile.setContentDescription(item.isFolder() ? "Folder " + item.name : appName(item.id));
        tile.setTooltipText(item.isFolder() ? item.name : appName(item.id));''')
replace('return info == null ? "App" : String.valueOf(info.loadLabel(getPackageManager()));',
'''if(info == null && dockFolders.containsKey(id)) return dockFolders.get(id).name;
        return info == null ? "App" : String.valueOf(info.loadLabel(getPackageManager()));''')

block('    private void buildDock() {','    private View buildTile(','''    private void buildDock() {
        LinearLayout outer=new LinearLayout(this);
        outer.setOrientation(LinearLayout.VERTICAL);
        outer.setPadding(dp(12),0,dp(12),dp(6));
        body.addView(outer,new LinearLayout.LayoutParams(-1,dp(showSearchBar?150:92)));
        LinearLayout favorites=new LinearLayout(this);
        favorites.setGravity(Gravity.CENTER);
        if("Pill".equals(dockStyle)) favorites.setBackground(rounded(0x60272B31,36));
        else if("Outline".equals(dockStyle)) {
            GradientDrawable bg=rounded(0x20000000,32);
            bg.setStroke(dp(1),0x80FFFFFF); favorites.setBackground(bg);
        }
        outer.addView(favorites,new LinearLayout.LayoutParams(-1,dp(82)));
        int width=(getResources().getDisplayMetrics().widthPixels-dp(24))/dockSlots;
        for(int i=0;i<dockSlots;i++) {
            final int slot=i;
            View tile;
            if(i<dock.size()) {
                String id=dock.get(i);
                Item folder=dockFolders.get(id);
                tile=buildTile(folder==null?new Item(id):folder,true,width);
            } else {
                FrameLayout blank=new FrameLayout(this);
                blank.setOnClickListener(v->showSearch());
                blank.setOnDragListener((v,e)->{
                    if(e.getAction()==DragEvent.ACTION_DRAG_STARTED) return true;
                    if(e.getAction()==DragEvent.ACTION_DROP) {
                        String key=readDrag(e); if(key!=null) moveToDockSlot(key,slot);
                    }
                    return true;
                });
                tile=blank;
            }
            favorites.addView(tile,new LinearLayout.LayoutParams(0,dp(82),1));
        }
        favorites.setOnLongClickListener(v->{showHomeOptions();return true;});
        if(showSearchBar) {
            TextView search=text("G    Search your apps                 ◉",14,Color.WHITE,false);
            search.setTypeface(Typeface.create("sans-serif-medium",Typeface.NORMAL));
            search.setGravity(Gravity.CENTER_VERTICAL|Gravity.START);
            search.setPadding(dp(19),0,dp(12),0);
            search.setBackground(rounded(0xBD263138,32));
            LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,dp(50));
            lp.topMargin=dp(5);outer.addView(search,lp);
            search.setOnClickListener(v->showSearch());
        }
    }

''')

block('        tile.setOnLongClickListener(v -> {','        tile.setOnDragListener((view, event) -> {','''        // Holding still opens actions; holding then moving enters native Android drag mode.
        final float[] down=new float[2];
        final long[] started=new long[1];
        final boolean[] consumed={false};
        final Runnable[] popup=new Runnable[1];
        final Runnable drag=()->{
            if(consumed[0]) return;
            consumed[0]=true;
            handler.removeCallbacks(popup[0]);
            tile.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
            ClipData data=ClipData.newPlainText("launcher-id",key);
            View.DragShadowBuilder shadow=new View.DragShadowBuilder(iconBox);
            if(tile.startDragAndDrop(data,shadow,null,0)) {
                tile.animate().alpha(.35f).setDuration(reduceMotion?0:100).start();
            }
        };
        tile.setOnTouchListener((v,e)->{
            switch(e.getActionMasked()) {
                case MotionEvent.ACTION_DOWN:
                    down[0]=e.getX(); down[1]=e.getY();
                    started[0]=android.os.SystemClock.uptimeMillis();
                    consumed[0]=false;
                    popup[0]=()->{if(!consumed[0]){
                        consumed[0]=true;tile.performHapticFeedback(HapticFeedbackConstants.LONG_PRESS);
                        showItemActions(key);
                    }};
                    handler.postDelayed(popup[0],620);
                    return true;
                case MotionEvent.ACTION_MOVE:
                    float dist=(float)Math.hypot(e.getX()-down[0],e.getY()-down[1]);
                    long duration=android.os.SystemClock.uptimeMillis()-started[0];
                    if(!consumed[0] && duration>260 && dist>dp(10))drag.run();
                    return true;
                case MotionEvent.ACTION_CANCEL:
                    if(popup[0]!=null)handler.removeCallbacks(popup[0]);return true;
                case MotionEvent.ACTION_UP:
                    if(popup[0]!=null)handler.removeCallbacks(popup[0]);
                    if(!consumed[0])tile.performClick();
                    return true;
            }
            return true;
        });
''')

block('    private void dropOnTile(','    private void moveToPage(','''    private Item dockItem(int index) {
        String id=dock.get(index);
        return dockFolders.containsKey(id)?dockFolders.get(id):new Item(id);
    }
    private void moveToDockSlot(String from,int slot) {
        int sh=homeIndex(from),sd=dockIndex(from);
        if(sh<0 && sd<0) return;
        if(sd<0 && dock.size()>=dockSlots){toast("Dock is full");return;}
        Item moving=sh>=0?home.remove(sh):dockItem(sd);
        if(moving.isWidget()) {toast("Widgets stay on home pages");return;}
        if(sd>=0)dock.remove(sd);
        if(moving.isFolder())dockFolders.put(moving.id,moving);
        dock.add(Math.min(slot,dock.size()),moving.id);
        editing=false;saveLayout();refreshScreen();
    }
    private void dropOnTile(String from,String target,boolean center) {
        if(from.equals(target))return;
        int sh=homeIndex(from),th=homeIndex(target),sd=dockIndex(from),td=dockIndex(target);
        Item a=sh>=0?home.get(sh):sd>=0?dockItem(sd):null;
        Item b=th>=0?home.get(th):td>=0?dockItem(td):null;
        if(a==null||b==null||a.isWidget()||b.isWidget())return;
        if(center&&!a.isFolder()) {
            if(b.isFolder()){
                if(!b.children.contains(a.id))b.children.add(a.id);
                if(sh>=0)home.remove(a);else dock.remove(sd);
            }else {
                Item folder=Item.folder("Folder");
                folder.children.add(b.id);folder.children.add(a.id);
                if(th>=0)home.set(th,folder);
                else{dock.set(td,folder.id);dockFolders.put(folder.id,folder);}
                if(sh>=0)home.remove(a);else dock.remove(a.id);
            }
        }else if(sh>=0 && th>=0)Collections.swap(home,sh,th);
        else if(sd>=0 && td>=0)Collections.swap(dock,sd,td);
        else if(sh>=0 && td>=0) {
            Item old=dockItem(td);home.set(sh,old);dock.set(td,a.id);
            if(a.isFolder())dockFolders.put(a.id,a);
            if(old.isFolder())dockFolders.remove(old.id);
        }else if(sd>=0 && th>=0) {
            home.set(th,a);dock.set(sd,b.id);
            if(a.isFolder())dockFolders.remove(a.id);
            if(b.isFolder())dockFolders.put(b.id,b);
        }
        editing=false;saveLayout();refreshScreen();
    }

''')
replace('''        int index=homeIndex(key);
        if(index<0)return;''','''        int index=homeIndex(key);
        if(index<0 && dockIndex(key)>=0) {
            Item moving=dockItem(dockIndex(key));
            dock.remove(moving.id);
            if(moving.isFolder())dockFolders.remove(moving.id);
            home.add(moving);index=home.size()-1;
        }
        if(index<0)return;''')
replace('''    private void dissolveFolder(Item folder) {
        int index = home.indexOf(folder);
        if (index < 0) return;
        home.remove(index);
        for (int i = 0; i < folder.children.size(); i++)
            home.add(index + i, new Item(folder.children.get(i)));
        saveLayout(); refreshScreen();
    }''','''    private void dissolveFolder(Item folder) {
        int i=home.indexOf(folder),d=dock.indexOf(folder.id);
        if(i>=0)home.remove(i);
        if(d>=0){dock.remove(d);dockFolders.remove(folder.id);}
        int insertion=i>=0?i:home.size();
        for(String id:folder.children)home.add(insertion++,new Item(id));
        saveLayout();refreshScreen();
    }''')
replace('if (folder.children.isEmpty()) home.remove(folder);',
'''if(folder.children.isEmpty()) {
                                    home.remove(folder);dock.remove(folder.id);dockFolders.remove(folder.id);
                                }''')
replace('''            for (String id : installed.keySet()) {
                if (!appName(id).toLowerCase(Locale.getDefault()).contains(query)) continue;''',
'''            for (String id : installed.keySet()) {
                if (hiddenApps.contains(id)) continue;
                if (!appName(id).toLowerCase(Locale.getDefault()).contains(query)) continue;''')

block('    private void showItemActions(String key) {','    private void openAppInfo(','''    private void showItemActions(String key) {
        int hi=homeIndex(key),di=dockIndex(key);
        Item item=hi>=0?home.get(hi):di>=0?dockItem(di):null;
        if(item==null)return;
        ArrayList<String> menu=new ArrayList<>();
        if(item.isWidget()){menu.add("Resize widget");menu.add("Remove widget");}
        else if(item.isFolder()){
            menu.add("Open folder");menu.add("Rename folder");
            menu.add(di>=0?"Move folder to home":"Move folder to dock");
            menu.add("Ungroup folder");
        }else{
            menu.add("Hide app");menu.add("Uninstall app");menu.add("App info");
            if(di>=0)menu.add("Move to home");
            else if(dock.size()<dockSlots)menu.add("Move to dock");
        }
        new AlertDialog.Builder(this)
            .setTitle(item.isFolder()?item.name:appName(item.id))
            .setItems(menu.toArray(new String[0]),(dlg,choice)->{
                String action=menu.get(choice);
                switch(action){
                    case "Resize widget":resizeWidget(item);break;
                    case "Remove widget":removeWidget(item);break;
                    case "Open folder":openFolder(item);break;
                    case "Rename folder":renameFolder(item);break;
                    case "Ungroup folder":dissolveFolder(item);break;
                    case "Move folder to dock":case "Move to dock":moveToDockSlot(key,dock.size());break;
                    case "Move folder to home":case "Move to home":moveDockItemHome(item.id);break;
                    case "Hide app":hideApp(item.id);break;
                    case "Uninstall app":uninstallApp(item.id);break;
                    case "App info":openAppInfo(item.id);break;
                }
            }).setNegativeButton("Cancel",null).show();
    }
    private void moveDockItemHome(String id) {
        int index=dock.indexOf(id);if(index<0)return;
        Item item=dockItem(index);dock.remove(index);
        if(item.isFolder())dockFolders.remove(id);
        home.add(item);saveLayout();refreshScreen();
    }
    private void hideApp(String id) {
        new AlertDialog.Builder(this).setTitle("Hide "+appName(id)+"?")
            .setMessage("Only hides the app on Pixel Home. Show it again in Settings → Hidden apps.")
            .setNegativeButton("Cancel",null).setPositiveButton("Hide",(d,w)->{
                hiddenApps.add(id);reconcileApps();refreshScreen();
            }).show();
    }
    private void uninstallApp(String id) {
        ComponentName app=ComponentName.unflattenFromString(id);if(app==null)return;
        try {
            Intent intent=new Intent(Intent.ACTION_DELETE,
                android.net.Uri.parse("package:"+app.getPackageName()));
            startActivity(intent); // Android prompts the user before uninstalling.
        } catch(Exception error){toast("Open App info to uninstall this app");}
    }
    private void showHiddenApps() {
        ArrayList<String> ids=new ArrayList<>(hiddenApps);
        ids.removeIf(id->!installed.containsKey(id));
        ids.sort(Comparator.comparing(this::appName,String.CASE_INSENSITIVE_ORDER));
        if(ids.isEmpty()){toast("No hidden apps");return;}
        String[] names=new String[ids.size()];
        for(int i=0;i<ids.size();i++)names[i]="Show · "+appName(ids.get(i));
        new AlertDialog.Builder(this).setTitle("Hidden apps")
            .setItems(names,(d,which)->{
                String id=ids.get(which);hiddenApps.remove(id);
                reconcileApps();refreshScreen();
            }).setPositiveButton("Done",null).show();
    }

''')
block('    private void showSettings() {','    private void saveToggle(','''    private void showSettings() {
        showActionSheet("Pixel Home settings",new String[]{
            "Home screen","Dock & search","Folders","Appearance & fonts",
            "Gestures & animations","Widgets","Hidden apps","Default Home app","Reset layout"
        },i->{
            switch(i){
                case 0: showActionSheet("Home screen",new String[]{
                    "Grid · "+columns+"×"+rows,
                    "Show date · "+(showDateHeader?"On":"Off"),"Edit home screen"},j->{
                        if(j==0)showGridSettings();
                        else if(j==1)saveToggle("show_date_header",showDateHeader=!showDateHeader);
                        else changeEditing(true);
                    });break;
                case 1: showDockPreferences();break;
                case 2: showActionSheet("Folders",new String[]{
                    "Folder previews · 3×3","Spring animation · "+(folderSpring?"On":"Off")},j->{
                        if(j==1)saveToggle("folder_spring",folderSpring=!folderSpring);
                    });break;
                case 3: showActionSheet("Appearance & fonts",new String[]{
                    "Choose label font · "+labelFont+" "+labelSizeSp+" sp",
                    "Wallpaper & style","Wallpaper dim · "+wallpaperDim+"%"},j->{
                        if(j==0)showFontSettings();else if(j==1)showWallpaperPicker();
                        else showDimSetting();
                    });break;
                case 4: showActionSheet("Gestures & animations",new String[]{
                    "Swipe down search · "+(swipeDownSearch?"On":"Off"),
                    "Reduce motion · "+(reduceMotion?"On":"Off"),"Edit mode"},j->{
                        if(j==0)saveToggle("swipe_down_search",swipeDownSearch=!swipeDownSearch);
                        else if(j==1)saveToggle("reduce_motion",reduceMotion=!reduceMotion);
                        else changeEditing(true);
                    });break;
                case 5: showWidgetPicker();break;
                case 6: showHiddenApps();break;
                case 7: openHomeSettings();break;
                case 8: confirmResetLayout();break;
            }
        });
    }
    private void showDockPreferences() {
        showActionSheet("Dock & search",new String[]{
            "Dock style · "+dockStyle,"Dock icons · "+dockSlots+" (3–9)",
            "Dock folders · Drag an app onto another",
            "Search bar · "+(showSearchBar?"On":"Off"),"Search apps now"
        },index->{
            if(index==0){
                String[] styles={"Pixel","Pill","Outline"};
                new AlertDialog.Builder(this).setTitle("Dock style")
                    .setSingleChoiceItems(styles,Arrays.asList(styles).indexOf(dockStyle),
                    (d,choice)->{
                        dockStyle=styles[choice];prefs.edit().putString("dock_style",dockStyle).apply();
                        d.dismiss();refreshScreen();
                    }).show();
            }else if(index==1){
                String[] values=new String[7];
                for(int i=0;i<7;i++)values[i]=(i+3)+" icons";
                new AlertDialog.Builder(this).setTitle("Dock capacity")
                    .setSingleChoiceItems(values,dockSlots-3,(d,choice)->{
                        int count=choice+3;
                        while(dock.size()>count)moveDockItemHome(dock.get(dock.size()-1));
                        dockSlots=count;prefs.edit().putInt("dock_slots",count).apply();
                        d.dismiss();refreshScreen();
                    }).show();
            }else if(index==2)new AlertDialog.Builder(this)
                .setMessage("Drag one app onto the center of another dock icon to create a folder. Drag apps onto that folder to add more.")
                .setPositiveButton("OK",null).show();
            else if(index==3)saveToggle("show_search_bar",showSearchBar=!showSearchBar);
            else showSearch();
        });
    }

''')
replace('                    home.clear(); dock.clear();',
        '                    home.clear(); dock.clear(); dockFolders.clear();')
replace('                    for(String id:installed.keySet()) home.add(new Item(id));',
        '                    for(String id:installed.keySet()) if(!hiddenApps.contains(id)) home.add(new Item(id));')


# Export/import the whole layout and launcher settings to Android's file picker.
# This does not claim to restore widget binding tokens after an uninstall.
replace('private static final int REQUEST_CONFIG_WIDGET = 713;',
'''private static final int REQUEST_CONFIG_WIDGET = 713;
    private static final int REQUEST_EXPORT = 784, REQUEST_IMPORT = 785;''')
replace('''        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode!=REQUEST_BIND_WIDGET && requestCode!=REQUEST_CONFIG_WIDGET)return;''',
'''        super.onActivityResult(requestCode,resultCode,data);
        if(requestCode==REQUEST_EXPORT && resultCode==RESULT_OK && data!=null) {
            writeBackup(data.getData()); return;
        }
        if(requestCode==REQUEST_IMPORT && resultCode==RESULT_OK && data!=null) {
            readBackup(data.getData()); return;
        }
        if(requestCode!=REQUEST_BIND_WIDGET && requestCode!=REQUEST_CONFIG_WIDGET)return;''')

replace('"Widgets","Hidden apps","Default Home app","Reset layout"',
        '"Widgets","Hidden apps","Backup & restore","Default Home app","Reset layout"')
replace('''                case 7: openHomeSettings();break;
                case 8: confirmResetLayout();break;''',
'''                case 7: showBackupOptions();break;
                case 8: openHomeSettings();break;
                case 9: confirmResetLayout();break;''')
replace('    private void showSettings() {','''    private void showBackupOptions() {
        showActionSheet("Backup & restore",new String[]{
            "Export layout & settings","Import layout & settings","About safe upgrades"
        },i->{
            if(i==0) {
                Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                intent.putExtra(Intent.EXTRA_TITLE,"pixel-home-layout.json");
                startActivityForResult(intent,REQUEST_EXPORT);
            }else if(i==1) {
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);
                intent.addCategory(Intent.CATEGORY_OPENABLE);
                intent.setType("application/json");
                startActivityForResult(intent,REQUEST_IMPORT);
            }else new AlertDialog.Builder(this)
                .setMessage("Android retains layouts during updates only when the package name and APK signer both match. Debug APKs compiled on different machines often have different signatures. Export before uninstalling. Widgets must be re-added after a reinstall.")
                .setPositiveButton("OK",null).show();
        });
    }
    private void writeBackup(android.net.Uri uri) {
        saveLayout();
        try {
            JSONObject b=new JSONObject();
            b.put("format","pixel-home-v6");
            b.put("home",prefs.getString(KEY_HOME,"[]"));
            b.put("dock",prefs.getString(KEY_DOCK,"[]"));
            b.put("columns",columns);b.put("rows",rows);
            b.put("label_font",labelFont);b.put("label_size",labelSizeSp);
            b.put("show_search_bar",showSearchBar);
            b.put("show_date_header",showDateHeader);
            b.put("swipe_down_search",swipeDownSearch);
            b.put("folder_spring",folderSpring);
            b.put("reduce_motion",reduceMotion);
            b.put("wallpaper_dim",wallpaperDim);
            b.put("dock_slots",dockSlots);b.put("dock_style",dockStyle);
            b.put("hidden_apps",new JSONArray(hiddenApps));
            try(java.io.OutputStream out=getContentResolver().openOutputStream(uri)){
                if(out==null)throw new java.io.IOException("No output stream");
                out.write(b.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
            }
            toast("Backup saved");
        }catch(Exception ex){toast("Backup failed: "+ex.getMessage());}
    }
    private void readBackup(android.net.Uri uri) {
        try {
            java.io.ByteArrayOutputStream memory=new java.io.ByteArrayOutputStream();
            try(java.io.InputStream in=getContentResolver().openInputStream(uri)){
                if(in==null)throw new java.io.IOException("No input stream");
                byte[] buffer=new byte[4096];int n;
                while((n=in.read(buffer))!=-1){
                    if(memory.size()+n>1048576)throw new java.io.IOException("Backup too large");
                    memory.write(buffer,0,n);
                }
            }
            JSONObject b=new JSONObject(memory.toString("UTF-8"));
            if(!"pixel-home-v6".equals(b.optString("format"))){
                toast("Unsupported backup file");return;
            }
            JSONArray inputHome=new JSONArray(b.getString("home"));
            JSONArray cleanHome=new JSONArray();
            for(int i=0;i<inputHome.length();i++) {
                JSONObject item=inputHome.optJSONObject(i);
                if(item!=null&&!item.has("widget"))cleanHome.put(item);
            }
            JSONArray inputDock=new JSONArray(b.getString("dock"));
            HashSet<String> hidden=new HashSet<>();
            JSONArray h=b.optJSONArray("hidden_apps");
            if(h!=null)for(int i=0;i<h.length();i++)hidden.add(h.optString(i));
            prefs.edit()
                .putString(KEY_HOME,cleanHome.toString()).putString(KEY_DOCK,inputDock.toString())
                .putInt("columns",b.optInt("columns",4))
                .putInt("rows",b.optInt("rows",5))
                .putInt("label_size",b.optInt("label_size",15))
                .putString("label_font",b.optString("label_font","Google Sans Medium"))
                .putBoolean("show_search_bar",b.optBoolean("show_search_bar",true))
                .putBoolean("show_date_header",b.optBoolean("show_date_header",true))
                .putBoolean("swipe_down_search",b.optBoolean("swipe_down_search",true))
                .putBoolean("folder_spring",b.optBoolean("folder_spring",true))
                .putBoolean("reduce_motion",b.optBoolean("reduce_motion",false))
                .putInt("wallpaper_dim",b.optInt("wallpaper_dim",18))
                .putInt("dock_slots",b.optInt("dock_slots",5))
                .putString("dock_style",b.optString("dock_style","Pixel"))
                .putStringSet("hidden_apps",hidden).commit();
            loadPreferences();restoreLayout();currentPage=0;refreshScreen();
            toast("Layout & settings restored. Re-add widgets.");
        }catch(Exception ex){toast("Restore failed: "+ex.getMessage());}
    }

    private void showSettings() {''')

manifest=Path(sys.argv[1])/"app/src/main/AndroidManifest.xml"
manifest.write_text(manifest.read_text().replace('android:allowBackup="false"',
                                                'android:allowBackup="true"'))


p.write_text(s)
gradle=Path(sys.argv[1])/"app/build.gradle"
g=gradle.read_text().replace("versionCode 5","versionCode 6").replace("versionName '1.4'","versionName '1.6'")
gradle.write_text(g)
print("Applied v6: persisted folders, dock customization, hide/uninstall, labels, drag to folder")
