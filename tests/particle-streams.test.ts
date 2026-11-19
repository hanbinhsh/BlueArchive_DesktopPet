import test from 'node:test';
import assert from 'node:assert/strict';
import {particleShaderData} from '../src/particle-streams';
const data=[[1,2,3,4],[5,6,7,8]];
test('Custom2 without Custom1 occupies TEXCOORD1 after both UV sets',()=>{
 assert.deepEqual(particleShaderData([0,1,3,4,5,38],data),[[5,6,7,8],[0,0,0,0]]);
});
test('one UV set packs Custom1 across the first two TEXCOORD registers',()=>{
 assert.deepEqual(particleShaderData([0,1,3,4,34,38],data),[[3,4,5,6],[7,8,0,0]]);
});
test('both UV sets retain ordinary Custom1/Custom2 layout',()=>{
 assert.deepEqual(particleShaderData([0,1,3,4,5,34,38],data),data);
 assert.deepEqual(particleShaderData([0,1,3,4,5,34],data),[data[0],[0,0,0,0]]);
});
test('unadapted stream semantics preserve the legacy adapter',()=>{
 assert.equal(particleShaderData([0,4,8,34],data),data);
});
