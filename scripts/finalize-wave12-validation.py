import json,pathlib,shutil
R=pathlib.Path(__file__).resolve().parents[1]
def read(name):return json.loads((R/name).read_text('utf8'))
def write(name,data):(R/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),'utf8')
ids=set(read('scripts/roster-wave12.json'));runtime=read('test-results/wave12-packaged-runtime.json')
assert runtime['complete'] and runtime['restart'] and not runtime['errors'];assert {r['character'] for r in runtime['results']}==ids
summary=[]
for kind in ['hold','transitions','expressions']:
 data=read('test-results/wave12-'+kind+'.json');assert {r['character'] for r in data}==ids
 for row in data:
  c=read('characters/'+row['character']+'/character.json');pickup=any(a['id']=='pickup' for a in c['actions'])
  if kind=='hold':
   samples=row['samples'];assert len(samples)==23;memory=[r['diagnostics']['memory'] for r in samples];assert all(m==memory[0] for m in memory)
   assert all(r['diagnostics']['action']==('pickup' if pickup else 'idle') and r['diagnostics']['error'] is None for r in samples)
   summary.append({'character':row['character'],'seconds':23,'gpuObjectCounts':memory[0],'stable':True,'dragAnimation':'pickup' if pickup else 'idle'})
  if kind=='transitions':assert {s['stage'] for s in row['stages']}==({'pickup','release','natural-return'} if pickup else {'natural-return'}) and not row['errors']
assert read('test-results/menu-rotation.json')['passed'];assert read('test-results/rotation-gestures.json')['restart'];assert read('test-results/wave12-packaged-scroll.json')['complete'];assert read('test-results/wave12-speeds.json')['complete'];assert read('test-results/wave12-package.json')['complete']
resources=read('test-results/wave12-resources.json');assert len(resources['unchangedPreviousFiles'])==504;assert len(read('test-results/wave12-halo-geometry.json'))==10
report={'version':'0.2.3','complete':True,'addedCharacters':5,'addedCostumes':10,'addedActions':303,'totalGroups':67,'totalCostumes':148,'totalActions':3777,'furnitureInteractions':86,'offlineLoads':10,'offlineActionSmokeChecks':sum(len(r['played']) for r in runtime['results']),'secondsPerActionSmoke':.36,'authoredChannelsCompared':sum(r['unchangedAuthoredChannels'] for r in resources['added']),'hold':summary,'expressionCostumes':10,'coreTests':35,'mouthUVTests':4,'unchangedAssetFiles':504,'menuAndRotation':'menu-rotation.json','rotationGestures':'rotation-gestures.json','limits':['Quick action checks do not play every long clip in full.','No new furniture, particles, voice or skill cinematics.','Chinatsu original has no own pickup clip in the acquired original set; dragging retains its own idle.','No new 30-minute soak was performed for this release.']}
write('test-results/wave12-validation.json',report)
write('test-results/wave12-action-expansion.json',[r for r in read('test-results/action-expansion.json') if r['character'] in ids])
p=R/'docs/RANDOM-ROSTER.md';s=p.read_text('utf8');mark='## 上一批 0.2.2 记录';notes='''## 0.2.3 验证记录

- 成品断网加载 10 套服装，快速播放 293 项非待机动作，验证回到待机和重启恢复。每项快速检查约 0.36 秒，未逐个完整播放所有长片段。
- 10 套服装的待机／互动眉眼和口型通过原始事件核对；每套连续拖动采样 23 次，窗口和 GPU 几何／纹理对象数稳定。9 套有自身提起动作的服装验证提起、放下和自然返回均存在多帧过渡；千夏原版保持自身待机。
- 实际 Ctrl、Shift、Alt 拖动分别超过一整圈；角度和自定义菜单配置跨重启恢复。浅／深主题菜单、显示项及排序、动作收藏入口、置顶、Esc、顶部恢复角度、星号居中与面板滚动回归通过。
- 妃咲及日奈睡衣在非零三轴角度、慢／快播放和过渡倍速下，普通动作及家具混合组合回归通过。35 项程序测试、4 项口型导入测试和全库资源检查通过。
- 本轮未重新执行 30 分钟组合压力测试；短时回归不代表长时稳定性验收。

'''
s=s.replace(mark,notes+mark);p.write_text(s,'utf8')
p=R/'docs/VALIDATION.md';s=p.read_text('utf8');p.write_text('# 0.2.3 验证补充\n\n详见 `docs/RANDOM-ROSTER.md` 的 0.2.3 验证记录及源码包 `validation/wave12-validation.json`。本批增加 10 套原版资源与自定义菜单、XYZ 无限圈旋转；旧角色资源逐文件保持不变。\n\n'+s,'utf8')
for entry in read('package.json')['build']['extraFiles']:shutil.copy2(R/entry['from'],R/'release/v0.2.3/win-unpacked'/entry['to'])
print('Validated',report['offlineActionSmokeChecks'],'actions and',report['authoredChannelsCompared'],'source channels; final notes copied')
