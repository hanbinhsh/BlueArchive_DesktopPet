"""Deterministic emission times from Unity's rate-over-time curves."""
import math
import heapq

def particle_random(seed,key):
    h=seed&0xffffffff
    for c in key:h=((h^ord(c))*16777619)&0xffffffff
    h=((h^(h>>16))*0x21f0aaad)&0xffffffff
    h=((h^(h>>15))*0x735a2d97)&0xffffffff
    return ((h^(h>>15))&0xffffffff)/4294967296

def initial_scalar(c,seed,key):
    mode=c.get('minMaxState',0);r=particle_random(seed,key)
    def first(name):
        keys=c.get(name,{}).get('m_Curve',[])
        return keys[0]['value'] if keys else 0
    if mode==1:return c['scalar']*first('maxCurve')
    if mode==2:
        a=c['minScalar']*first('minCurve');b=c['scalar']*first('maxCurve')
        return a+(b-a)*r
    if mode==3:return c['minScalar']+(c['scalar']-c['minScalar'])*r
    return c.get('scalar',0)

def limit_births(schedule,initial,delay):
    """Drop births while Unity's non-ring particle pool is full."""
    maximum=initial['maxNumParticles'];ends=[];result=[]
    def born(row):return row[0]+initial_scalar(delay,row[3],'delay')
    for row in sorted(schedule,key=born):
        birth=born(row)
        while ends and ends[0]<=birth+1e-7:heapq.heappop(ends)
        if len(ends)>=maximum:continue
        life=max(.0001,initial_scalar(initial['startLifetime'],row[3],'particle.InitialModule.startLifetime'))
        heapq.heappush(ends,birth+life);result.append(row)
    return result

def burst_times(burst, duration):
    """A zero cycle count repeats until emission stops, not zero emissions."""
    start=burst['time'];interval=burst['repeatInterval'];count=burst['cycleCount']
    if count:
        return [start+k*interval for k in range(count)]
    if interval<=0 or not math.isfinite(interval):
        raise ValueError('Indefinite burst requires a positive repeat interval')
    # Float32 source intervals can straddle the exact duration boundary.
    count=max(0,math.ceil((duration-start)/interval-1e-6))
    if count>100000:raise ValueError('Burst schedule exceeds safe adaptation bound')
    return [start+k*interval for k in range(count)]

def evaluate(c, t):
    if c.get('minMaxState', 0) == 0:
        return c.get('scalar', 0)
    if c['minMaxState'] != 1:
        raise ValueError('Random emission-rate curves require a source RNG policy')
    keys = c.get('maxCurve', {}).get('m_Curve', [])
    if not keys:
        return 0
    value = keys[-1]['value']
    if t <= keys[0]['time']:
        value = keys[0]['value']
    else:
        for a, b in zip(keys, keys[1:]):
            if t >= b['time']:
                continue
            dt = b['time'] - a['time']; u = (t-a['time']) / dt
            x, y = a['outSlope'], b['inSlope']
            if x is None or y is None or not math.isfinite(x+y):
                value = a['value']
            else:
                value = (2*u**3-3*u*u+1)*a['value']+(u**3-2*u*u+u)*dt*x+(-2*u**3+3*u*u)*b['value']+(u**3-u*u)*dt*y
            break
    return c['scalar'] * value

def emission_times(curve, begin, end, period, frequency=240, seed=None):
    if curve.get('minMaxState', 0) == 0:
        rate = curve.get('scalar', 0)
        return [n/rate for n in range(math.floor(begin*rate)+1, math.ceil(end*rate))] if rate > 0 else []
    count = 0.; threshold = 1.; births = []
    if curve.get('minMaxState')==3 and seed is None:
        raise ValueError('Random emission requires an explicit deterministic seed')
    steps = math.ceil((end-begin)*frequency)
    for k in range(steps):
        a = begin+k/frequency; b = min(end, a+1/frequency)
        if curve.get('minMaxState')==3:
            # Unity's native probe shows a fluctuating integrated rate, not
            # one randomly chosen fixed interval for the whole system. Use
            # stable 60 Hz samples; no claim to duplicate its private RNG.
            tick=math.floor((a+b)*.5*60)
            random=particle_random(seed,'emission-rate:'+str(tick))
            rate=max(0.,curve['minScalar']+(curve['scalar']-curve['minScalar'])*random)
        else:rate = max(0., evaluate(curve, ((a+b)*.5 % period)/period))
        following = count+rate*(b-a)
        while threshold <= following and rate > 0:
            birth = a+(threshold-count)/rate
            if birth < end: births.append(birth)
            threshold += 1
        count = following
    return births
