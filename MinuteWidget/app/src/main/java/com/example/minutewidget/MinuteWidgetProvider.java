package com.example.minutewidget;
import android.app.PendingIntent;
import android.appwidget.AppWidgetManager;
import android.appwidget.AppWidgetProvider;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.SystemClock;
import android.widget.RemoteViews;
import java.util.Locale;
public class MinuteWidgetProvider extends AppWidgetProvider {
 static final String P="timer", E="end", A="ADD", R="RESET";
 public void onReceive(Context c, Intent i){ super.onReceive(c,i); SharedPreferences p=c.getSharedPreferences(P,0); long n=SystemClock.elapsedRealtime(); if(A.equals(i.getAction()))p.edit().putLong(E,Math.max(n,p.getLong(E,0))+60000).apply(); else if(R.equals(i.getAction()))p.edit().putLong(E,0).apply(); update(c); }
 public void onUpdate(Context c,AppWidgetManager m,int[] ids){update(c);}
 static PendingIntent pi(Context c,String a,int n){return PendingIntent.getBroadcast(c,n,new Intent(c,MinuteWidgetProvider.class).setAction(a),PendingIntent.FLAG_UPDATE_CURRENT|PendingIntent.FLAG_IMMUTABLE);}
 static void update(Context c){AppWidgetManager m=AppWidgetManager.getInstance(c); SharedPreferences p=c.getSharedPreferences(P,0); long e=p.getLong(E,0),r=Math.max(0,e-SystemClock.elapsedRealtime()),s=(r+999)/1000; for(int id:m.getAppWidgetIds(new ComponentName(c,MinuteWidgetProvider.class))){RemoteViews v=new RemoteViews(c.getPackageName(),com.example.minutewidget.R.layout.minute_widget);v.setTextViewText(R.id.timer,String.format(Locale.getDefault(),"%02d:%02d",s/60,s%60));v.setOnClickPendingIntent(R.id.add_minute,pi(c,A,1));v.setOnClickPendingIntent(R.id.reset,pi(c,R,2));m.updateAppWidget(id,v);} if(r>0)new android.os.Handler(c.getMainLooper()).postDelayed(()->update(c),1000);}
}
