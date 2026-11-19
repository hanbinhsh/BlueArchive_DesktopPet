import { Box3, BufferGeometry, Mesh, Object3D, SkinnedMesh, Vector3 } from 'three';

const rigidParts = new WeakMap<BufferGeometry, number[][] | null>();
function rigidGroups(geometry: BufferGeometry): number[][] | null {
  if (rigidParts.has(geometry)) return rigidParts.get(geometry)!;
  const joints = geometry.getAttribute('skinIndex'), weights = geometry.getAttribute('skinWeight');
  const groups = new Map<number, number[]>();
  if (!joints || !weights) return null;
  for (let i = 0; i < weights.count; i++) {
    let joint = -1;
    for (let k = 0; k < 4; k++) {
      const weight = weights.getComponent(i, k);
      if (Math.abs(weight - 1) < 1e-6 && joint < 0) joint = joints.getComponent(i, k);
      else if (Math.abs(weight) > 1e-6) { rigidParts.set(geometry, null); return null; }
    }
    if (joint < 0) { rigidParts.set(geometry, null); return null; }
    if (!groups.has(joint)) groups.set(joint, []);
    groups.get(joint)!.push(i);
  }
  const parts = groups.size > 1 ? [...groups.values()] : null;
  rigidParts.set(geometry, parts); return parts;
}

// Measure only each visible mesh itself. setFromObject recursively includes
// hidden children; official timelines also park collapsed props far offstage.
export function visiblePoseBounds(root: Object3D, minExtent = 0, updateMatrices = true): Box3 {
  // Runtime diagnostics must preserve the final prop skin matrices applied
  // after local animation blending. Asset framing still updates by default.
  if (updateMatrices) root.updateMatrixWorld(true);
  const result = new Box3(), size = new Vector3();
  root.traverseVisible(object => {
    const mesh = object as Mesh;
    if (!mesh.isMesh || mesh.userData.BA_auxiliary) return;
    // One renderer can contain several independent props. A collapsed bomb
    // parked far away must not enlarge the bounds of the still-visible prop.
    const groups = minExtent && (mesh as SkinnedMesh).isSkinnedMesh ? rigidGroups(mesh.geometry) : null;
    if (groups) {
      const vertex = new Vector3();
      for (const indices of groups) {
        const part = new Box3();
        for (const index of indices) part.expandByPoint(mesh.getVertexPosition(index, vertex).applyMatrix4(mesh.matrixWorld));
        part.getSize(size);
        if (Math.max(size.x, size.y, size.z) >= minExtent) result.union(part);
      }
      return;
    }
    let local: Box3 | null;
    if ((mesh as SkinnedMesh).isSkinnedMesh) {
      (mesh as SkinnedMesh).computeBoundingBox();
      local = (mesh as SkinnedMesh).boundingBox;
    } else {
      mesh.geometry.computeBoundingBox();
      local = mesh.geometry.boundingBox;
    }
    if (!local || local.isEmpty()) return;
    const world = local.clone().applyMatrix4(mesh.matrixWorld);
    world.getSize(size);
    if (Math.max(size.x, size.y, size.z) < minExtent) return;
    result.union(world);
  });
  return result;
}
