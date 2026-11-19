"""Character-owned particle roots restart with their authored animation segments."""
from timeline_visibility import boolean_curves

def phone_controls(metadata, track, group, names):
    result=[]
    for segment in track['clips']:
        end=segment['start']+segment['duration']
        for curve in boolean_curves(metadata, {'clips':[segment]}):
            name=curve['path'].split('/')[-1]
            if name not in names or curve['attribute']!='m_IsActive':continue
            keys=curve['keys']
            for index,(start,active) in enumerate(keys):
                stop=min(end,keys[index+1][0] if index+1<len(keys) else end)
                if active<.5 or stop<=start:continue
                result.append({'parents':[group],'track':'Character-owned phone',
                    'prefab':name+'__existing','existing':True,'restartOnActivation':True,
                    'bindingResolved':True,'exposedReference':None,'binding':name,
                    'start':start,'duration':stop-start,'clipIn':0,'speed':segment['speed'],'seed':0})
    return result
