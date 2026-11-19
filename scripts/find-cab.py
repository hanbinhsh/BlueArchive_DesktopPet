"""Find shared Unity dependencies in cached packs without decoding textures."""
import json, pathlib, struct, sys, zipfile, zlib
import lz4.block
ROOT = pathlib.Path(__file__).resolve().parents[1]
W = ROOT/'.assets'
def cab_names(raw):
    if not raw.startswith(b'UnityFS\0'): return []
    version = struct.unpack_from('>I',raw,8)[0]
    offset = 12
    for _ in range(2): offset = raw.index(b'\0',offset)+1
    size, packed, unpacked, flags = struct.unpack_from('>QIII',raw,offset)
    offset += 20
    if version >= 7: offset = (offset+15)//16*16
    if flags & 0x80: offset = size-packed
    data = raw[offset:offset+packed]
    if len(data) != packed: raise ValueError('Need full bundle header')
    codec = flags & 0x3f
    if codec in (2,3): data = lz4.block.decompress(data,uncompressed_size=unpacked)
    elif codec != 0: raise ValueError('Unsupported block-info compression')
    count = struct.unpack_from('>I',data,16)[0]
    offset = 20+count*10
    nodes = struct.unpack_from('>I',data,offset)[0]; offset += 4
    names = []
    for _ in range(nodes):
        offset += 20
        end = data.index(b'\0',offset)
        names.append(data[offset:end].decode().lower()); offset = end+1
    return names

if __name__ == '__main__':
    wanted = sys.argv[1].lower()
    catalog = {b['Name']:(p['PackName'],b) for p in json.loads((W/'catalog.json').read_text())['FullPatchPacks'] for b in p['BundleFiles']}
    for pack in (W/'packs').glob('*.zip'):
        with zipfile.ZipFile(pack) as archive:
            for name in archive.namelist():
                if not name.endswith('.bundle'): continue
                with archive.open(name) as stream: raw = stream.read(16384)
                try: names = cab_names(raw)
                except ValueError: names = cab_names(archive.read(name))
                if wanted not in names: continue
                raw = archive.read(name); item = catalog[name][1]
                assert len(raw) == item['Size'] and zlib.crc32(raw) == item['Crc']
                (W/'selected'/name).write_bytes(raw)
                evidence = W/'wave5-extra-dependencies.json'
                data = json.loads(evidence.read_text()) if evidence.exists() else []
                if not any(x['bundle']['Name'] == name for x in data): data.append({'pack':pack.name,'bundle':item})
                evidence.write_text(json.dumps(data,indent=2))
                print('FOUND',pack.name,name); sys.exit(0)
    print('Not in cached packs'); sys.exit(1)
