"""Translate the draw state of selected props with verified source materials."""

def adapt_prop_material(material):
    extras = material.get('extras') or {}
    smoke = extras.get('BA_smokeFx')
    particle = extras.get('BA_cafeParticle')
    if (smoke and smoke.get('kind') == 'step' and 'maskTexture' in smoke
            and particle and (particle.get('texture') or {}).get('name', '').startswith('FX_TEX_CH0347_Sandart')):
        # Source Sandart step masks have Unity m_ColorSpace = 1 (sRGB); Unity's
        # authored CustomData threshold curve expects hardware sRGB->linear
        # decoding when comparing mask.r against threshold.
        smoke['maskTexture']['srgb'] = True
        return
    name = material['name']
    factors = material['pbrMetallicRoughness']
    if name == 'CH0100_Table_02':
        # The glass samples an opaque patch of the shared tray atlas. Keep
        # the opaque liquid submesh, but approximate the glass shader's
        # transparency independently of the atlas alpha.
        factors['baseColorFactor'] = [0.9386792, 0.9924694, 1, 0.30]
    elif name == 'CH0123_Alpha':
        factors['baseColorFactor'] = [1, 1, 1, 0.227451]
    elif name == 'CH0123_Alpha2':
        factors['baseColorFactor'] = [0.7729619, 0.8490566, 0.8112414, 0.3607843]
    elif name == 'my_seahouse_01_tableitems _a':
        # ENV_ALPHA_MODE uses the source tint alpha. A 0.5 cutoff applied
        # after the 0.357 multiplier discards the entire cup wall.
        factors['baseColorFactor'] = [1, 1, 1, 0.35686275]
    elif name == 'my_seahouse_01_tableitems':
        # The opaque slot uses this atlas's RGB without its data alpha.
        material['alphaMode'] = 'OPAQUE'
        material.pop('alphaCutoff', None)
        return
    elif name not in {'my_hotsprings_woodenbathtub 1', 'my_event094_sandbath_alpha'}:
        return

    material['alphaMode'] = 'BLEND'
    material['doubleSided'] = False
    material.pop('alphaCutoff', None)
    material.setdefault('extras', {})['BA_depthWrite'] = False
