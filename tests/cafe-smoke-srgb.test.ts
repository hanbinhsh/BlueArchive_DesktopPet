import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {attachCafeSmoke} from '../src/cafe-smoke';
import {attachWaterFx} from '../src/furniture-fx';

test('attachCafeSmoke decodes sRGB step masks on a cloned texture without mutating shared NoColorSpace textures', async () => {
 const shared = new THREE.DataTexture(new Uint8Array([115, 115, 115, 255]), 1, 1);
 shared.colorSpace = THREE.NoColorSpace;
 const parser = {async getDependency(_type: string, _index: number) { return shared; }};
 const depth = {texture: {value: null}, size: {value: new THREE.Vector2(1, 1)}, range: {value: new THREE.Vector2(0.1, 10)}, scale: {value: 1}, required: false};

 const srgbMat = new THREE.MeshBasicMaterial();
 srgbMat.userData.BA_smokeFx = {
  kind: 'step',
  floats: {_Step_Scroll_Use: 1, _Step_Power: 0, _Step_Custom_DataVertex_color_Use: 0, _RGBRGBA: 0, _Multiply: 1, _Vertex_Alpha_Use: 0, _Custom_Data_Mask_Offset_Use: 0, _Custom_Data_Main_Offset_Use: 0, _Mask_Speed_X: 0, _Mask_Speed_Y: 0, _Main_Speed_X: 0, _Main_Speed_Y: 0},
  colors: {_Color: [2, 2, 2, 1]},
  maskTexture: {index: 0, st: [1, 1, 0, 0], srgb: true},
 };
 const srgbTextures = new Set<THREE.Texture>();
 await attachCafeSmoke(srgbMat, parser, srgbTextures, depth);
 const compiled: any = {uniforms: {}, vertexShader: '#include <uv_vertex>\n#include <project_vertex>', fragmentShader: '#include <map_fragment>\n#include <color_fragment>\n#include <premultiplied_alpha_fragment>\n#include <colorspace_fragment>'};
 srgbMat.onBeforeCompile(compiled, {} as any);
 assert.notEqual(compiled.uniforms.maskTex.value, shared);
 assert.equal(compiled.uniforms.maskTex.value.colorSpace, THREE.SRGBColorSpace);
 assert.equal(shared.colorSpace, THREE.NoColorSpace);

 const linearMat = new THREE.MeshBasicMaterial();
 linearMat.userData.BA_smokeFx = {
  kind: 'step',
  floats: {_Step_Scroll_Use: 1, _Step_Power: 0, _Step_Custom_DataVertex_color_Use: 0, _RGBRGBA: 0, _Multiply: 1, _Vertex_Alpha_Use: 0, _Custom_Data_Mask_Offset_Use: 0, _Custom_Data_Main_Offset_Use: 0, _Mask_Speed_X: 0, _Mask_Speed_Y: 0, _Main_Speed_X: 0, _Main_Speed_Y: 0},
  colors: {_Color: [2, 2, 2, 1]},
  maskTexture: {index: 0, st: [1, 1, 0, 0]},
 };
 await attachCafeSmoke(linearMat, parser, new Set<THREE.Texture>(), depth);
 const compiledLinear: any = {uniforms: {}, vertexShader: '#include <uv_vertex>\n#include <project_vertex>', fragmentShader: '#include <map_fragment>\n#include <color_fragment>\n#include <premultiplied_alpha_fragment>\n#include <colorspace_fragment>'};
 linearMat.onBeforeCompile(compiledLinear, {} as any);
 assert.equal(compiledLinear.uniforms.maskTex.value, shared);
 assert.equal(compiledLinear.uniforms.maskTex.value.colorSpace, THREE.NoColorSpace);
});

test('attachWaterFx decodes sRGB step mask and distort textures on clones without mutating shared textures', async () => {
 const shared = new THREE.DataTexture(new Uint8Array([120, 120, 120, 255]), 1, 1);
 shared.colorSpace = THREE.NoColorSpace;
 const parser = {async getDependency(_type: string, _index: number) { return shared; }};
 const mat = new THREE.MeshBasicMaterial();
 mat.userData.BA_waterFx = {
  kind: 'step',
  color: [1, 1, 1, 1],
  floats: {_Step_Scroll_Use: 1, _Step_Power: 0, _Step_Custom_DataVertex_color_Use: 0, _RGBRGBA: 0, _Multiply: 1},
  mainTexture: {index: 0, st: [1, 1, 0, 0]},
  maskTexture: {index: 0, st: [1, 1, 0, 0], srgb: true},
  distortTexture: {index: 0, st: [1, 1, 0, 0], srgb: true},
 };
 await attachWaterFx(mat, parser, new Set<THREE.Texture>());
 const compiled: any = {uniforms: {}, vertexShader: '#include <uv_vertex>', fragmentShader: '#include <map_fragment>\n#include <premultiplied_alpha_fragment>'};
 mat.onBeforeCompile(compiled, {} as any);
 assert.equal(compiled.uniforms.mainTex.value, shared);
 assert.equal(shared.colorSpace, THREE.NoColorSpace);
 assert.notEqual(compiled.uniforms.maskTex.value, shared);
 assert.equal(compiled.uniforms.maskTex.value.colorSpace, THREE.SRGBColorSpace);
 assert.notEqual(compiled.uniforms.distortTex.value, shared);
 assert.equal(compiled.uniforms.distortTex.value.colorSpace, THREE.SRGBColorSpace);
});
