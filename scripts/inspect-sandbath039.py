"""Identify the authored decorative faces separately from the animated partner."""
from pathlib import Path
import json
from glb import load
p=Path('characters/ibuki_swimsuit/f211311_1.glb');d,b=load(p)
m=next(m for m in d['materials']if m.get('name')=='my_event094_sandbath')
im=d['images'][d['textures'][m['pbrMetallicRoughness']['baseColorTexture']['index']]['source']];view=d['bufferViews'][im['bufferView']];a=view.get('byteOffset',0)
Path('.assets/sandbath039-native-atlas.png').write_bytes(b[a:a+view['byteLength']])
print('Extracted the unchanged furniture texture atlas')
