import * as THREE from 'three';

export interface HaloParameters {
  offset: number[]; rotation: number[]; minOffset: number[]; maxOffset: number[];
  positionPower: number; rotationPower: number; fixYRotation: boolean;
}
// Unity's follow component is procedural, not an AnimationClip. Use its
// serialized local offsets/limits and frame-rate-independent interpolation.
export class HaloFollower {
  private offset = new THREE.Vector3();
  private rotation = new THREE.Quaternion();
  private min = new THREE.Vector3();
  private max = new THREE.Vector3();
  private desired = new THREE.Vector3();
  private current = new THREE.Vector3();
  private targetRotation = new THREE.Quaternion();
  private parentRotation = new THREE.Quaternion();
  private initialYaw: number;
  constructor(readonly node: THREE.Object3D, readonly target: THREE.Object3D, readonly parameters: HaloParameters) {
    this.offset.fromArray(parameters.offset); this.rotation.fromArray(parameters.rotation).normalize();
    this.min.fromArray(parameters.minOffset); this.max.fromArray(parameters.maxOffset);
    this.initialYaw = node.rotation.y;
  }
  update(dt: number, snap = false) {
    const parent = this.node.parent!;
    this.target.updateWorldMatrix(true, false); parent.updateWorldMatrix(true, false);
    this.desired.copy(this.offset); this.target.localToWorld(this.desired); parent.worldToLocal(this.desired);
    this.node.position.lerp(this.desired, snap ? 1 : 1 - Math.pow(1 - this.parameters.positionPower, dt * 60));
    // Clamp lag in the target's local coordinate frame, including X reflection.
    this.current.copy(this.node.position); parent.localToWorld(this.current); this.target.worldToLocal(this.current);
    this.current.clamp(this.min, this.max); this.target.localToWorld(this.current); parent.worldToLocal(this.current);
    this.node.position.copy(this.current);
    this.target.getWorldQuaternion(this.targetRotation).multiply(this.rotation);
    parent.getWorldQuaternion(this.parentRotation).invert(); this.targetRotation.premultiply(this.parentRotation);
    this.node.quaternion.slerp(this.targetRotation, snap ? 1 : 1 - Math.pow(1 - this.parameters.rotationPower, dt * 60));
    if (this.parameters.fixYRotation) this.node.rotation.y = this.initialYaw;
    this.node.updateMatrixWorld(true);
  }
}
