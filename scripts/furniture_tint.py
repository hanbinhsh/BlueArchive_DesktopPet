"""Use the declared MX/C-Simple tint, rather than an unused legacy _Color."""
def adapt_simple_tint(original,material):
    colors=dict(original.m_SavedProperties.m_Colors)
    if '_Tint' not in colors:return False
    shader=original.m_Shader.read().m_ParsedForm.m_Name
    if shader not in ['MX/C-Simple','MX/C-Simple-Transparent']:return False
    tint=[getattr(colors['_Tint'],k)for k in 'rgba']
    material['pbrMetallicRoughness']['baseColorFactor']=[max(0,min(1,x))for x in tint]
    material.setdefault('extras',{}).update(BA_sourceShader=shader,BA_sourceColorProperty='_Tint',BA_sourceTint=tint)
    if shader=='MX/C-Simple-Transparent':
        material['alphaMode']='BLEND';material['extras']['BA_depthWrite']=False
    return True
