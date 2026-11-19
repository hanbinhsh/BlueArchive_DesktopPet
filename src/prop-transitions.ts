import * as THREE from 'three';

// Props have their own skin; never override joints also used by the body/face.
const bodyJoint = /Bip\d+[ _](?:Head|Neck|Pelvis|Spine|[LR][ _](?:Thigh|Calf|Foot|Hand|Finger|Forearm|UpperArm|Clavicle))|(?:^|[_ ])(?:eye|brow|blow|mouth|hair|skirt)/i;
export function propBones(root: THREE.Object3D) {
  const props = new Set<THREE.Bone>(), body = new Set<THREE.Bone>();
  const meshes: string[] = [];
  root.traverse(object => {
    const mesh = object as THREE.SkinnedMesh;
    if (!mesh.isSkinnedMesh) return;
    // New Year Kayoko's separately skinned cat includes its own eye bones.
    const isProp = /(?:^|_)Cat(?:_|$)/i.test(mesh.name) || !mesh.skeleton.bones.some(bone => bodyJoint.test(bone.name));
    if (isProp) meshes.push(mesh.name);
    for (const bone of mesh.skeleton.bones) (isProp ? props : body).add(bone);
  });
  return { bones: [...props].filter(bone => !body.has(bone)), meshes };
}

/** Blend complete prop skin transforms, not multiplying independently blended
 * parent/child scales. Unity exports can contain reciprocal scales (0.001 and
 * 1000); local TRS blending creates a huge prop between two correct poses.
 * Matrix blending keeps every skinned vertex between the two endpoint poses.
 */
export class PropTransitions {
  readonly meshes: string[];
  readonly bones: THREE.Bone[];
  private pairs: { bone: THREE.Bone; sample: THREE.Object3D; from: THREE.Matrix4 }[];
  private sampleRoot: THREE.Object3D;
  private mixer: THREE.AnimationMixer;
  private inverse = new THREE.Matrix4();
  private blended = new THREE.Matrix4();
  private action?: THREE.AnimationAction;
  private elapsed = 0;
  private duration = 0;

  constructor(private root: THREE.Object3D) {
    const selected = propBones(root); this.meshes = selected.meshes; this.bones = selected.bones;
    const copies = new Map<THREE.Object3D, THREE.Object3D>();
    const copy = (source: THREE.Object3D): THREE.Object3D => {
      const node = new THREE.Object3D();
      node.name = source.name; node.uuid = source.uuid;
      node.position.copy(source.position); node.quaternion.copy(source.quaternion); node.scale.copy(source.scale);
      copies.set(source, node);
      for (const child of source.children) node.add(copy(child));
      return node;
    };
    this.sampleRoot = copy(root);
    this.mixer = new THREE.AnimationMixer(this.sampleRoot);
    this.pairs = this.bones.map(bone => ({ bone, sample: copies.get(bone)!, from: new THREE.Matrix4() }));
  }

  begin(clip: THREE.AnimationClip, duration: number) {
    this.elapsed = 0; this.duration = duration;
    this.inverse.copy(this.root.parent!.matrixWorld).invert();
    for (const pair of this.pairs) pair.from.multiplyMatrices(this.inverse, pair.bone.matrixWorld);
    this.mixer.stopAllAction();
    this.action = this.mixer.clipAction(clip).reset().setLoop(THREE.LoopOnce, 1);
    this.action.clampWhenFinished = true; this.action.play();
  }

  update(time: number, dt: number) {
    if (!this.action || !this.duration) return;
    this.elapsed += dt;
    const alpha = Math.min(1, this.elapsed / this.duration);
    this.action.paused = false;
    this.mixer.setTime(time);
    this.sampleRoot.updateMatrixWorld(true);
    for (const pair of this.pairs) {
      const a = pair.from.elements, b = pair.sample.matrixWorld.elements, c = this.blended.elements;
      for (let i = 0; i < 16; i++) c[i] = a[i] + (b[i] - a[i]) * alpha;
      pair.bone.matrixWorld.multiplyMatrices(this.root.parent!.matrixWorld, this.blended);
    }
    if (alpha === 1) { this.mixer.stopAllAction(); this.duration = 0; }
  }
}
