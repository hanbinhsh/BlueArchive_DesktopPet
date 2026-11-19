import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeSettings,roamLimits} from '../src/shared';
test('old profiles keep automatic activity off; untrusted settings cannot produce runaway movement',()=>{
 const old=normalizeSettings({});assert.equal(old.randomIdle,false);assert.equal(old.roaming,false);
 const s=normalizeSettings({randomInterval:NaN,roamRadius:99999,roamSpeed:Infinity,favorites:['iori:interact','iori:interact','../../x','bad']});
 assert.equal(s.randomInterval,30);assert.equal(s.roamRadius,4000);assert.equal(s.roamSpeed,35);assert.deepEqual(s.favorites,['iori:interact']);
 assert.equal(normalizeSettings({randomInterval:-2,roamSpeed:-50}).roamSpeed,10);
});
test('roaming stays inside its radius and negative-coordinate monitor work area',()=>{
 assert.deepEqual(roamLimits(-1300,160,{x:-1920,y:0,width:1920,height:1080},540),{min:-1460,max:-1140});
 assert.deepEqual(roamLimits(-550,160,{x:-1920,y:0,width:1920,height:1080},540),{min:-710,max:-540});
 assert.deepEqual(roamLimits(0,160,{x:0,y:0,width:300,height:500},540),{min:0,max:0});
 assert.deepEqual(roamLimits(1500,4000,{x:0,y:0,width:3840,height:2160},420),{min:0,max:3420});
});
