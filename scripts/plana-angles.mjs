import {_electron as electron} from 'playwright';
import path from 'node:path';
const env={...process.env,BA_TEST_DATA:path.resolve('test-results/roster-preview-profile')};delete env.ELECTRON_RUN_AS_NODE;
const app=await electron.launch({args:['.'],env});
try {const p=await app.firstWindow();await p.waitForFunction(()=>window.petDiagnostics?.frames>5);
for(const yaw of [-.65,-1.85,-2.4]){await p.evaluate(y=>window.pet.rotate(y),yaw);await p.waitForTimeout(300);await p.reload();await p.waitForFunction(()=>window.petDiagnostics?.frames>5);await p.screenshot({path:`test-results/plana-angle-${yaw}.png`,omitBackground:true});}}
finally{await app.close();}

