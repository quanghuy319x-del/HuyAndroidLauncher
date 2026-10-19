#!/usr/bin/env python3
"""Make Pixel Home v6 install alongside older builds without deleting their data."""
from pathlib import Path
import sys
project=Path(sys.argv[1])
gradle=project/"app/build.gradle"
text=gradle.read_text()
old="applicationId 'dev.glasshome.launcher'"
new="applicationId 'dev.glasshome.pixelhome6'"
if old not in text:
    raise SystemExit(f"Missing original package id {old!r}")
gradle.write_text(text.replace(old,new,1))
manifest=project/"app/src/main/AndroidManifest.xml"
xml=manifest.read_text()
xml=xml.replace('android:label="Pixel Home"','android:label="Pixel Home v6"',1)
manifest.write_text(xml)
print("Side-by-side package: dev.glasshome.pixelhome6")
