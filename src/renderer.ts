import { compositeFragment } from './composite-shader';
import * as THREE from 'three';
import { SceneView } from './scene-view';
import { type PetApi,type Settings,type Character } from './shared';
import { effectiveSpeed,type PlaybackRequest } from './activities';
import { visiblePoseBounds } from './framing';
declare global {interface Window {pet:PetApi;petDiagnostics:any;petMeasureFraming?:boolean;petFramingDiagnostics?:any;}}
const api=window.pet,canvas=document.querySelector<HTMLCanvasElement>('#pet')!,status=document.querySelector<HTMLElement>('#status')!,message=document.querySelector<HTMLElement>('#message')!;
window.petDiagnostics={frames:0,action:'',error:null,hit:true,actionTime:0,sceneLoads:0};
let settings:Settings,character:Character,view:SceneView|undefined,previous:SceneView|undefined;
let visible=true,ready=false,roaming=0,hit=true,request:PlaybackRequest|undefined,generation=0,elapsed=0,gapElapsed=0,inGap=false,loading=false;
let blend=1,blendDuration=.18,prefetchKey:string|undefined,viewport='';
let gesture:{x:number;y:number;yaw:number;pitch:number;roll:number;rotate:boolean;axis:string;moved:boolean;pointerId:number}|null=null;
const cursor={x:0,y:0},mouse=new THREE.Vector2(2,2),raycaster=new THREE.Raycaster(),cache=new Map<string,Promise<SceneView>>();
const renderer=new THREE.WebGLRenderer({canvas,alpha:true,stencil:true,antialias:true,preserveDrawingBuffer:true,powerPreference:'low-power'});
renderer.setClearColor(0,0);renderer.outputColorSpace=THREE.SRGBColorSpace;
const targets=[new THREE.WebGLRenderTarget(1,1,{stencilBuffer:true,samples:4}),new THREE.WebGLRenderTarget(1,1,{stencilBuffer:true,samples:4})];
const composite=new THREE.Scene(),quadCamera=new THREE.OrthographicCamera(-1,1,1,-1,0,1);
const quadMaterial=new THREE.ShaderMaterial({depthTest:false,depthWrite:false,transparent:true,premultipliedAlpha:true,uniforms:{a:{value:targets[0].texture},b:{value:targets[1].texture},mixValue:{value:1}},vertexShader:'varying vec2 uv0;void main(){uv0=uv;gl_Position=vec4(position.xy,0.,1.);}',fragmentShader:compositeFragment});
composite.add(new THREE.Mesh(new THREE.PlaneGeometry(2,2),quadMaterial));
function resize(){if(!settings)return;const w=Math.round(settings.size*1.5),h=Math.round(settings.size*1.45),ratio=Math.min(devicePixelRatio,2),key=`${w}:${h}:${ratio}`;if(key!==viewport){viewport=key;renderer.setPixelRatio(ratio);renderer.setSize(w,h,false);for(const t of targets)t.setSize(Math.round(w*ratio),Math.round(h*ratio));}view?.resize(settings.size);previous?.resize(settings.size);}
const keyOf=(id?:string)=>id?character.furniture!.find(f=>f.id===id)!.model:character.model;
function prune(){for(const [key,p]of cache)void p.then(v=>{if(v!==view&&v!==previous&&key!==prefetchKey&&cache.get(key)===p){cache.delete(key);v.dispose();}}).catch(()=>{if(cache.get(key)===p)cache.delete(key);});}
function ensure(id?:string){const key=keyOf(id);let p=cache.get(key);if(!p){p=api.asset(id).then(payload=>SceneView.create(payload,settings)).then(v=>{window.petDiagnostics.sceneLoads++;api.durations(v.durations);return v;});cache.set(key,p);void p.catch(()=>{if(cache.get(key)===p)cache.delete(key);});}return p;}
function setHit(value:boolean){if(value===hit)return;hit=value;window.petDiagnostics.hit=value;api.hit(value);}
function hitTest(){if(!view||!ready||gesture)return;raycaster.setFromCamera(mouse,view.camera);setHit(raycaster.intersectObject(view.root,true).some(h=>{for(let p:THREE.Object3D|null=h.object;p;p=p.parent)if(!p.visible)return false;return (h.object as THREE.Mesh).isMesh&&!h.object.userData.BA_auxiliary;}));}
function updateMouse(e:MouseEvent){mouse.set(e.clientX/innerWidth*2-1,1-e.clientY/innerHeight*2);}
async function receive(r:PlaybackRequest){
 const current=++generation;request=r;loading=true;elapsed=gapElapsed=0;inGap=false;prefetchKey=keyOf(r.step?.kind==='furniture'?r.step.id:undefined);
 try{
  const nextView=await ensure(r.step?.kind==='furniture'?r.step.id:undefined);
  if(current!==generation){prune();return;}
  previous=undefined;
  if(nextView!==view){previous=view;view=nextView;blend=previous?0:1;blendDuration=.18/effectiveSpeed(settings).transition;view.orientation(settings,0,false);resize();}
  roaming=0;view.play(r.step?.id||'idle',settings,!!r.continuous||!r.step||r.step.mode==='seconds',r.step?.mode==='count'?r.step.value:1);
  ready=true;loading=false;window.petDiagnostics.error=null;status.hidden=true;
  api.playbackEvent(r.token,'ready');api.activity(r.step?'sequence':'idle');
  prefetchKey=r.next?keyOf(r.next.kind==='furniture'?r.next.id:undefined):undefined;
  if(r.next)void ensure(r.next.kind==='furniture'?r.next.id:undefined).catch(()=>{});prune();
 }catch(e){if(current!==generation)return;loading=false;api.playbackEvent(r.token,'error',String(e));window.petDiagnostics.error=String(e);message.textContent='动作加载失败：'+String(e);status.hidden=false;prune();}
}
api.onPlayback(r=>void receive(r));
api.onSettings(s=>{settings=s;view?.orientation(s,roaming,false);resize();});
api.onRoam(direction=>{if(!view||(direction&&gesture)||(!direction&&!roaming))return;roaming=direction;view.orientation(settings,direction,true);view.play(direction?'walk':'idle',settings,true);api.activity(direction?'walk':'idle');});
function direct(id:string){if(!view)return;request=undefined;generation++;loading=false;view.play(id,settings,id==='idle'||(id==='pickup'&&!!gesture?.moved));api.activity(id);}
api.onAction(id=>{if(!gesture?.moved)direct(id);});
api.onCursor(p=>{cursor.x=p.x;cursor.y=p.y;if(!gesture){mouse.set(p.x/innerWidth*2-1,1-p.y/innerHeight*2);hitTest();}});
api.onVisibility(v=>{visible=v;last=performance.now();if(!v)finishGesture(false);});
function touch(){if(roaming){roaming=0;view?.orientation(settings,0,true);direct('idle');}api.touch();}
function finishGesture(click:boolean){if(!gesture)return;const old=gesture;gesture=null;if(canvas.hasPointerCapture(old.pointerId))canvas.releasePointerCapture(old.pointerId);if(old.moved&&!old.rotate){api.drag(false);if(!view?.furniture)direct('idle');}if(click&&!old.moved){if(view?.furniture){if(!request?.step||request.continuous)view.play(view.actionId,settings,true);}else{api.activity('manual');direct('interact');}}hitTest();}
canvas.addEventListener('pointerdown',e=>{updateMouse(e);hitTest();if(e.button!==0||!ready||!hit)return;touch();gesture={x:e.screenX,y:e.screenY,yaw:settings.yaw,pitch:settings.pitch,roll:settings.roll,rotate:e.shiftKey||e.ctrlKey||e.altKey,axis:e.altKey?'z':e.ctrlKey?'x':'y',moved:false,pointerId:e.pointerId};canvas.setPointerCapture(e.pointerId);api.hit(true);});
window.addEventListener('pointermove',e=>{updateMouse(e);if(gesture){const dx=e.screenX-gesture.x,dy=e.screenY-gesture.y;if(!gesture.moved&&Math.hypot(dx,dy)>=4){gesture.moved=true;if(!gesture.rotate){api.drag(true);if(!view?.furniture)direct(view?.actions.has('pickup')?'pickup':'idle');}}if(gesture.rotate&&gesture.moved){if(gesture.axis==='x')settings.pitch=gesture.pitch+dy*.012;else if(gesture.axis==='z')settings.roll=gesture.roll+dx*.012;else settings.yaw=gesture.yaw+dx*.012;view?.orientation(settings,0,false);api.rotate(settings.yaw,settings.pitch,settings.roll);}}else hitTest();});
window.addEventListener('mousemove',e=>{if(!gesture){updateMouse(e);hitTest();}});
window.addEventListener('pointerup',()=>finishGesture(true));window.addEventListener('pointercancel',()=>finishGesture(false));window.addEventListener('blur',()=>finishGesture(false));canvas.addEventListener('lostpointercapture',()=>finishGesture(false));window.addEventListener('mouseleave',()=>{if(!gesture){mouse.set(2,2);setHit(false);}});
window.addEventListener('contextmenu',e=>{e.preventDefault();touch();finishGesture(false);api.menu();});canvas.addEventListener('wheel',e=>{if(settings?.wheelPassThrough){e.preventDefault();return;}if(ready&&hit&&!gesture){e.preventDefault();touch();api.resize(settings.size-Math.sign(e.deltaY)*20);}},{passive:false});window.addEventListener('resize',resize);
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();message.textContent='显卡渲染上下文丢失，请重启桌宠。';status.hidden=false;api.report(message.textContent);});
let last=performance.now(),accumulated=0;
function frame(now:number){requestAnimationFrame(frame);const dt=(now-last)/1000;last=now;if(!visible||!ready||!view){accumulated=0;return;}accumulated+=dt;if(accumulated<1/30-.0005)return;const real=accumulated,step=Math.min(real,.1);accumulated=0;
 if(Number.isFinite(window.petDiagnostics.seekTime)){view.mixer.setTime(window.petDiagnostics.seekTime);delete window.petDiagnostics.seekTime;}
 const frozen=Number.isFinite(window.petDiagnostics.freezeTime);if(frozen)view.mixer.setTime(window.petDiagnostics.freezeTime);
 view.update(frozen?0:step,settings,cursor,roaming,!gesture&&!request?.step);
 if(previous){previous.update(step,settings,cursor,0,false);blend=Math.min(1,blend+step/blendDuration);renderer.setRenderTarget(targets[0]);renderer.clear();previous.render(renderer);renderer.setRenderTarget(targets[1]);renderer.clear();view.render(renderer);renderer.setRenderTarget(null);quadMaterial.uniforms.mixValue.value=blend;renderer.render(composite,quadCamera);if(blend===1){previous=undefined;prune();}}

 else{renderer.setRenderTarget(null);view.render(renderer);}
 hitTest();const diag=window.petDiagnostics;Object.assign(diag,view.diagnostics(diag.measureFace,diag.measurePose));if(diag.pose)diag.pose.canvas=[canvas.width,canvas.height];diag.frames++;diag.memory={...renderer.info.memory};diag.cachedScenes=cache.size;diag.playbackToken=request?.token;diag.loading=loading;diag.sceneKey=view.furniture?.model||character.model;diag.sceneAction=view.actionId;
 if(window.petMeasureFraming){view.camera.updateMatrixWorld(true);const box=visiblePoseBounds(view.root,.003,false),p=new THREE.Box3();for(const x of [box.min.x,box.max.x])for(const y of [box.min.y,box.max.y])for(const z of [box.min.z,box.max.z])p.expandByPoint(new THREE.Vector3(x,y,z).project(view.camera));window.petFramingDiagnostics={zoom:view.camera.zoom,centerY:view.camera.position.y,min:p.min.toArray(),max:p.max.toArray()};}
 if(request?.step&&!loading&&!request.continuous){if(inGap){gapElapsed+=real;if(gapElapsed>=request.step.gap){const token=request.token;request=undefined;view.finished=false;api.playbackEvent(token,'done');}}else{elapsed+=real;if(view.finished||(request.step.mode==='seconds'&&elapsed>=request.step.value)){view.hold();inGap=true;gapElapsed=0;api.playbackEvent(request.token,'gap');if(request.step.gap===0){const token=request.token;request=undefined;view.finished=false;api.playbackEvent(token,'done');}}}}
 else if(!loading&&!request?.step&&view.finished&&!view.furniture){view.finished=false;view.play('idle',settings,true);api.activity('idle');}
}
async function start(){const init=await api.init();settings=init.settings;if(init.error||!init.character)throw Error(init.error||'缺少角色');character=init.character;view=await ensure(init.furniture?.id);ready=true;resize();status.hidden=true;view.orientation(settings,0,false);api.activity('idle');setHit(false);requestAnimationFrame(frame);}
void start().catch(e=>{message.textContent=String(e);status.hidden=false;window.petDiagnostics.error=String(e);api.report(String(e));});
