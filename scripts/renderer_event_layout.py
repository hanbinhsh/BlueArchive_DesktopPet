"""Reconcile legacy renderer event indices with the current original prefab."""
LAYOUTS={
    # CH0192's authored events retain indices 9/10 from the earlier renderer layout.
    'junko_newyear':{9:'CH0192_Body_Face01_Outline',10:'CH0192_Body_Face_Outline'},
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
    # CH0088 clips address CH0088_Weapon at prefab child index 2 (bone_root is
    # child 0). Enumerating renderers shifted index 2 onto CH0088_Halo, hiding
    # her halo in Cafe Idle/Reaction instead of her flamethrower.
    'megu':{2:'CH0088_Weapon'},
    # CH0172 Cafe clips address CH0172_CafeOnly child indices 4/5/6
    # (Hand01/Hand02/strategytable_prop_02). On CH0172, index 5 is CH0172_Halo
    # and index 6 is absent; map all three explicitly so Halo is never hidden.
    'niko':{4:'CH0172_Hand01_Mesh',5:'CH0172_Hand02_Mesh',6:'my_event091_strategytable_prop_02'},
}
def renderer_event_layout(character,names):
    result=list(names)
    for index,name in LAYOUTS.get(character,{}).items():
        while len(result)<=index:result.append('')
        result[index]=name
    return result
