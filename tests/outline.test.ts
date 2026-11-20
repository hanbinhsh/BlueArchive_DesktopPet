import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import {ModelOutline,smoothOutlineNormals} from '../src/model-outline';
import {normalizeSettings} from '../src/shared';
import {visiblePoseBounds} from '../src/framing';

test('outline migration keeps the switch and validates wiki percentage width',()=>{
 assert.equal(normalizeSettings({outline:true}).outlineWidth,38);
 for(const [input,expected] of [[-2,0],[500,400],[38,38],[NaN,38],[Infinity,38]])assert.equal(normalizeSettings({outlineWidth:input}).outlineWidth,expected);
});
test('outline normals weld UV seams without modifying original shading normals',()=>{
 const g=new THREE.BoxGeometry().toNonIndexed(),before=g.getAttribute('normal').array.slice();smoothOutlineNormals(g);
 const p=g.getAttribute('position'),n=g.getAttribute('smoothNormal');
 for(let i=0;i<p.count;i++)for(let j=i+1;j<p.count;j++)if(p.getX(i)===p.getX(j)&&p.getY(i)===p.getY(j)&&p.getZ(i)===p.getZ(j))assert.deepEqual([n.getX(i),n.getY(i),n.getZ(i)],[n.getX(j),n.getY(j),n.getZ(j)]);
 assert.deepEqual(g.getAttribute('normal').array,before);g.dispose();
});
test('outline follows hidden parents, excludes transparent FX, and leaves picking/framing unchanged',()=>{
 const root=new THREE.Group(),g=new THREE.BoxGeometry(),opaque=new THREE.MeshBasicMaterial(),water=new THREE.MeshBasicMaterial({transparent:true});
 const body=new THREE.Mesh(g,opaque),fx=new THREE.Mesh(g,water);root.add(body,fx);
 const before=visiblePoseBounds(root),outline=new ModelOutline(root);outline.apply(true,38);
 assert.equal(outline.meshes.length,1);assert.equal(outline.meshes[0].parent,body);
 assert.deepEqual(visiblePoseBounds(root),before);const hits:THREE.Intersection[]=[];outline.meshes[0].raycast(new THREE.Raycaster(),hits);assert.equal(hits.length,0);
 assert.ok(Math.abs((outline.meshes[0].material as THREE.ShaderMaterial).uniforms.outlineWidth.value-.00076)<1e-12);
 body.visible=false;let visible=0;root.traverseVisible(o=>{if(o.userData.isOutline)visible++;});assert.equal(visible,0);
 const vs=(outline.meshes[0].material as THREE.ShaderMaterial).vertexShader;
 assert.match(vs,/skinScale=length\(objectNormal\)/);
 assert.match(vs,/if\(skinScale<\.02\)/);
 outline.dispose();assert.equal(body.children.length,0);g.dispose();opaque.dispose();water.dispose();
});
