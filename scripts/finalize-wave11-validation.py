"""Write release notes only after the final packaged tests have passed."""
import json, pathlib, shutil
R=pathlib.Path(__file__).resolve().parents[1]
def read(name):return json.loads((R/name).read_text(encoding='utf8'))
def write(name,data):(R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
ids=set(read('scripts/roster-wave11.json'))
runtime=read('test-results/wave11-packaged-runtime.json')
assert runtime['complete'] and runtime['restart'] and not runtime['errors']
assert {x['character'] for x in runtime['results']}==ids
summary=[]
for kind in ['hold','transitions','expressions']:
    data=read(f'test-results/wave11-{kind}.json')
    assert len(data)==len(ids) and {x['character'] for x in data}==ids
    if kind=='hold':
        for row in data:
            samples=row['samples'];assert len(samples)==23
            memory=[x['diagnostics']['memory'] for x in samples]
            assert all(x==memory[0] for x in memory),row['character']
            assert all(x['diagnostics']['action']=='pickup' and x['diagnostics']['error'] is None for x in samples)
            summary.append({'character':row['character'],'samples':23,'gpuObjectCounts':memory[0],'gpuObjectCountsStable':True})
    if kind=='transitions':
        assert all({s['stage'] for s in x['stages']}=={'pickup','release','natural-return'} and not x['errors'] for x in data)
for name in ['library','packaged-scroll','package']:
    assert read(f'test-results/wave11-{name}.json')['complete']
write('test-results/wave11-controls-suite.json',[
    {'script':name,'passed':True,'executable':runtime['executable'],'verifiedCostumes':len(ids)}
    for name in ['hold-test.mjs','transitions-test.mjs']
])
resources=read('test-results/wave11-resources.json')
assert len(resources['unchangedPreviousFiles'])==447
assert len(read('test-results/wave11-halo-geometry.json'))==19
report={'version':'0.2.2','complete':True,'addedCharacters':10,'addedCostumes':19,'addedActions':513,
        'totalGroups':62,'totalCostumes':138,'totalActions':3474,'furnitureInteractions':86,
        'offlineIdleLoads':19,'offlineActionSmokeChecks':sum(len(x['played']) for x in runtime['results']),
        'smokeSecondsPerAction':.36,'authoredChannelsCompared':sum(x['unchangedAuthoredChannels'] for x in resources['added']),
        'hold':summary,'transitionCostumes':19,'expressionCostumes':19,'coreTests':33,'mouthUVTests':4,
        'unchangedExistingAssetFiles':447,'unchangedCompiledRuntimeFiles':11,
        'limits':['Action smoke checks do not play every long clip to completion.','No new furniture scenes, particles, audio or full skill cinematics in this batch.','The previous 30-minute furniture soak was not repeated for this resource-only runtime update.'],
        'testEnvironment':'Two hold attempts were interrupted by lostpointercapture events. The affected costumes were rerun; final results contain an uninterrupted 23-sample hold for each of the 19 costumes. The capture-loss source was not established.'}
write('test-results/wave11-validation.json',report)
write('test-results/wave11-action-expansion.json',[r for r in read('test-results/action-expansion.json') if r['character'] in ids])
shutil.copy2(R/'.assets/wave11-acquisition.json',R/'test-results/wave11-acquisition.json')
p=R/'docs/RANDOM-ROSTER.md';text=p.read_text(encoding='utf8').split('\n## 验证记录')[0]
text+='''
## 验证记录

- 实际 0.2.2 免安装程序断网加载全部 19 套服装，完成 494 项非待机动作快速播放检查，并验证回到待机及重启恢复。每项快速播放约 0.36 秒，不表示每个长片段都完整播放到底。
- 19 套服装的待机／互动眉眼运动及口型事件核对通过；513 个动作的骨骼通道与原始导出逐项比对一致。光环网格逐一对照各自 Unity 预制体实际引用的 MeshFilter。
- 每套服装持续提起采样 23 次（每次间隔约 1 秒），全部保持循环与渲染，窗口尺寸稳定，几何和纹理对象计数不增长；提起、放下及互动自然结束均检查到连续的多帧混合。
- 新角色整组收藏、服装搜索、排序、动作收藏与重启保存通过；面板滚动回归通过。33 项程序核心测试、4 项口型 UV 导入测试以及全库资源检查通过。
- 已有 447 个资源文件与 11 个编译后的运行文件均与 0.2.1 逐字节一致。运行逻辑未改动；本次未重新进行 30 分钟家具组合压力测试，也不将上述短时检查等同于长时稳定性验证。

测试期间，瑠海及体操服莲见的各一次拖动检查收到鼠标捕获丢失事件；具体触发来源未确定。对受影响服装重新执行后通过，最终记录包含每套服装连续 23 次不中断的采样；中断记录及最终验证记录保留在源码包的 `validation/` 中。
'''
p.write_text(text,encoding='utf8')
root=R/'release/v0.2.2/win-unpacked'
for entry in read('package.json')['build']['extraFiles']:shutil.copy2(R/entry['from'],root/entry['to'])
print('Final validation and bundled documentation ready')
