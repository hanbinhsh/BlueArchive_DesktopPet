import { readFileSync, readdirSync, writeFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { PropTransitions } from '../src/prop-transitions';

// Geometry/animation audit: textures are irrelevant to skin matrix evaluation.
const loader = new GLTFLoader();
loader.register(() => ({ name: 'audit-textures', loadTexture: async () => new THREE.Texture() }));
const report = [];
for (const character of readdirSync('characters', {withFileTypes:true}).filter(d=>d.isDirectory()).map(d=>d.name)) {
  const manifest = JSON.parse(readFileSync(`characters/${character}/character.json`, 'utf8'));
  const bytes = readFileSync(`characters/${character}/${manifest.model}`);
  const gltf = await loader.parseAsync(bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength), '');
  const parent = new THREE.Group(); parent.add(gltf.scene);
  const props = new PropTransitions(gltf.scene), mixer = new THREE.AnimationMixer(gltf.scene);
  const allBones: THREE.Bone[] = []; gltf.scene.traverse(o=>{if((o as THREE.Bone).isBone)allBones.push(o as THREE.Bone);});
  const selected = new Set(props.bones), unhandled: Record<string,number> = {};
  const clips = (manifest.actions || []).map((a: {clip:string}) => THREE.AnimationClip.findByName(gltf.animations,a.clip)!);
  if (!clips.length) clips.push(...gltf.animations);
  const idle = THREE.AnimationClip.findByName(gltf.animations,manifest.animations.idle)!;
  let cases = 0, worstBefore = 1, worstAfter = 1;
  const affected = new Set<string>();
  const scales = () => allBones.map(bone => [0,1,2].map(i => new THREE.Vector3().setFromMatrixColumn(bone.matrixWorld,i).length()));
  function pose(clip: THREE.AnimationClip, time: number) {
    mixer.stopAllAction(); const action = mixer.clipAction(clip).reset().setLoop(THREE.LoopOnce,1);
    action.clampWhenFinished = true; action.play(); mixer.update(time); parent.updateMatrixWorld(true); return action;
  }
  for (const other of clips.filter((c: THREE.AnimationClip) => c !== idle)) {
    for (const [from,to] of [[idle,other],[other,idle]]) {
      for (const phase of [0,.5,.99]) {
        const time = from.duration * phase;
        const endpoints = [];
        for (let frame=1;frame<=6;frame++) {pose(to,frame*.03);endpoints.push(scales());}
        const source = pose(from,time), start = scales();
        props.begin(to,.18);
        const target = mixer.clipAction(to).reset().setLoop(THREE.LoopOnce,1).play();
        target.clampWhenFinished=true; source.crossFadeTo(target,.18,false);
        for (let frame=0;frame<6;frame++) {
          mixer.update(.03); parent.updateMatrixWorld(true);
          const before = scales(); props.update(target.time,.03); const after = scales();
          for(let i=0;i<allBones.length;i++)for(let axis=0;axis<3;axis++) {
            const bound = Math.max(start[i][axis],endpoints[frame][i][axis],1e-6);
            const oldRatio=before[i][axis]/bound, ratio=after[i][axis]/bound;
            if(!selected.has(allBones[i])) { if(oldRatio>1.1)unhandled[allBones[i].name]=Math.max(unhandled[allBones[i].name]||0,oldRatio);continue; }
            worstBefore=Math.max(worstBefore,oldRatio);worstAfter=Math.max(worstAfter,ratio);
            if(oldRatio>1.1)affected.add(allBones[i].name);
            assert.ok(Number.isFinite(ratio)&&ratio<1.0001,`${character}: ${allBones[i].name} exceeds endpoint size (${ratio})`);
          }
        }
        cases++;
      }
    }
  }
  report.push({character,meshes:props.meshes,bones:props.bones.length,cases,worstBefore,worstAfter,affected:[...affected],unhandled});
  console.log(character,cases,'transitions; old/new maximum scale ratio:',worstBefore.toFixed(2),worstAfter.toFixed(2));
}
writeFileSync('test-results/prop-transitions.json',JSON.stringify(report,null,2));
