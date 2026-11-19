"""Decode the authored streamed/dense/constant Unity clip curves (no generated poses)."""
import struct,bisect,math

def curves(clip):
 data=clip['m_MuscleClip']['m_Clip']['data'];stream=data['m_StreamedClip'];raw=struct.pack('<'+'I'*len(stream['data']),*stream['data']);offset=0;result={}
 while offset<len(raw):
  time,count=struct.unpack_from('<fI',raw,offset);offset+=8
  for _ in range(count):
   index,*coeff=struct.unpack_from('<I4f',raw,offset);offset+=20
   result.setdefault(index,[]).append((time,coeff))
 dense=data['m_DenseClip'];start=stream.get('curveCount',max(result,default=-1)+1)
 for i in range(dense['m_CurveCount']):
  values=[dense['m_SampleArray'][f*dense['m_CurveCount']+i] for f in range(dense['m_FrameCount'])]
  result[start+i]=[(dense['m_BeginTime']+f/dense['m_SampleRate'],[0,0,(values[f+1]-v)*dense['m_SampleRate'] if f+1<len(values) else 0,v]) for f,v in enumerate(values)]
 start+=dense['m_CurveCount']
 for i,value in enumerate(data['m_ConstantClip']['data']):result[start+i]=[(0,[0,0,0,value])]
 return result

def sample(keys,time):
 index=max(0,bisect.bisect_right([k[0] for k in keys],time)-1);start,c=keys[index]
 if start < -1e20:return c[3]
 dt=max(0,time-start);return ((c[0]*dt+c[1])*dt+c[2])*dt+c[3]

def euler_quaternion(v):
 x,y,z=[n*math.pi/360 for n in v];sx,cx=math.sin(x),math.cos(x);sy,cy=math.sin(y),math.cos(y);sz,cz=math.sin(z),math.cos(z)
 # Unity ZXY intrinsic == Three YXZ; reflect source X into glTF.
 return [sx*cy*cz+cx*sy*sz,-(cx*sy*cz-sx*cy*sz),-(cx*cy*sz-sx*sy*cz),cx*cy*cz+sx*sy*sz]
