#!/usr/bin/env node
// Install locked dependencies and print an absolute-path config; never edit a client config.
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));
if(Number(process.versions.node.split('.')[0])<20)throw new Error('Node 20+ is required');
for(const [command,args,cwd] of [['git',['--version'],root],['python3',['--version'],root],
 [process.platform==='win32'?'npm.cmd':'npm',['ci','--ignore-scripts','--no-audit','--no-fund'],root+'integrations/mcp-server']]){
 const result=spawnSync(command,args,{cwd,stdio:['inherit',2,2]});
 if(result.error||result.status!==0)throw new Error(`Setup failed: ${command}`);
}
console.log(JSON.stringify({mcpServers:{'apple-native-engineer':{command:process.execPath,args:[root+'integrations/mcp-server/scripts/github-launcher.mjs'],env:{APPLE_NATIVE_PYTHON:'python3'}}}},null,2));
