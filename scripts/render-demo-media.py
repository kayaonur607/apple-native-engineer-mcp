#!/usr/bin/env python3
"""Render actual recorded MCP responses into README evidence and a captioned video.
Requires Pillow and ffmpeg for media authoring only, never for MCP runtime.
"""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/demo'
TRACE = json.loads((OUT / 'session.json').read_text())
EVENTS = TRACE['events']
BG, PANEL, TEXT, MUTED, GREEN, RED, LINE = '#0b1018', '#141d2a', '#edf3fb', '#a2b1c6', '#75e0bd', '#ff998c', '#29374b'
FONT = os.environ.get('DEMO_FONT', '/System/Library/Fonts/Supplemental/Arial.ttf')
BOLD = os.environ.get('DEMO_BOLD_FONT', '/System/Library/Fonts/Supplemental/Arial Bold.ttf')
MONO = os.environ.get('DEMO_MONO_FONT', '/System/Library/Fonts/Menlo.ttc')
def font(n, bold=False, mono=False):
    return ImageFont.truetype(MONO if mono else BOLD if bold else FONT, n)
def canvas():
    im = Image.new('RGB', (1600, 1000), BG)
    return im, ImageDraw.Draw(im)
def label(d, xy, text, size=24, fill=TEXT, bold=False, mono=False):
    d.text(xy, text, fill=fill, font=font(size, bold, mono))
def lines(d, text, x, y, width=83, size=23, fill=TEXT, gap=34, mono=False, max_lines=15):
    wrapped = []
    for line in text.splitlines():
        wrapped += textwrap.wrap(line, width=width, replace_whitespace=False) or ['']
    for i, line in enumerate(wrapped[:max_lines]): label(d, (x, y+i*gap), line, size, fill, mono=mono)
def base(kicker, title, subtitle):
    im,d=canvas()
    label(d,(72,58),kicker,22,GREEN,bold=True)
    label(d,(72,105),title,54,bold=True)
    label(d,(72,183),subtitle,24,MUTED)
    return im,d
def footer(d, extra='Rendered from session.json. Public fixtures; no customer code.'):
    label(d,(72,914),extra,21,MUTED)
    label(d,(72,950),f"RECORDED {TRACE['recorded_at']}  |  APPLE NATIVE ENGINEER v2.2.0",17,MUTED,mono=True)

before = EVENTS[3]['response']['structuredContent']
after = EVENTS[4]['response']['structuredContent']
im,d=base('EVIDENCE 01 / STATIC REVIEW','From source code to actionable findings','Two real fixture audits. The session does not rewrite the app automatically.')
for x,title,r,color in [(72,'LEGACY FIXTURE',before,RED),(824,'CLEAN REFERENCE',after,GREEN)]:
    d.rounded_rectangle((x,255,x+704,875),radius=22,fill=PANEL,outline=LINE,width=2)
    label(d,(x+32,285),title,23,color,bold=True)
    label(d,(x+32,335),str(r['data']['violations']),102,color,bold=True)
    label(d,(x+32,460),'SwiftUI violations',26,MUTED)
    label(d,(x+32,515),f"{r['data']['scanned_files']} Swift files  /  status: {r['status']}",22,mono=True)
    y=584
    if r['status']=='fail':
        for f in r['findings'][:3]:
            label(d,(x+32,y),f"{f['code']}  {f['severity'].upper()}",22,color,mono=True)
            lines(d,f['message'],x+32,y+34,width=43,size=21,gap=28,max_lines=2)
            y+=90
    else:
        lines(d,'0 lint violations.\n1 informational finding retained.\n\nNot proof of runtime accessibility\nor App Store approval.',x+32,y,width=44,size=22,gap=34)
footer(d)
im.save(OUT/'audit-comparison.png')

prepared=EVENTS[5]['response']['structuredContent']
verified=EVENTS[6]['response']['structuredContent']
im,d=base('EVIDENCE 02 / ASSET PRODUCTION','One master. Eighteen Xcode icon slots.','Actual generated files, then a separate verification call. No AI-generated artwork.')
d.rounded_rectangle((72,255,455,875),radius=22,fill=PANEL,outline=LINE,width=2)
master=Image.open(ROOT/'tests/fixtures/clean-app/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png').convert('RGB')
im.paste(master.resize((260,260)),(132,313))
label(d,(110,620),'1024 x 1024 PNG',27,bold=True)
label(d,(110,665),'Opaque fixture master',22,MUTED)
label(d,(110,718),'prepare_icon_assets',22,GREEN,mono=True)
label(d,(110,760),'verify_icon_set',22,GREEN,mono=True)
for i,name in enumerate(prepared['data']['files']):
    x=510+(i%6)*170; y=280+(i//6)*165
    icon=Image.open(ROOT/'.swiftwork/video-demo/AppIcon.appiconset'/name).convert('RGB')
    im.paste(icon.resize((95,95)),(x,y))
    label(d,(x,y+109),f'{icon.width} x {icon.height}',17,MUTED,mono=True)
label(d,(510,820),f"{verified['data']['slots']} verified   /   {verified['data']['missing']} missing   /   {verified['data']['wrong_size']} wrong size",24,GREEN,mono=True)
footer(d)
im.save(OUT/'icon-pipeline.png')

# Animated video/GIF share the same evidence; static cards above remain reproducible.
import importlib.util
spec = importlib.util.spec_from_file_location("animate_demo", ROOT / "scripts/animate-demo.py")
animation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(animation)
animation.render(ROOT, TRACE)
