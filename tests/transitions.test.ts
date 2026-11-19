import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { PropTransitions } from '../src/prop-transitions';

test('prop transitions do not multiply reciprocal parent and child scales during a body crossfade', () => {
  const parent = new THREE.Group(), root = new THREE.Group(); parent.add(root);
  const acc = new THREE.Bone(), chair = new THREE.Bone(), head = new THREE.Bone();
  acc.name = 'bone_accroot'; chair.name = 'bone_chair'; head.name = 'Bip001 Head';
  root.add(acc, head); acc.add(chair);
  const mesh = new THREE.SkinnedMesh(); mesh.name = 'chair'; mesh.bind(new THREE.Skeleton([chair])); root.add(mesh);
  const body = new THREE.SkinnedMesh(); body.name = 'body'; body.bind(new THREE.Skeleton([head])); root.add(body);
  const clip = (name: string, a: number, b: number) => new THREE.AnimationClip(name, 1, [
    new THREE.VectorKeyframeTrack('bone_accroot.scale', [0, 1], [a,a,a,a,a,a]),
    new THREE.VectorKeyframeTrack('bone_chair.scale', [0, 1], [b,b,b,b,b,b]),
  ]);
  const idle = clip('idle', 1, 1), pickup = clip('pickup', .001, 1000);
  const props = new PropTransitions(root), mixer = new THREE.AnimationMixer(root);
  assert.deepEqual(props.meshes, ['chair']); assert.deepEqual(props.bones, [chair]);
  const a = mixer.clipAction(idle).play(); mixer.update(0); parent.updateMatrixWorld(true);
  props.begin(pickup, .18);
  const b = mixer.clipAction(pickup).play(); a.crossFadeTo(b, .18, false);
  mixer.update(.09); parent.updateMatrixWorld(true);
  assert.ok(chair.matrixWorld.elements[0] > 200, 'reproduce the original huge intermediate prop');
  const bodyBefore = head.matrixWorld.clone();
  props.update(b.time, .09);
  assert.ok(Math.abs(chair.matrixWorld.elements[0] - 1) < 1e-5);
  assert.deepEqual(head.matrixWorld.elements, bodyBefore.elements);
  mixer.update(.09); parent.updateMatrixWorld(true); props.update(b.time, .09);
  assert.ok(Math.abs(chair.matrixWorld.elements[0] - 1) < 1e-5);
  // Returning from pickup must be protected too.
  props.begin(idle, .18); b.crossFadeTo(a.reset().play(), .18, false);
  mixer.update(.09); parent.updateMatrixWorld(true); props.update(a.time, .09);
  assert.ok(Math.abs(chair.matrixWorld.elements[0] - 1) < 1e-5);
});
