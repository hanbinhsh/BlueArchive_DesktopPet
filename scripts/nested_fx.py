"""Map child director windows from their shared root clock to furniture time."""

def window_control(parent, root, window):
    # Sibling activation tracks all use the director's clock, not the clipIn
    # of an already activated ancestor. Clamp visibility without losing the
    # particle's elapsed time when its activation began before its parent.
    begin=root['start']+(window['start']-root['clipIn'])/root['speed']
    end=begin+window['duration']/root['speed']
    start=max(parent['start'],begin)
    end=min(parent['start']+parent['duration'],end)
    if end<=start:return None
    speed=root['speed']*window['speed']
    return {**parent,'start':start,'duration':end-start,
            'clipIn':window['clipIn']+(start-begin)*speed,'speed':speed,
            'existing':False,'propertyClock':root}
