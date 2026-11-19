import test from 'node:test';
import assert from 'node:assert/strict';
import * as T from 'three';
import {updateFxBillboard} from '../src/fx-billboard';
test('a group billboard keeps sibling icon offsets in one camera frame through scene rotation',()=>{
 const root=new T.Group(),group=new T.Group(),bubble=new T.Group(),icon=new T.Group();root.add(group);group.add(bubble,icon);bubble.position.set(0,.7,.71);icon.position.set(0,.8,.71);
 const camera=new T.PerspectiveCamera();camera.position.set(0,3,8);camera.lookAt(0,0,0);camera.updateMatrixWorld(true);
 for(const yaw of [0,.7,2.4]){root.rotation.set(.3,yaw,-.1);updateFxBillboard(group,camera,false);const delta=icon.getWorldPosition(new T.Vector3()).sub(bubble.getWorldPosition(new T.Vector3())).applyQuaternion(camera.quaternion.clone().invert());assert.ok(Math.abs(delta.x)<1e-6&&Math.abs(delta.z)<1e-6);assert.ok(Math.abs(delta.y-.1)<1e-6);}
});
test('fixed Y billboards stay vertical with a pitched camera',()=>{
 const group=new T.Group(),camera=new T.Camera();camera.rotation.x=.7;camera.updateMatrixWorld(true);updateFxBillboard(group,camera,true);assert.ok(new T.Vector3(0,1,0).applyQuaternion(group.quaternion).distanceTo(new T.Vector3(0,1,0))<1e-6);
});
