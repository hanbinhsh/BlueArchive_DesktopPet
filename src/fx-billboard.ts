import * as THREE from 'three';
// The source FxBillboard rotates a hierarchy, not just its rendered quads.
// Keeping child offsets in that frame preserves speech-bubble/icon placement.
export function updateFxBillboard(object:THREE.Object3D,camera:THREE.Camera,fixedY:boolean){
 const facing=camera.getWorldQuaternion(new THREE.Quaternion());
 if(fixedY){const forward=new THREE.Vector3(0,0,1).applyQuaternion(facing);facing.setFromAxisAngle(new THREE.Vector3(0,1,0),Math.atan2(forward.x,forward.z));}
 object.parent?.updateWorldMatrix(true,false);
 const parent=object.parent?.getWorldQuaternion(new THREE.Quaternion())||new THREE.Quaternion();
 object.quaternion.copy(parent.invert().multiply(facing));object.updateWorldMatrix(false,true);
}
