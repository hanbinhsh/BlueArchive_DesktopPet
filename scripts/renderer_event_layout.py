"""Reconcile legacy renderer event indices with the current original prefab."""
LAYOUTS={
    # CH0238 clips address the two authored face meshes as 7/8. The current
    # prefab hierarchy has them at 6/7; index 8 is now the halo renderer.
    # Preserve the original event times/indices and resolve named faces here.
    'chiaki':{7:'CH0238_Face01',8:'CH0238_Face02'},
    'juri_parttime':{6:'CH0286_Face_Outline',7:'CH0286_Face01_Outline'},
}
def renderer_event_layout(character,names):
    result=list(names)
    for index,name in LAYOUTS.get(character,{}).items():
        while len(result)<=index:result.append('')
        result[index]=name
    return result
