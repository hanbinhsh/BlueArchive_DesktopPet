import {readFileSync,writeFileSync} from 'node:fs';
import {validateCharacter} from '../src/shared';
const ids=Object.keys(JSON.parse(readFileSync('scripts/roster-wave12.json','utf8')));
const results=ids.map(id=>{
  const character=validateCharacter(JSON.parse(readFileSync(`.assets/expanded-ready/${id}/character.json`,'utf8')));
  return {id:character.id,actions:character.actions?.length,valid:true};
});
writeFileSync('test-results/wave12-manifests.json',JSON.stringify(results,null,2));
console.log('Validated',results.length,'character manifests');
