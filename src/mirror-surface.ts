import * as THREE from 'three';

export interface MirrorSurfaceSpec {
  tint?: [number, number, number];
  reflectivity?: number;
  normal?: [number, number, number];
}

const VERTEX_SHADER = /* glsl */ `
varying vec3 vWorldPos;
varying vec2 vUv;
void main() {
  vUv = uv;
  vec4 wp = modelMatrix * vec4(position, 1.0);
  vWorldPos = wp.xyz;
  gl_Position = projectionMatrix * viewMatrix * wp;
}
`;

const FRAGMENT_SHADER = /* glsl */ `
uniform sampler2D uReflectionMap;
uniform mat4 uReflectionVP;
uniform vec3 uGlassTint;
uniform float uReflectivity;
varying vec3 vWorldPos;
varying vec2 vUv;
void main() {
  vec4 clip = uReflectionVP * vec4(vWorldPos, 1.0);
  vec2 uv = (clip.xy / max(clip.w, 1e-6)) * 0.5 + 0.5;
  // Subtle cool silver-mirror gradient + soft diagonal glass sheen
  float sheen = 0.055 * smoothstep(0.15, 0.85, vUv.x * 0.65 + vUv.y * 0.35);
  vec3 baseGlass = clamp(uGlassTint + vec3(sheen), 0.0, 1.0);
  if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) {
    gl_FragColor = vec4(baseGlass, 1.0);
    #include <colorspace_fragment>
    return;
  }
  vec4 refl = texture2D(uReflectionMap, uv);
  vec3 col = mix(baseGlass, mix(baseGlass, refl.rgb, uReflectivity), refl.a);
  gl_FragColor = vec4(col, 1.0);
  #include <colorspace_fragment>
}
`;

export function reflectPointAcrossPlane(
  point: THREE.Vector3,
  planePoint: THREE.Vector3,
  planeNormal: THREE.Vector3,
  out = new THREE.Vector3(),
): THREE.Vector3 {
  const dist = point.clone().sub(planePoint).dot(planeNormal);
  return out.copy(point).addScaledVector(planeNormal, -2 * dist);
}

export function reflectDirectionAcrossPlane(
  dir: THREE.Vector3,
  planeNormal: THREE.Vector3,
  out = new THREE.Vector3(),
): THREE.Vector3 {
  const proj = dir.dot(planeNormal);
  return out.copy(dir).addScaledVector(planeNormal, -2 * proj);
}

export class PlanarMirror {
  readonly mesh: THREE.Mesh;
  readonly material: THREE.ShaderMaterial;
  readonly virtualCamera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.01, 50);
  lastDiag: Record<string, unknown> = {};
  private target?: THREE.WebGLRenderTarget;
  private localCenter = new THREE.Vector3();
  private localNormal = new THREE.Vector3(0, 0, 1);
  private localCorners: THREE.Vector3[] = [];
  private readonly worldCenter = new THREE.Vector3();
  private readonly worldNormal = new THREE.Vector3();
  private readonly normalMatrix = new THREE.Matrix3();
  private readonly clipPlane = new THREE.Plane();
  private readonly reflVP = new THREE.Matrix4();
  private readonly camPos = new THREE.Vector3();
  private readonly mirrorRight = new THREE.Vector3();
  private readonly mirrorUp = new THREE.Vector3();
  private readonly worldUp = new THREE.Vector3(0, 1, 0);
  private readonly tmpCorner = new THREE.Vector3();
  private readonly size = new THREE.Vector2();

  constructor(mesh: THREE.Mesh, spec: MirrorSurfaceSpec = {}) {
    this.mesh = mesh;
    const geom = mesh.geometry;
    geom.computeBoundingBox();
    if (geom.boundingBox) {
      const bb = geom.boundingBox;
      bb.getCenter(this.localCenter);
      for (const x of [bb.min.x, bb.max.x]) {
        for (const y of [bb.min.y, bb.max.y]) {
          for (const z of [bb.min.z, bb.max.z]) {
            this.localCorners.push(new THREE.Vector3(x, y, z));
          }
        }
      }
    }
    if (spec.normal) {
      this.localNormal.set(spec.normal[0], spec.normal[1], spec.normal[2]).normalize();
    } else {
      const pos = geom.getAttribute('position');
      const idx = geom.getIndex();
      if (pos && pos.count >= 3) {
        const i0 = idx ? idx.getX(0) : 0;
        const i1 = idx ? idx.getX(1) : 1;
        const i2 = idx ? idx.getX(2) : 2;
        const a = new THREE.Vector3().fromBufferAttribute(pos, i0);
        const b = new THREE.Vector3().fromBufferAttribute(pos, i1);
        const c = new THREE.Vector3().fromBufferAttribute(pos, i2);
        const n = b.sub(a).cross(c.sub(a));
        if (n.lengthSq() > 1e-10) this.localNormal.copy(n.normalize());
      }
    }
    const tint = spec.tint ?? [0.76, 0.81, 0.88];
    this.material = new THREE.ShaderMaterial({
      vertexShader: VERTEX_SHADER,
      fragmentShader: FRAGMENT_SHADER,
      side: THREE.FrontSide,
      polygonOffset: true,
      polygonOffsetFactor: -2,
      polygonOffsetUnits: -2,
      uniforms: {
        uReflectionMap: { value: null },
        uReflectionVP: { value: this.reflVP },
        uGlassTint: { value: new THREE.Color(tint[0], tint[1], tint[2]) },
        uReflectivity: { value: spec.reflectivity ?? 0.90 },
      },
    });
    this.material.userData.BA_mirrorSurface = spec;
    mesh.material = this.material;
  }

  updateVirtualCamera(mainCamera: THREE.OrthographicCamera): boolean {
    this.mesh.updateWorldMatrix(true, false);
    this.worldCenter.copy(this.localCenter).applyMatrix4(this.mesh.matrixWorld);
    this.normalMatrix.getNormalMatrix(this.mesh.matrixWorld);
    this.worldNormal.copy(this.localNormal).applyMatrix3(this.normalMatrix).normalize();

    mainCamera.updateMatrixWorld(true);
    mainCamera.getWorldPosition(this.camPos);
    // Only render when camera is on the reflective front side of the mirror plane
    const sideDot = this.camPos.clone().sub(this.worldCenter).dot(this.worldNormal);
    if (sideDot <= 0) return false;

    // Build orthonormal basis aligned with the mirror surface, looking straight
    // from behind the glass along +worldNormal so characters standing in front of
    // the mirror appear centered and properly mirrored even in oblique 45-degree Cafe views.
    this.mirrorRight.crossVectors(this.worldUp, this.worldNormal);
    if (this.mirrorRight.lengthSq() < 1e-6) {
      this.mirrorRight.set(1, 0, 0).cross(this.worldNormal);
    }
    this.mirrorRight.normalize();
    this.mirrorUp.crossVectors(this.worldNormal, this.mirrorRight).normalize();

    let halfW = 0.4;
    let halfH = 0.6;
    if (this.localCorners.length > 0) {
      let maxW = 0;
      let maxH = 0;
      for (const c of this.localCorners) {
        this.tmpCorner.copy(c).applyMatrix4(this.mesh.matrixWorld).sub(this.worldCenter);
        maxW = Math.max(maxW, Math.abs(this.tmpCorner.dot(this.mirrorRight)));
        maxH = Math.max(maxH, Math.abs(this.tmpCorner.dot(this.mirrorUp)));
      }
      if (maxW > 1e-4) halfW = maxW;
      if (maxH > 1e-4) halfH = maxH;
    }

    const vc = this.virtualCamera;
    vc.left = -halfW;
    vc.right = halfW;
    vc.top = halfH;
    vc.bottom = -halfH;
    vc.zoom = 1;
    vc.near = 0.05;
    vc.far = 25;
    vc.position.copy(this.worldCenter).addScaledVector(this.worldNormal, -4.0);
    vc.up.copy(this.mirrorUp);
    vc.lookAt(this.worldCenter);
    vc.updateMatrixWorld(true);
    vc.updateProjectionMatrix();

    this.reflVP.multiplyMatrices(vc.projectionMatrix, vc.matrixWorldInverse);
    // Clip everything behind the mirror glass so the mirror frame backing never occludes the reflection
    this.clipPlane.setFromNormalAndCoplanarPoint(this.worldNormal, this.worldCenter);
    this.clipPlane.constant -= 0.015;
    this.lastDiag = {
      center: this.worldCenter.toArray().map((n) => +n.toFixed(3)),
      normal: this.worldNormal.toArray().map((n) => +n.toFixed(3)),
      halfSize: [+halfW.toFixed(3), +halfH.toFixed(3)],
      sideDot: +sideDot.toFixed(3),
    };
    return true;
  }

  render(renderer: THREE.WebGLRenderer, scene: THREE.Scene, mainCamera: THREE.OrthographicCamera) {
    if (!this.mesh.visible) return;
    if (!this.updateVirtualCamera(mainCamera)) return;

    renderer.getDrawingBufferSize(this.size);
    const dim = Math.max(256, Math.min(1024, Math.round(Math.max(this.size.x, this.size.y))));
    const w = dim;
    const h = dim;
    if (!this.target) {
      this.target = new THREE.WebGLRenderTarget(w, h, {
        stencilBuffer: true,
        minFilter: THREE.LinearFilter,
        magFilter: THREE.LinearFilter,
      });
      this.target.texture.colorSpace = THREE.SRGBColorSpace;
    } else if (this.target.width !== w || this.target.height !== h) {
      this.target.setSize(w, h);
    }

    const oldTarget = renderer.getRenderTarget();
    const oldClipping = renderer.clippingPlanes;
    const oldClearAlpha = renderer.getClearAlpha();
    const oldClearColor = renderer.getClearColor(new THREE.Color());
    const wasVisible = this.mesh.visible;

    this.mesh.visible = false;
    renderer.clippingPlanes = [...oldClipping, this.clipPlane];
    try {
      renderer.setRenderTarget(this.target);
      renderer.setClearColor(0x000000, 0);
      renderer.clear(true, true, true);
      renderer.render(scene, this.virtualCamera);
    } finally {
      this.mesh.visible = wasVisible;
      renderer.clippingPlanes = oldClipping;
      renderer.setClearColor(oldClearColor, oldClearAlpha);
      renderer.setRenderTarget(oldTarget);
    }
    this.material.uniforms.uReflectionMap.value = this.target.texture;
  }

  dispose() {
    this.target?.dispose();
    this.material.dispose();
  }
}
