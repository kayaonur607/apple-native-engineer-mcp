#!/usr/bin/env python3
"""Evidence-based motion graphics, not an app/simulator screen recording."""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import math
import os
import subprocess
import textwrap
from PIL import Image, ImageDraw, ImageFont

W,H,FPS,DURATION=1600,900,24,64
BG='#0b1018'; PANEL='#141d2a'; WHITE='#edf3fb'; MUTED='#a2b1c6'; GREEN='#75e0bd'; RED='#ff998c'; LINE='#29374b'
@lru_cache(maxsize=80)
def font(n,bold=False,mono=False):
    key='DEMO_MONO_FONT' if mono else 'DEMO_BOLD_FONT' if bold else 'DEMO_FONT'
    fallback='/System/Library/Fonts/Menlo.ttc' if mono else '/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf'
    return ImageFont.truetype(os.environ.get(key,fallback),n)
def ease(x):
    x=max(0,min(1,x)); return 1-(1-x)**3
def text(d,x,y,s,n=25,color=WHITE,bold=False,mono=False):
    d.text((x,y),str(s),font=font(n,bold,mono),fill=color)
def wrap(d,x,y,s,width=75,n=24,color=WHITE,gap=34,limit=7):
    rows=[]
    for line in str(s).splitlines(): rows+=textwrap.wrap(line,width) or ['']
    for i,row in enumerate(rows[:limit]): text(d,x,y+i*gap,row,n,color)
def box(d,x,y,w,h): d.rounded_rectangle((int(x),int(y),int(x+w),int(y+h)),radius=22,fill=PANEL,outline=LINE,width=2)

def render(root,trace):
    out=root/'assets/demo'; events=trace['events']
    before=events[3]['response']['structuredContent']; clean=events[4]['response']['structuredContent']
    slots=events[5]['response']['structuredContent']['data']['slots']
    verified=events[6]['response']['structuredContent']['data']
    master=Image.open(root/'tests/fixtures/clean-app/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png').convert('RGB')
    icon=master.resize((88,88),Image.Resampling.LANCZOS)
    preview=[]
    proc=subprocess.Popen(['ffmpeg','-y','-hide_banner','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','fast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out/'usage-demo.mp4')],stdin=subprocess.PIPE)
    try:
        for frame in range(FPS*DURATION):
            now=frame/FPS; scene=int(now//8); t=now%8; e=events[scene]
            im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
            # Moving signal along the top rail and a continuous chapter progress bar.
            d.line((72,52,1528,52),fill=LINE,width=2)
            px=72+1456*(now/DURATION); d.ellipse((px-5,47,px+5,57),fill=GREEN)
            text(d,72,78,f'APPLE NATIVE ENGINEER / v2.2.0 / {scene+1:02d} OF 08',21,GREEN,True)
            shift=int(30*(1-ease(t/0.7)))
            text(d,72,124+shift,e['title'],48,WHITE,True)
            text(d,72,196,'Motion graphics from recorded MCP responses. Public fixtures. No audio.',23,MUTED)
            box(d,72,260,1456,500)
            text(d,104,286,f"{e['method']}  /  actual call {e['duration_ms']} ms",22,GREEN,mono=True)
            p=ease((t-.4)/1.2)
            if scene==0:
                nodes=[(130,'MCP CLIENT','Requests + tools'),(650,'LOCAL SERVER','Apple Native Engineer'),(1170,'EVIDENCE','Typed results')]
                for i,(x,title,desc) in enumerate(nodes):
                    yy=408+int(35*(1-ease((t-.3-i*.3)/.8)))
                    box(d,x,yy,300,145);text(d,x+24,yy+28,title,25,GREEN,True);text(d,x+24,yy+78,desc,20,MUTED)
                for start in [443,963]:
                    d.line((start,480,start+180,480),fill=LINE,width=3)
                    for offset in [0,.5]:
                        x=start+180*((t*.5+offset)%1); d.ellipse((x-6,474,x+6,486),fill=GREEN)
                for i,(name,count) in enumerate([('TOOLS',25),('RESOURCES',55),('PROMPTS',13)]):
                    text(d,260+i*460,620,f'{round(count*ease((t-1.2)/1.4))}',60,WHITE,True)
                    text(d,260+i*460,696,name,20,MUTED)
            elif scene==1:
                request='Review a native Apple interface'
                text(d,120,361,'prompts/get: apple-native-start',27,WHITE,mono=True)
                text(d,120,421,request[:int(len(request)*ease((t-.5)/2))],37,GREEN,True)
                items=['Understand the platform and project','Read relevant Apple HIG and API guidance','Implement with the host AI; verify with tools']
                for i,s in enumerate(items):
                    progress=ease((t-1.4-i*.6)/.7)
                    if progress>0:
                        x=120+int(45*(1-progress));text(d,x,526+i*61,f'{i+1:02d}  {s}',28,WHITE)
            elif scene==2:
                data=e['response']['structuredContent']['data']
                metrics=[('DEPLOYMENT',f"iOS {data['deployment_targets']['iOS']}"),('SWIFT',data['swift_versions'][0]),('SOURCE FILES',str(data['swift_files']))]
                for i,(title,value) in enumerate(metrics):
                    y=390+int(65*(1-ease((t-.5-i*.25)/.8)))
                    box(d,120+i*470,y,425,190);text(d,147+i*470,y+28,title,21,MUTED);text(d,147+i*470,y+81,value,58,WHITE,True)
                text(d,120,636,'Inspect first. Advice must match the real deployment target.',30,GREEN,True)
                text(d,120,692,'Fixture: tests/fixtures/legacy-app',22,MUTED,mono=True)
            elif scene==3:
                text(d,120,363,before['data']['violations'],110,RED,True)
                text(d,120,493,'recorded violations',26,MUTED)
                text(d,120,549,'7 Swift files',25,WHITE)
                for i,f in enumerate(before['findings'][:3]):
                    q=ease((t-.5-i*.55)/.65);x=565+int(75*(1-q));y=357+i*119
                    if q>0:
                        box(d,x,y,905,104);text(d,x+22,y+15,f"{f['code']} / {f['severity'].upper()}",20,RED,mono=True)
                        wrap(d,x+22,y+47,f['message'],width=69,n=23,gap=28,limit=2)
            elif scene==4:
                for i,(title,r,col) in enumerate([('LEGACY FIXTURE',before,RED),('CLEAN REFERENCE',clean,GREEN)]):
                    x=120+i*700;yy=350+int(45*(1-ease((t-.4-i*.4)/1)))
                    box(d,x,yy,650,345);text(d,x+28,yy+30,title,24,col,True)
                    text(d,x+28,yy+85,r['data']['violations'],110,col,True)
                    text(d,x+28,yy+222,'SwiftUI violations',27,MUTED)
                    text(d,x+28,yy+279,f"{r['data']['scanned_files']} files / {r['status'].upper()}",23,WHITE,mono=True)
                text(d,120,716,'Separate reference implementations; no automatic source rewrite.',22,MUTED)
            elif scene==5:
                im.paste(master.resize((200,200)),(130,397))
                text(d,130,627,'1024 x 1024',25,WHITE,True)
                text(d,130,671,'SUPPLIED MASTER',19,MUTED)
                d.line((380,500,485,500),fill=GREEN,width=3)
                for i in range(slots):
                    q=ease((t-.7-i*.10)/1.25)
                    if q<=0:continue
                    tx=540+(i%6)*151;ty=355+(i//6)*120
                    x=230+(tx-230)*q;y=465+(ty-465)*q
                    size=max(2,int(35+53*q));im.paste(icon.resize((size,size)),(int(x),int(y)))
                if t>3: text(d,540,712,f'{slots} PNG slots + Contents.json',27,GREEN,True)
            elif scene==6:
                for i,(value,title) in enumerate([(verified['slots'],'VERIFIED SLOTS'),(verified['missing'],'MISSING FILES'),(verified['wrong_size'],'WRONG SIZE')]):
                    q=ease((t-.4-i*.4)/.8);yy=374+int(45*(1-q))
                    box(d,120+i*470,yy,425,257);text(d,150+i*470,yy+35,value,95,GREEN,True);text(d,150+i*470,yy+176,title,22,MUTED)
                text(d,120,681,'Verification is a separate tool call against the generated files.',26,WHITE)
                # A visible sweep records the validation progression as an illustration.
                if t<4:d.line((120+1350*p,350,120+1350*p,651),fill=GREEN,width=2)
            else:
                info=json.loads(e['response']['contents'][0]['text'])
                text(d,120,357,'INSTALLED VERSION',23,MUTED)
                text(d,120,406,f"v{info['version']}",103,GREEN,True)
                items=['GitHub Releases deliver stable versions','Stage and smoke-test before activation','Reconnect to load an update; pin to stay fixed']
                for i,s in enumerate(items):
                    q=ease((t-.8-i*.5)/.8)
                    if q>0:text(d,670+int(35*(1-q)),390+i*83,s,26,WHITE)
                text(d,120,671,'Read apple-native://release in your MCP client.',29,WHITE,True)
                text(d,120,718,'Explore the tools. Inspect the raw session. Reproduce the results.',22,MUTED)
            d.rounded_rectangle((72,802,1528,808),radius=3,fill=LINE)
            if now>0:d.rounded_rectangle((72,802,72+1456*now/DURATION,808),radius=3,fill=GREEN)
            text(d,72,831,'ANIMATED EVIDENCE / Edited timing / Not a desktop, AI-chat or simulator recording',19,MUTED)
            text(d,72,864,f"Source: session.json / {trace['recorded_at']} / {int(now)//60:02d}:{int(now)%60:02d}",16,MUTED,mono=True)
            # Smooth dip-through-background scene transitions, no abrupt slide cuts.
            fade=min(1,t/.3,(8-t)/.3)
            if fade<1:im=Image.blend(Image.new('RGB',(W,H),BG),im,max(0,fade))
            if frame==FPS*4:im.save(out/'video-poster.png')
            if frame%12==0:preview.append(im.resize((640,360)).quantize(colors=64))
            proc.stdin.write(im.tobytes())
            if frame%(FPS*8)==0:print(f'Animating chapter {scene+1}/8',flush=True)
    finally:proc.stdin.close()
    if proc.wait()!=0:raise RuntimeError('Video encoding failed')
    preview[0].save(out/'usage-preview.gif',save_all=True,append_images=preview[1:],duration=500,loop=0,optimize=True)
    (out/'usage-demo.vtt').write_text('WEBVTT\n\n'+''.join(f"00:{i*8//60:02d}:{i*8%60:02d}.000 --> 00:{(i+1)*8//60:02d}:{(i+1)*8%60:02d}.000\n{e['title']}\n\n" for i,e in enumerate(events)))
    checks=[]
    for name in ['session.json','audit-comparison.png','icon-pipeline.png','video-poster.png','usage-preview.gif','usage-demo.mp4','usage-demo.vtt']:
        checks.append(f"{hashlib.sha256((out/name).read_bytes()).hexdigest()}  {name}")
    (out/'SHA256SUMS').write_text('\n'.join(checks)+'\n')
    print('Encoded 64-second animated 1600x900 / 24fps evidence walkthrough.',flush=True)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    render(root,json.loads((root/'assets/demo/session.json').read_text()))
