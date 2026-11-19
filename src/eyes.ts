import * as THREE from 'three';
/** Small pupil-only offsets, applied after the original animation and removed
 * before its next evaluation so unanimated bones never accumulate drift. */
export class EyeFollower {
  readonly bones: THREE.Bone[] = [];
  private offsets = new Map<THREE.Bone, THREE.Vector3>();
  private smooth = new THREE.Vector2();
  constructor(root: THREE.Object3D) {
    root.traverse(object => { if ((object as THREE.Bone).isBone && /(?:^|_)Xtra_eye[LR]$/i.test(object.name)) this.bones.push(object as THREE.Bone); });
  }
  reset() { for (const [bone, delta] of this.offsets) bone.position.sub(delta); this.offsets.clear(); }
  update(enabled: boolean, cursor: {x:number;y:number}, width: number, height: number, camera: THREE.Camera, dt: number) {
    if (!enabled || this.bones.length !== 2) { this.smooth.set(0, 0); return; }
    const left = this.bones[0].getWorldPosition(new THREE.Vector3());
    const right = this.bones[1].getWorldPosition(new THREE.Vector3());
    const gap = left.distanceTo(right); if (gap < 1e-5) return;
    const projected = left.clone().add(right).multiplyScalar(.5).project(camera);
    const target = new THREE.Vector2(
      THREE.MathUtils.clamp((cursor.x / width * 2 - 1 - projected.x) * 1.3, -1, 1),
      THREE.MathUtils.clamp((1 - cursor.y / height * 2 - projected.y) * 1.3, -1, 1));
    this.smooth.lerp(target, 1-Math.exp(-dt*9));
    const rightAxis = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const upAxis = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    const shift = rightAxis.multiplyScalar(gap*.065*this.smooth.x).add(upAxis.multiplyScalar(gap*.04*this.smooth.y));
    for (const bone of this.bones) {
      if (!bone.parent) continue;
      const world = bone.getWorldPosition(new THREE.Vector3());
      const a = bone.parent.worldToLocal(world.clone());
      const b = bone.parent.worldToLocal(world.add(shift));
      const delta = b.sub(a); bone.position.add(delta); this.offsets.set(bone, delta);
    }
  }
  diagnostics() { return { supported: this.bones.length === 2, direction: this.smooth.toArray(), offsets: [...this.offsets.values()].map(v=>v.toArray()) }; }
}
