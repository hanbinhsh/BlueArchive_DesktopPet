import test from 'node:test';
import assert from 'node:assert/strict';
import { Group, Mesh, BoxGeometry, MeshBasicMaterial, Bone, SkinnedMesh, Skeleton, BufferGeometry, Float32BufferAttribute, Uint16BufferAttribute } from 'three';
import { visiblePoseBounds } from '../src/framing';

test('furniture framing excludes collapsed offstage weapons and hidden descendants of a visible mesh', () => {
  const root = new Group();
  const furniture = new Mesh(new BoxGeometry(2, 2, 2), new MeshBasicMaterial());
  root.add(furniture);
  const hidden = new Mesh(new BoxGeometry(10, 10, 10));
  hidden.visible = false; hidden.position.z = 30; furniture.add(hidden);
  const weapon = new Mesh(new BoxGeometry(1, 1, 1));
  weapon.scale.setScalar(.0008); weapon.position.z = -17; root.add(weapon);
  assert.deepEqual(visiblePoseBounds(root, .003).min.toArray(), [-1, -1, -1]);
  assert.deepEqual(visiblePoseBounds(root, .003).max.toArray(), [1, 1, 1]);
  weapon.scale.setScalar(1); weapon.position.z = -2;
  assert.equal(visiblePoseBounds(root, .003).min.z, -2.5);
});

test('collapsed rigid parts inside the same skinned renderer do not expand furniture framing', () => {
  const root = new Group(), a = new Bone(), b = new Bone(); root.add(a, b);
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([-1,-1,0, 1,-1,0, 0,1,0, -1,-1,0, 1,-1,0, 0,1,0], 3));
  geometry.setAttribute('skinIndex', new Uint16BufferAttribute([0,0,0,0, 0,0,0,0, 0,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0], 4));
  geometry.setAttribute('skinWeight', new Float32BufferAttribute(Array(6).fill([1,0,0,0]).flat(), 4));
  const mesh = new SkinnedMesh(geometry); root.add(mesh); mesh.bind(new Skeleton([a,b]));
  b.position.x = 100; b.scale.setScalar(.0001);
  assert.deepEqual(visiblePoseBounds(root, .003).max.toArray(), [1, 1, 0]);
  b.position.x = 2; b.scale.setScalar(1);
  assert.equal(visiblePoseBounds(root, .003).max.x, 3);
});

test('runtime framing can measure final prop matrices without replacing them with local TRS', () => {
  const root = new Group(), mesh = new Mesh(new BoxGeometry(2,2,2)); root.add(mesh);root.updateMatrixWorld(true);
  mesh.matrixWorld.makeTranslation(3,0,0);
  const before=mesh.matrixWorld.toArray();
  assert.equal(visiblePoseBounds(root,.003,false).max.x,4);
  assert.deepEqual(mesh.matrixWorld.toArray(),before);
  assert.equal(visiblePoseBounds(root,.003).max.x,1);
});
