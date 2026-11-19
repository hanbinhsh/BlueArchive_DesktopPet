"""Preserve Unity renderer events and boolean curves, not invented expressions."""
def attach_visibility(doc, renderer_names, defaults=None, ignore_missing=False, ignored_events=()):
    nodes = {n['name']: i for i,n in enumerate(doc['nodes'])}
    clips = {}
    for clip in doc['scenes'][0]['extras']['BAAD_unity_animation']['clips']:
        tracks = {}
        for curve in clip.get('unity_curves', []):
            name = curve['path'].split('/')[-1]
            if curve['attribute'] in ('m_IsActive', 'm_Enabled') and name in nodes:
                tracks[name] = [[k[0], k[1] >= .5] for k in curve['keys']]
        for event in clip['events']:
            if event['function'] not in ('AniEvt_EnableChildRenderer','AniEvt_DisableChildRenderer'): continue
            ignored=next((e for e in ignored_events if e['clip']==clip['name'] and e['index']==event['int'] and e['function']==event['function'] and abs(e['time']-event['time'])<1e-6),None)
            if ignored:
                doc.setdefault('extras',{}).setdefault('BA_unresolved_legacy_renderer_events',[]).append(ignored)
                continue
            if ignore_missing and not 0 <= event['int'] < len(renderer_names): continue
            name = renderer_names[event['int']]
            if ignore_missing and name not in nodes: continue
            if name not in nodes: raise ValueError('Missing renderer: '+name)
            tracks.setdefault(name, []).append([event['time'], event['function']=='AniEvt_EnableChildRenderer'])
        clips[clip['track']] = [{'node':nodes[n], 'keys':sorted(keys)} for n,keys in tracks.items()]
    doc['scenes'][0]['extras']['BA_pet_visibility'] = {'defaults': {str(nodes[n]):v for n,v in (defaults or {}).items() if n in nodes}, 'clips':clips}
