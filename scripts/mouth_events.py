"""Decode original mouth commands, including mirrored tiles and reset events."""

def normalize_repeat_uv(uv, wrap_u, wrap_v):
    """Canonicalize whole texture repeats without changing the sampled mouth."""
    result = dict(uv)
    for axis, wrap in [('x', wrap_u), ('y', wrap_v)]:
        if not 0 <= result[axis] < 1:
            if wrap != 0:  # Unity TextureWrapMode.Repeat
                raise ValueError(f'Out-of-range mouth UV requires verified Repeat sampling: {axis}={result[axis]}, wrap={wrap}')
            result[axis] %= 1
    return result
def mouth_events(clip, default_tile):
    result = []
    for e in clip['events']:
        fn = e['function']
        if fn not in ('SetMouthTile', 'SetHorizontallyFlippedMouthTile', 'SetMouthTileToDefault'): continue
        event = {'time': e['time'], 'tile': default_tile if fn == 'SetMouthTileToDefault' else abs(e['int'])}
        if fn == 'SetHorizontallyFlippedMouthTile': event['flipped'] = True
        if fn == 'SetMouthTileToDefault': event['reset'] = True
        result.append(event)
    return result
