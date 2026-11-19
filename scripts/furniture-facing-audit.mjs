// Compare the current student's head direction with the ordinary idle pose.
// Candidate angles require visual review: lying poses and occlusion need judgement.
import {readFileSync,readdirSync,writeFileSync} from 'node:fs';
import * as T from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
const loader=new GLTFLoader();loader.register(()=>({name:'audit-textures',loadTexture:async()=>new T.Texture()}));
async function load(file){const b=readFileSync(file);return loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');}
const root=process.env.BA_CHARACTERS||'characters',rows=[];
for(const dir of readdirSync(root,{withFileTypes:true}).filter(d=>d.isDirectory())){
 const c=JSON.parse(readFileSync(`${root}/${dir.name}/character.json`));if(!c.furniture?.length)continue;
 const base=await load(`${root}/${dir.name}/${c.model}`),head=base.scene.getObjectByName('Bip001_Head')||base.scene.getObjectByName('Bip001 Head');
 if(!head){console.log('NO HEAD',dir.name);continue;}
 const mix=new T.AnimationMixer(base.scene);mix.clipAction(T.AnimationClip.findByName(base.animations,c.animations.idle)).play();mix.setTime(.1);base.scene.updateMatrixWorld(true);
 const forward=new T.Vector3(0,0,1).transformDirection(head.matrixWorld.clone().invert());
 for(const f of c.furniture){const g=await load(`${root}/${dir.name}/${f.model}`),h=g.scene.getObjectByName(head.name);if(!h)continue;
 const m=new T.AnimationMixer(g.scene);m.clipAction(T.AnimationClip.findByName(g.animations,f.clip)).play();const samples=[];
 for(const fraction of [.1,.3,.5,.7,.9]){m.setTime(f.duration*fraction);g.scene.updateMatrixWorld(true);samples.push(forward.clone().transformDirection(h.matrixWorld).toArray());}
 const avg=new T.Vector3();for(const s of samples)avg.add(new T.Vector3(...s));avg.multiplyScalar(1/samples.length);
 const faceYaw=-Math.atan2(avg.x,avg.z),current=f.yaw??Math.PI*.75;
 const wrap=v=>Math.atan2(Math.sin(v),Math.cos(v));const choices=[faceYaw+Math.PI/6,faceYaw-Math.PI/6];const candidate=choices.sort((a,b)=>Math.abs(wrap(a-current))-Math.abs(wrap(b-current)))[0];
 rows.push({character:dir.name,id:f.id,name:f.name,current:current/Math.PI,front:faceYaw/Math.PI,candidate:candidate/Math.PI,vertical:avg.y,confidence:Math.hypot(avg.x,avg.z),currentFacing:-avg.x*Math.sin(current)+avg.z*Math.cos(current),samples});
 m.stopAllAction();g.scene.traverse(o=>{if(o.isMesh){o.geometry.dispose();for(const mat of Array.isArray(o.material)?o.material:[o.material])mat.dispose();}});
 }mix.stopAllAction();console.log(dir.name);
}
writeFileSync('test-results/furniture-facing-1029.json',JSON.stringify(rows,null,2));
