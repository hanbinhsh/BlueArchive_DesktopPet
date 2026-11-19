"""Reconcile legacy renderer event indices with the current original prefab."""
LAYOUTS={
    # CH0238 clips address the two authored face meshes as 7/8. The current
    # prefab hierarchy has them at 6/7; index 8 is now the halo renderer.
    # Preserve the original event times/indices and resolve named faces here.
    'chiaki':{7:'CH0238_Face01',8:'CH0238_Face02'},
    'juri_parttime':{6:'CH0286_Face_Outline',7:'CH0286_Face01_Outline'},
    # CH0123 clips address the two body meshes at their prefab child indices
    # 3/4 (CH0123_CutIn_Body / CH0123_Body). Enumerating renderers alone shifted
    # indices 3/4 onto CH0123_Prop and CH0123_Halo, causing yukata z-fighting
    # and hiding her handheld onsen props in cafe/skill clips.
    'shigure_onsen':{3:'CH0123_CutIn_Body',4:'CH0123_Body'},
    # CH0159 clips address CH0159_Blanket_Mesh at prefab child index 3 (bone_root
    # is child 0). Enumerating renderers alone shifted index 3 onto CH0159_Halo,
    # hiding her halo instead of her lap blanket in CH0159_Formation_Pickup.
    'himari':{3:'CH0159_Blanket_Mesh'},
}
def renderer_event_layout(character,names):
    result=list(names)
    for index,name in LAYOUTS.get(character,{}).items():
        while len(result)<=index:result.append('')
        result[index]=name
    return result
