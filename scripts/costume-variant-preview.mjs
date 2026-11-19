// Standalone visual audit: also accepts scenario assets with only one clip.
// It never loads user settings or relaxes production character validation.
import { build } from 'esbuild';
import { _electron as electron } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync, readdirSync } from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const dir = path.resolve('test-results/costume-viewer');
mkdirSync(dir, { recursive: true });
await build({
  stdin: { resolveDir: process.cwd(), contents: `
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const renderer = new THREE.WebGLRenderer({antialias:true, preserveDrawingBuffer:true});
renderer.setSize(600,650); renderer.setClearColor(0x344252);
document.body.append(renderer.domElement);
window.auditLoad = async (url, label, clipName, yaw = 0) => {
 const gltf = await new GLTFLoader().loadAsync(url);
 const scene = new THREE.Scene(); scene.add(gltf.scene);
 const json = gltf.parser.json, visibility = json.scenes?.[0]?.extras?.BA_pet_visibility;
 const clip = clipName ? THREE.AnimationClip.findByName(gltf.animations,clipName) : gltf.animations[0];
 const mixer = new THREE.AnimationMixer(gltf.scene);
 if (clip) { mixer.clipAction(clip).play(); mixer.update(.4); }
 const values = {...visibility?.defaults};
 for (const track of visibility?.clips?.[clip?.name] || []) {
   for (const [time, value] of track.keys) if (time <= .4) values[track.node] = value;
 }
 for (const [index, value] of Object.entries(values)) (await gltf.parser.getDependency('node', +index)).visible = value;
 gltf.scene.rotation.y = yaw; gltf.scene.updateMatrixWorld(true);
 let meshes=0;
 const box = new THREE.Box3();
 gltf.scene.traverseVisible(o => {if(o.isMesh) {o.frustumCulled=false; box.union(new THREE.Box3().setFromObject(o, true)); meshes++;}});
 const center=box.getCenter(new THREE.Vector3()), size=box.getSize(new THREE.Vector3());
 const camera=new THREE.PerspectiveCamera(30,600/650,.001,1000);
 const distance=Math.max(size.y,size.x*650/600)*2.1;
 camera.position.set(center.x,center.y+size.y*.04,center.z+distance);
 camera.lookAt(center);
 scene.add(new THREE.HemisphereLight(0xffffff,0xddeeff,2.4));
 renderer.render(scene,camera);
 document.querySelector('#caption').textContent=label;
 const result={meshes,clip:clip?.name || null, height:size.y,width:size.x};
 if(!meshes || !Number.isFinite(size.y) || size.y<=0) throw Error('No visible geometry');
 mixer.stopAllAction(); mixer.uncacheRoot(gltf.scene);
 gltf.scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();for(const m of [].concat(o.material)){for(const v of Object.values(m))if(v?.isTexture)v.dispose();m.dispose();}}});
 return result;
};
`},
  bundle: true, outfile: path.join(dir, 'viewer.js'), platform: 'browser',
});
writeFileSync(path.join(dir, 'viewer.html'), '<html><meta charset="utf-8"><style>body{margin:0;background:#344252;color:white;font:15px sans-serif}#caption{height:40px;padding:10px;box-sizing:border-box}</style><div id="caption"></div><script src="viewer.js"></script></html>');
writeFileSync(path.join(dir, 'main.cjs'), `const{app,BrowserWindow}=require('electron');app.whenReady().then(()=>{const w=new BrowserWindow({width:600,height:690,useContentSize:true,show:false,webPreferences:{backgroundThrottling:false}});w.loadFile(${JSON.stringify(path.join(dir,'viewer.html'))});});`);
const env = { ...process.env }; delete env.ELECTRON_RUN_AS_NODE;
const app = await electron.launch({args:[path.join(dir,'main.cjs')],env});
const results=[];
try {
  const page=await app.firstWindow();
  await page.waitForFunction(()=>typeof window.auditLoad==='function');
  const root=path.resolve('.assets/costume-variant-preview');
  const entries = process.argv.slice(2).length ? process.argv.slice(2) : readdirSync(root);
  for(const id of entries) {
    const folder = id.startsWith('audit_') ? path.join(root,id) : path.resolve('characters',id);
    const manifest=JSON.parse(readFileSync(path.join(folder,'character.json'),'utf8'));
    const result=await page.evaluate(async ({url,label,clip})=>window.auditLoad(url,label,clip),{
      url:pathToFileURL(path.resolve(folder,manifest.model)).href,label:manifest.name,clip:manifest.animations?.idle});
    const screenshot=`test-results/costume-${id}.png`;
    await page.screenshot({path:screenshot});
    results.push({id,...result,screenshot});
  }
} finally {await app.close();}
writeFileSync('test-results/costume-variant-render.json',JSON.stringify(results,null,2));
console.log(JSON.stringify(results,null,2));

