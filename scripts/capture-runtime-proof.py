#!/usr/bin/env python3
"""Compile a controlled SwiftUI app and capture actual simulator appearances."""
import json, plistlib, subprocess, pathlib, datetime, time
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'assets/runtime-proof';out.mkdir(exist_ok=True)
app=root/'.swiftwork/RuntimeProof.app';app.mkdir(parents=True,exist_ok=True)
commands=[]
def run(*args):
    commands.append(list(args))
    return subprocess.check_output(args,stderr=subprocess.STDOUT,text=True)
sdk=run('xcrun','--sdk','iphonesimulator','--show-sdk-path').strip()
devices=json.loads(run('xcrun','simctl','list','devices','available','--json'))['devices']
device=next(d for group in devices.values() for d in group if d['name'].startswith('iPhone'))
if device['state']!='Booted':run('xcrun','simctl','boot',device['udid'])
run('xcrun','simctl','bootstatus',device['udid'],'-b')
run('xcrun','swiftc','-parse-as-library','-sdk',sdk,'-target','arm64-apple-ios17.0-simulator',str(root/'examples/runtime-proof/ProofApp.swift'),'-o',str(app/'RuntimeProof'))
with (app/'Info.plist').open('wb') as f:plistlib.dump({'CFBundleIdentifier':'dev.applenative.runtimeproof','CFBundleExecutable':'RuntimeProof','CFBundleName':'RuntimeProof','CFBundlePackageType':'APPL','CFBundleVersion':'1','CFBundleShortVersionString':'1.0','MinimumOSVersion':'17.0','UILaunchScreen':{}},f)
run('xcrun','simctl','install',device['udid'],str(app))
run('xcrun','simctl','launch',device['udid'],'dev.applenative.runtimeproof')
for style in ['light','dark']:
    run('xcrun','simctl','ui',device['udid'],'appearance',style)
    time.sleep(3)
    run('xcrun','simctl','io',device['udid'],'screenshot',str(out/f'{style}.png'))
run('xcrun','simctl','ui',device['udid'],'appearance','light')
record={'recorded_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'device':device['name'],'sdk':pathlib.Path(sdk).name,'commands':commands,'scope':'Controlled app compiled, installed, launched and captured in light/dark. No interaction, VoiceOver, RTL or AX-size certification.'}
(out/'evidence.json').write_text(json.dumps(record,indent=2).replace(str(root),'<repository>').replace(sdk,'<simulator-sdk>')+'\n')
print(record['scope'])
