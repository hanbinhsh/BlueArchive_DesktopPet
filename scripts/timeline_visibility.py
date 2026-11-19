"""Compose boolean curves across ordered Timeline clips without losing repeats."""
def boolean_curves(metadata, track):
    clips={c['name']:c for c in metadata};result={}
    segments=sorted(track['clips'],key=lambda c:c['start'])
    for index, segment in enumerate(segments):
        start=segment['start'];end=start+segment['duration']
        if index+1<len(segments):end=min(end,segments[index+1]['start'])
        for curve in clips[segment['name']].get('unity_curves',[]):
            if curve.get('attribute') not in ('m_IsActive','m_Enabled') or not curve['keys']:continue
            key=(curve['path'],curve['attribute'])
            target=result.setdefault(key,{**curve,'keys':[]})
            source=sorted(curve['keys'],key=lambda k:k[0])
            before=[k for k in source if k[0]<=segment['clipIn']+1e-7]
            target['keys'].append([start,(before[-1] if before else source[0])[1]])
            for k in source:
                time=start+(k[0]-segment['clipIn'])/segment['speed']
                # The next clip owns the shared boundary. Exported float endpoints
                # can extend ~1e-6 past it and must not disable the next phone.
                if start+1e-6<time<end-1e-6:target['keys'].append([time,k[1]])
    for curve in result.values():
        keys=[]
        for time,value in sorted(curve['keys'],key=lambda k:k[0]):
            if keys and abs(time-keys[-1][0])<1e-6:keys[-1]=[time,value]
            elif not keys or value!=keys[-1][1]:keys.append([time,value])
        curve['keys']=keys
    return list(result.values())
