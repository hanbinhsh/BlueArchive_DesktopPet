import test from 'node:test';
import assert from 'node:assert/strict';
import { fitWindow, normalizeSettings, validateCharacter, mouthTileAt, mouthStateAt, mouthOffset, mouthTransform, validMouthTile } from '../src/shared';
import { readFileSync } from 'node:fs';

test('fractional mouth origins use exact defaults and grid-aligned explicit/mirrored events',()=>{
 const spec={material:'mouth',defaultTile:401,columns:8,rows:8,baseUV:[.12,.5] as [number,number],events:{}};
 assert.deepEqual(mouthTransform(spec,[],0),{tile:401,flipped:false,x:0,y:0});
 const regular=mouthTransform(spec,[{time:0,tile:402}],1);
 assert.ok(Math.abs((.12+regular.x)-.25)<1e-8);
 const mirror=mouthTransform(spec,[{time:0,tile:402,flipped:true}],1);
 assert.ok(Math.abs((-.12+mirror.x)-.375)<1e-8);
 assert.deepEqual(mouthTransform(spec,[{time:0,tile:402},{time:1,tile:401,reset:true}],1),{tile:401,flipped:false,x:0,y:0});
 assert.deepEqual(mouthTransform(spec,[{time:.03,tile:401,reset:true}],0,true),{tile:401,flipped:false,x:0,y:0});
});

test('both original Hina costumes address their official 4x4 mouth atlas',()=>{
 for(const id of ['hina','hina_swimsuit']){
  const c=validateCharacter(JSON.parse(readFileSync(`characters/${id}/character.json`,'utf8'))),m=c.mouth!;
  assert.equal(m.columns,4);assert.equal(m.rows,4);assert.equal(m.defaultTile,300);
  assert.deepEqual(mouthOffset(101,m.defaultTile,m.columns,m.rows),{x:.25,y:.5});
  for(const events of Object.values(m.events))for(const e of events){assert.ok(e.tile%100<4);assert.ok(Math.floor(e.tile/100)<4);}
 }
});

test('looping furniture retains the authored last mouth through the first-frame event gap',()=>{
  const events=[{time:1/30,tile:306,flipped:true}];
  assert.deepEqual(mouthStateAt(events,0,300,false),{tile:300,flipped:false});
  assert.deepEqual(mouthStateAt(events,0,300,true),{tile:306,flipped:true});
  assert.deepEqual(mouthStateAt(events,.04,300,true),{tile:306,flipped:true});
  assert.deepEqual(mouthStateAt([],0,401,true),{tile:401,flipped:false});
  assert.deepEqual(mouthStateAt([{time:0,tile:402},{time:2,tile:605}],0,401,true),{tile:402,flipped:false});
});

test('action framing rejects invalid camera projections and unknown action ids', () => {
  const c = JSON.parse(readFileSync('characters/izuna/character.json', 'utf8'));
  assert.equal(validateCharacter(c).framing?.actions?.victory.zoom, .62);
  for (const view of [{zoom:0,centerY:1},{zoom:Infinity,centerY:1},{zoom:.5,centerY:NaN}]) {
    assert.throws(() => validateCharacter({...c,framing:{actions:{victory:view}}}));
  }
  assert.throws(() => validateCharacter({...c,framing:{actions:{missing:{zoom:.5,centerY:1}}}}));
});
test('expanded action catalogs accept full libraries and reject malformed metadata', () => {
  const c = JSON.parse(readFileSync('characters/serika/character.json', 'utf8'));
  // This test replaces the action library, so its fixture cannot retain camera
  // references to actions belonging to the installed character's library.
  delete c.framing;
  const actions = Array.from({length:80},(_,i)=>({id:`extra_${i}`,label:`动作 ${i}`,clip:`clip_${i}`,category:'战斗',sourceName:`Original_Attack_${i}`}));
  assert.equal(validateCharacter({...c,actions}).actions?.length,80);
  assert.throws(()=>validateCharacter({...c,actions:[{...actions[0],category:'untrusted'}]}));
  assert.throws(()=>validateCharacter({...c,actions:[{...actions[0],sourceName:42}]}));
  assert.throws(()=>validateCharacter({...c,actions:Array.from({length:513},(_,i)=>({...actions[0],id:`extra_${i}`}))}));
});
test('recovers a pet from a disconnected monitor into the remaining work area', () => {
  assert.deepEqual(fitWindow({ x: 2200, y: 500 }, 420, 406, [{ x: 0, y: 0, width: 1920, height: 1040 }]), { x: 1500, y: 500 });
});
test('keeps negative-coordinate displays and clamps windows to their work area', () => {
  assert.deepEqual(fitWindow({ x: -1900, y: 900 }, 420, 406, [{ x: 0, y: 0, width: 1920, height: 1040 }, { x: -1920, y: 0, width: 1920, height: 1080 }]), { x: 0, y: 634 });
  assert.deepEqual(fitWindow({ x: -1900, y: 100 }, 420, 406, [{ x: 0, y: 0, width: 1920, height: 1040 }, { x: -1920, y: 0, width: 1920, height: 1080 }]), { x: -1900, y: 100 });
});
test('invalid settings cannot introduce nonfinite window geometry', () => {
  const settings = normalizeSettings({ size: Infinity, yaw: NaN, position: { x: NaN, y: 12 } });
  assert.equal(settings.size, 280); assert.equal(settings.yaw, 0); assert.equal(settings.position, null);
  assert.equal(normalizeSettings({ size: 99999 }).size, 480);
});
test('character manifests reject path traversal and missing interaction', () => {
  const valid = { id: 'serika', name: '芹香', model: 'model.glb', source: { url: 'https://example.com', description: 'test source' }, scale: 1, yaw: 0, animations: { idle: 'Idle', interact: 'Touch' } };
  assert.equal(validateCharacter(valid).id, 'serika');
  assert.throws(() => validateCharacter({ ...valid, model: '../model.glb' }));
  assert.throws(() => validateCharacter({ ...valid, animations: { idle: 'Idle' } }));
});

test('furniture packs reject escaping paths, duplicate actions and invalid clocks', () => {
  const valid = { id:'test', name:'测试', model:'model.glb', source:{url:'https://example.com',description:'test'}, scale:1, yaw:0, animations:{idle:'idle',interact:'interact'} };
  const furniture = { id:'f1', name:'家具', model:'f1.glb', clip:'f1', duration:3, mouthEvents:[{time:0,tile:0}] };
  assert.equal(validateCharacter({...valid,furniture:[furniture]}).furniture?.length,1);
  for (const bad of [{...furniture,model:'../model.glb'},{...furniture,duration:Infinity},{...furniture,yaw:NaN},{...furniture,mouthEvents:[{time:NaN,tile:0}]}]) assert.throws(()=>validateCharacter({...valid,furniture:[bad]}));
  assert.throws(()=>validateCharacter({...valid,furniture:[furniture,furniture]}));
});
test('official mouth events follow clip time, reset on replay, and address the atlas from its bottom row', () => {
  const c = validateCharacter(JSON.parse(readFileSync('characters/serika/character.json', 'utf8')));
  const events = c.mouth!.events[c.animations.interact];
  assert.deepEqual(events.map(e => e.tile), [402, 701, 703, 602, 402]);
  assert.equal(mouthTileAt(events, .1, 402), 402);
  assert.equal(mouthTileAt(events, .2, 402), 701);
  assert.equal(mouthTileAt(events, .9, 402), 703);
  assert.equal(mouthTileAt(events, 1.2, 402), 602);
  assert.equal(mouthTileAt(events, 3, 402), 402);
  assert.equal(mouthTileAt(events, 0, 402), 402);
  assert.deepEqual(mouthOffset(701, 402), { x: -.125, y: -.375 });
  assert.deepEqual(mouthOffset(303, 203, 4, 4), { x: 0, y: -.25 });
  assert.equal(validMouthTile(708), false);
  assert.throws(() => validateCharacter({ ...c, mouth: { ...c.mouth, events: { test: [{ time: -1, tile: 402 }] } } }));
  assert.throws(() => validateCharacter({ ...c, actions: [c.actions![0], c.actions![0]] }));
});

test('mirrored official mouth events stay inside the requested tile and reset on the next normal event', () => {
  const events = [{time:0,tile:602,flipped:true},{time:1,tile:404}];
  assert.deepEqual(mouthStateAt(events,.5,601),{tile:602,flipped:true});
  assert.deepEqual(mouthStateAt(events,1,601),{tile:404,flipped:false});
  assert.deepEqual(mouthStateAt([],2,601),{tile:601,flipped:false});
  const offset=mouthOffset(602,601,8,8,true);
  // Geometry's base tile spans [1/8,2/8]; flip into tile column 2, not column 1.
  assert.equal(-1/8+offset.x,3/8);assert.equal(-2/8+offset.x,2/8);
  assert.equal(offset.y,0);
});
