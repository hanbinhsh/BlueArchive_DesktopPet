import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { PlanarMirror, reflectPointAcrossPlane, reflectDirectionAcrossPlane } from '../src/mirror-surface';

test('reflectPointAcrossPlane and reflectDirectionAcrossPlane mirror across arbitrary tilted plane', () => {
  const n = new THREE.Vector3(1, 0, 1).normalize();
  const p = new THREE.Vector3(2, 0, 0);
  const pt = new THREE.Vector3(4, 3, 2);
  const r = reflectPointAcrossPlane(pt, p, n);
  // Midpoint lies on the plane
  const mid = pt.clone().add(r).multiplyScalar(0.5);
  assert.ok(Math.abs(mid.clone().sub(p).dot(n)) < 1e-6);
  // Vector from pt to r is parallel to n
  assert.ok(r.clone().sub(pt).cross(n).length() < 1e-6);
  // Reflecting direction preserves length and flips normal component
  const d = new THREE.Vector3(0.3, 0.7, -0.2).normalize();
  const rd = reflectDirectionAcrossPlane(d, n);
  assert.ok(Math.abs(rd.length() - 1) < 1e-6);
  assert.ok(Math.abs(rd.dot(n) + d.dot(n)) < 1e-6);
});

test('PlanarMirror virtual camera projects mirror-plane points and reflected objects to matching UVs', () => {
  const geom = new THREE.PlaneGeometry(2, 2);
  const mesh = new THREE.Mesh(geom, new THREE.MeshBasicMaterial());
  mesh.position.set(0, 1, 0);
  mesh.rotation.y = 0.4;
  mesh.updateMatrixWorld(true);

  const mirror = new PlanarMirror(mesh);
  const cam = new THREE.OrthographicCamera(-2, 2, 2, -2, 0.1, 50);
  cam.position.set(0, 1.5, 8);
  cam.lookAt(0, 1, 0);
  cam.updateMatrixWorld(true);
  cam.updateProjectionMatrix();

  assert.equal(mirror.updateVirtualCamera(cam), true);

  // Pick a point on the mirror plane and a point along the reflected view ray in front of the mirror
  const mirrorPoint = new THREE.Vector3(0.3, 0.2, 0).applyMatrix4(mesh.matrixWorld);
  const vp = new THREE.Matrix4().multiplyMatrices(mirror.virtualCamera.projectionMatrix, mirror.virtualCamera.matrixWorldInverse);
  const p1 = mirrorPoint.clone().applyMatrix4(vp);
  // Moving along virtualCamera's forward axis from mirrorPoint must keep identical NDC xy
  const vcDir = new THREE.Vector3();
  mirror.virtualCamera.getWorldDirection(vcDir);
  const reflectedObj = mirrorPoint.clone().addScaledVector(vcDir, 1.2);
  const p2 = reflectedObj.clone().applyMatrix4(vp);
  assert.ok(Math.abs(p1.x - p2.x) < 1e-5 && Math.abs(p1.y - p2.y) < 1e-5);

  // Camera behind the mirror returns false (back face does not reflect)
  cam.position.set(0, 1.5, -8);
  cam.lookAt(0, 1, 0);
  cam.updateMatrixWorld(true);
  assert.equal(mirror.updateVirtualCamera(cam), false);

  mirror.dispose();
  geom.dispose();
});
