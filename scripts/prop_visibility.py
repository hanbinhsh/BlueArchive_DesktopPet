"""Resolve scene-specific prop visibility lost when leaving the game runtime."""

def apply_prop_visibility(doc, character, timeline=None):
    if character != 'shigure_onsen':
        return
    visibility = doc['scenes'][0]['extras']['BA_pet_visibility']
    defaults = visibility['defaults']
    cutin = next(i for i, node in enumerate(doc['nodes'])
                 if node['name'] == 'CH0123_CutIn_Body' and 'mesh' in node)
    # The alternate body is used by the authored m_Enabled track in the
    # bath/cut-in. The ordinary body alone should render in the cafe.
    defaults[str(cutin)] = False

    if timeline == 'my_hotsprings_01_woodenbathtub_CH0123':
        # Both ducks are explicitly posed on the deck in Shigure's timeline.
        # The mesh ripple and particle ripple are ambient children of the
        # generic bath prefab, where the ducks sit in the water by default.
        suffixes = ('duck_01_Bubble', 'duck_02_Bubble')
        ripples = [i for i, node in enumerate(doc['nodes'])
                   if node['name'].startswith('furniture_') and node['name'].endswith(suffixes)]
        assert len(ripples) == 2, ripples
        for i in ripples:
            defaults[str(i)] = False
