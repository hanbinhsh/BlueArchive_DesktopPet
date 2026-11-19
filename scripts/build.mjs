import { build } from 'esbuild';
import { mkdir, copyFile } from 'node:fs/promises';
await mkdir('dist', { recursive: true });
await build({ entryPoints: ['src/main.ts'], outfile: 'dist/main.cjs', bundle: true, platform: 'node', external: ['electron'], format: 'cjs' });
await build({ entryPoints: ['src/preload.ts'], outfile: 'dist/preload.cjs', bundle: true, platform: 'node', external: ['electron'], format: 'cjs' });
await build({ entryPoints: ['src/renderer.ts'], outfile: 'dist/renderer.js', bundle: true, platform: 'browser', format: 'esm' });
await copyFile('src/index.html', 'dist/index.html');

await build({ entryPoints: ["src/panel-preload.ts"], outfile: "dist/panel-preload.cjs", bundle: true, platform: "node", external: ["electron"], format: "cjs" });
await build({ entryPoints: ["src/panel.ts"], outfile: "dist/panel.js", bundle: true, platform: "browser", format: "esm" });
await copyFile("src/panel.html", "dist/panel.html");
await copyFile('src/panel.css','dist/panel.css');
await build({entryPoints:['src/range-preload.ts'],outfile:'dist/range-preload.cjs',bundle:true,platform:'node',external:['electron'],format:'cjs'});
await build({entryPoints:['src/range.ts'],outfile:'dist/range.js',bundle:true,platform:'browser',format:'iife'});
await copyFile('src/range.html','dist/range.html');

// Build the small Windows wheel forwarding bridge; no Node runtime is needed by users.
const {execFile}=await import('node:child_process');
const {promisify}=await import('node:util');
const path=(await import('node:path')).default;
await mkdir('native/bin',{recursive:true});
await promisify(execFile)(path.join(process.env.WINDIR||'C:/Windows','Microsoft.NET/Framework64/v4.0.30319/csc.exe'),['/nologo','/target:exe','/platform:x64','/optimize+','/out:'+path.resolve('native/bin/wheel-forwarder.exe'),path.resolve('native/WindowWheel.cs')]);

await build({entryPoints:["src/menu-preload.ts"],outfile:"dist/menu-preload.cjs",bundle:true,platform:"node",external:["electron"],format:"cjs"});
await build({entryPoints:["src/menu.ts"],outfile:"dist/menu.js",bundle:true,platform:"browser",format:"esm"});
for(const name of ["menu.html","menu.css"])await copyFile("src/"+name,"dist/"+name);
