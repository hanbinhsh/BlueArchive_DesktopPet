"""Represent an authored static FX mesh with the shared material evaluator."""
import copy

def attach_static_particles(effect,duration):
 def walk(n):
  yield n
  for c in n['children']:yield from walk(c)
 if not any(n.get('staticRenderer') for n in walk(effect)):return
 # Some authored effects contain only MeshRenderers (the hot-spring water
 # layers). A neutral single-instance descriptor needs no particle sibling.
 prototype=next((n['particle'] for n in walk(effect) if n.get('particle')),{'InitialModule':{},'ShapeModule':{'enabled':False},'ClampVelocityModule':{'enabled':False}})
 for n in walk(effect):
  if not n.get('staticRenderer'):continue
  p=copy.deepcopy(prototype)
  for name,value in p.items():
   if name.endswith('Module') and isinstance(value,dict):value['enabled']=False
  c=lambda v:{'minMaxState':0,'scalar':v,'minScalar':v}
  initial=p['InitialModule'];initial.update(startLifetime=c(duration+1),startSpeed=c(0),gravityModifier=c(0),size3D=False,startSize=c(1),rotation3D=False,startRotation=c(0),startColor={'minMaxState':0,'maxColor':{'r':1,'g':1,'b':1,'a':1}},maxNumParticles=1)
  p.update(looping=False,prewarm=False,lengthInSec=duration+1,startDelay=c(0),simulationSpeed=1,moveWithTransform=0,ringBufferMode=0)
  p['EmissionModule']={'enabled':True,'rateOverTime':c(0),'m_Bursts':[{'time':0,'countCurve':c(1),'cycleCount':1,'repeatInterval':1,'probability':1}]}
  n['particle']=p;n['particleId']='static:'+n['path'];n['renderer'].update(m_RenderMode=4,m_RenderAlignment=2,m_Pivot={'x':0,'y':0,'z':0},m_Flip={'x':0,'y':0,'z':0})
