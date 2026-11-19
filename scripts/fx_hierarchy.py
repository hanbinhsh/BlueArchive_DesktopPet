"""Preserve authored rotations when cloning a sub-emitter under its trigger."""
def multiply(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def annotate(n,rotation=(0,0,0,1),scale=(1,1,1)):
 n['_worldRotation']=multiply(rotation,n['rotation']);n['_worldScale']=[a*b for a,b in zip(scale,n['scale'])]
 for c in n['children']:annotate(c,n['_worldRotation'],n['_worldScale'])
def reparent(child,parent):
 q=parent['_worldRotation'];child['rotation']=multiply([-q[0],-q[1],-q[2],q[3]],child['_worldRotation'])
 child['scale']=[a/b for a,b in zip(child['_worldScale'],parent['_worldScale'])]
 child['position']=[0,0,0]
