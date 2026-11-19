import { readdirSync, readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
const root = path.resolve('characters');
const results = [];
for (const dir of readdirSync(root, { withFileTypes: true }).filter(d => d.isDirectory())) {
  const manifest = JSON.parse(readFileSync(path.join(root, dir.name, 'character.json'), 'utf8'));
  if (!/^[\w.-]+\.glb$/i.test(manifest.model)) throw new Error('Invalid GLB filename');
  const bytes = readFileSync(path.join(root, dir.name, manifest.model));
  if (bytes.toString('ascii', 0, 4) !== 'glTF' || bytes.readUInt32LE(4) !== 2 || bytes.readUInt32LE(8) !== bytes.length) throw new Error('Invalid GLB header');
  const gltf = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)).toString('utf8'));
  if ([...(gltf.images || []), ...(gltf.buffers || [])].some(x => x.uri)) throw new Error('External resources are forbidden');
  const animations = (gltf.animations || []).map(a => ({ name: a.name, channels: a.channels.length }));
  for (const role of ['idle', 'interact']) if (!animations.some(a => a.name === manifest.animations[role] && a.channels > 0)) throw new Error(`Missing ${role} animation`);
  for (const action of manifest.actions || []) if (!animations.some(a => a.name === action.clip && a.channels > 0)) throw new Error(`Missing menu action ${action.id}`);
  if (manifest.mouth) {
    if (!gltf.materials.some(m => m.name === manifest.mouth.material && m.pbrMetallicRoughness?.baseColorTexture)) throw new Error('Missing mouth atlas');
    const original = gltf.scenes[0].extras.BAAD_unity_animation.clips;
    for (const [clip, events] of Object.entries(manifest.mouth.events)) {
      const metadata = original.find(c => c.track === clip);
      const expected=metadata?.events.filter(e=>['SetMouthTile','SetHorizontallyFlippedMouthTile','SetMouthTileToDefault'].includes(e.function)).map(e=>({time:e.time,tile:e.function==='SetMouthTileToDefault'?manifest.mouth.defaultTile:Math.abs(e.int),...e.function==='SetHorizontallyFlippedMouthTile'?{flipped:true}:{}}));
      const normalized=events.map(({reset,...e})=>e);
      if (!metadata || JSON.stringify(expected) !== JSON.stringify(normalized) || events.some((e,i)=>e.reset!==undefined&&(e.reset!==true||metadata.events.filter(e=>['SetMouthTile','SetHorizontallyFlippedMouthTile','SetMouthTileToDefault'].includes(e.function))[i]?.function!=='SetMouthTileToDefault'))) throw new Error(`Mouth events differ from official export: ${clip}`);
    }
  }
  if (!gltf.skins?.length || !gltf.meshes?.length || !gltf.images?.length) throw new Error('Missing skeleton, meshes or textures');
  results.push({ id: manifest.id, bytes: bytes.length, sha256: crypto.createHash('sha256').update(bytes).digest('hex'), meshes: gltf.meshes.length, skins: gltf.skins.length, images: gltf.images.length, animations, source: manifest.source });
}
if (!results.length) throw new Error('No verified character packs installed');
mkdirSync('test-results', { recursive: true });
writeFileSync('test-results/assets.json', JSON.stringify(results, null, 2));
console.log(JSON.stringify(results, null, 2));
