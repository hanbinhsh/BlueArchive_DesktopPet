"""Finalize the verified 0.2.21 runnable directory without creating archives."""
from pathlib import Path
import json,hashlib,shutil
from collections import defaultdict
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.21/win-unpacked'
read=lambda n:json.loads((T/n).read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
v=read('release043-verification.json');assert v['version']=='0.2.21'and v['resources']==741 and v['unchangedPreviousFiles']==676
for file,key in [('resources/app.asar','appAsarSha256'),('BA Desktop Pet.exe','executableSha256'),('resources/native/wheel-forwarder.exe','wheelHelperSha256')]:assert sha(base/file)==v[key]
for row in read('release043-resources.json'):assert sha(R/'characters'/row['path'])==sha(base/'resources/characters'/row['path'])==row['sha256']
runtime=read('wave15-runtime.json');assert runtime['complete']and runtime['restart']and not runtime['errors']and len(runtime['results'])==17 and sum(r['available']for r in runtime['results'])==387
assert not read('faces043-runtime.json')['errors']and read('faces043-runtime.json')['complete']
assert len(read('final043-runtime.json'))==17
assert all(not r['omitted']for r in read('wave15-fx-adaptation.json')+read('wave15-embedded-adaptation.json'))
assert not read('wave15-embedded-final-audit.json')['missing']and not read('wave15-persistent-audit.json')['unexplained']
assert not read('static043-source-audit.json')['errors']and not read('wave15-embedded-source.json')['errors']
loops=read('newfx043-loops.json');phone=read('phone043-loops.json');assert loops['complete']and not loops['errors']and phone['complete']and not phone['errors']
assert [r['speed']for r in phone['cycles']]==[1,1,2,.5]and len(loops['cycles'])==3
holds=read('hold043.json');transitions=read('transitions043.json');assert len(holds)==len(transitions)==4 and all(not r['errors']for r in transitions)
assert 'pass 83'in(T/'release043-core-tests.log').read_text('utf8')and'Ran 29 tests'in(T/'release043-python-tests.log').read_text('utf8')
visual=read('visual043-review.json');assert visual['complete']and visual['faceFramesReviewed']==147 and visual['furnitureFramesReviewed']==170
program=read('release043-program-identity.json');assert len(program['identicalRuntimeFiles'])==14 and program['changedRuntimeFiles']==['/dist/renderer.js']
assert read('release043-feature-gates.json')['oldResourcesActivatingNewBranches']==0 and read('wave15-skin-integrity.json')['complete']
soak=read('release043-soak.json');assert soak['complete']and soak['version']=='0.2.21'and soak['elapsedSeconds']>=1800 and not soak['errors']and soak['fps']>=20
census=read('wave15-census.json');assert(census['installedPlayable'],census['remainingPlayable'],census['outfits'],census['actions'],census['furniture'])==(88,61,186,4692,179)
native=read('wave15-resources.json');channels=sum(r['unchangedAuthoredChannels']for r in native['added']);assert channels==149851
groups=defaultdict(list)
for sample in soak['samples']:groups[(sample['character'],sample['diagnostics']['scene'])].append(sample)
gpu=[p['memoryMiB']for s in soak['samples']for p in s['metrics']if p['type']=='GPU']
resources=dict(elapsedSeconds=soak['elapsedSeconds'],fps=soak['fps'],totalProcessWorkingSetMiB=soak['memoryMiB'],gpuProcessWorkingSetMiB=dict(min=min(gpu),max=max(gpu)),note='GPU process working set is system RAM, not measured VRAM; geometries and textures are live Three.js resources.',scenes=[dict(character=k[0],scene=k[1],samples=len(ss),cycles=sorted({s['cycle']for s in ss}),resources={name:dict(min=min(s['diagnostics']['memory'][name]for s in ss),max=max(s['diagnostics']['memory'][name]for s in ss))for name in ['geometries','textures']})for k,ss in sorted(groups.items())])
(T/'release043-resource-summary.json').write_text(json.dumps(resources,indent=2),'utf8')
memory=soak['memoryMiB'];body=f'''## 最终成品验收

最终0.2.21程序离线启动，17套外观的387个普通动作逐项播放、角色切换和重启恢复通过。原149,851条body动画通道的值、时间和插值与原导出逐项相同；676个旧资源逐文件保持0.2.20。15个程序运行文件中14个相同，仅渲染bundle增加由新资源启用的拖尾与火焰分支。滚轮桥接程序按同一C#源码重编译。

17张普通预览、56张家具四向、170张最终家具时间采样、147张面部／提起采样，共390帧、39张接触表已逐页查看。眉眼、嘴型、光环和附件未见明显转换异常；一花手机、美祢茶几、桔梗水面作为历史场景回归。另有一花手机4个整段循环（1×、1×、2×、0.5×）以及庚／晴／泳装亚津子3个完整倍速循环；4套外观各23秒持续拖动、提起放下和自然回待机过渡通过。83项TypeScript、29项Python及类型检查、全资源检查通过。

真实连续运行{soak['elapsedSeconds']:.2f}秒，完成{soak['cycles']}轮家具／互动组合与{soak['selections']}次角色切换，平均{soak['fps']:.2f} FPS，零捕获错误。预热后进程总工作集{memory['min']:.1f}～{memory['max']:.1f} MiB，倒数第二个5分钟均值{memory['previousFiveMinutes']:.1f} MiB，最后5分钟{memory['lastFiveMinutes']:.1f} MiB，通过末期增长检查。GPU进程工作集和按场景统计的几何／纹理数另见release043-resource-summary.json；没有将进程内存冒称显存。

最终可运行目录包含741项离线资源，不依赖用户安装Node.js。只生成文件夹，没有创建程序或源码ZIP。
'''
p=R/'docs/ROSTER-015.md';s=p.read_text('utf8').replace('最终成品测试与稳定性结果完成后补入。','最终成品测试结果如下。')
if '## 最终成品验收'not in s:s+='\n'+body
p.write_text(s,'utf8')
def prepend(file,heading,text):
 p=R/file;s=p.read_text('utf8')
 if heading not in s:p.write_text(heading+'\n\n'+text+'\n\n'+s,'utf8')
prepend('docs/VALIDATION.md','## 0.2.21 随机追加十位',f'17套新外观／387动作／14家具的离线与重启验证通过。390帧／39张接触表已查看，4套长拖和过渡、手机及新特效倍速循环通过；83项核心和29项Python测试通过。真实{soak["elapsedSeconds"]:.1f}秒循环约{soak["fps"]:.2f} FPS，零捕获错误；[完整记录](ROSTER-015.md)。')
prepend('docs/ASSETS.md','## 0.2.21 原始特效补齐','泳装亚津子的原生相机屏幕、闪光和喷泉常驻粒子已恢复；庚大锅拖尾与晴咖啡桌火焰增加对应原生分支。原149851条body通道保持原数值，旧676资源保持字节一致。详细来源与验收见[ROSTER-015](ROSTER-015.md)。')
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.21'
for entry in package['build']['extraFiles']:
 p=base/entry['to'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/entry['from'],p)
docs=base/'docs';docs.mkdir(exist_ok=True)
for p in(R/'docs').glob('*.md'):
 if not p.name.startswith('WORK-IN-PROGRESS'):shutil.copy2(p,docs/p.name)
p=base/'使用说明.md';p.write_text(p.read_text('utf8').replace('`release/v0.2.21/win-unpacked/BA Desktop Pet.exe`','`BA Desktop Pet.exe`'),'utf8')
validation=base/'validation';validation.mkdir(exist_ok=True)
evidence=['release043-verification.json','release043-resources.json','release043-program-identity.json','wave15-resources.json','wave15-selection.json','wave15-census.json','wave15-acquisition.json','wave15-original-structure.json','wave15-framing.json','wave15-view-selection.json','wave15-furniture-adaptation.json','wave15-fx-adaptation.json','wave15-fx-dependencies.json','wave15-shared-dependencies.json','wave15-embedded-source.json','wave15-embedded-adaptation.json','wave15-embedded-final-audit.json','wave15-embedded-fx-dependencies.json','wave15-persistent-audit.json','static043-source-audit.json','wave15-runtime.json','faces043-runtime.json','final043-runtime.json','visual043-review.json','newfx043-loops.json','phone043-loops.json','hold043.json','transitions043.json','release043-soak.json','release043-soak-cases.json','release043-resource-summary.json']
for name in evidence:shutil.copy2(T/name,validation/name)
for name in ['release043-feature-gates.json','wave15-skin-integrity.json']:shutil.copy2(T/name,validation/name)
for pattern in ['wave15-normal-contact.jpg','wave15-angle-options-*.jpg','final043-contact-*.jpg','faces043-contact-*.jpg']:
 for p in T.glob(pattern):shutil.copy2(p,validation/p.name)
summary=dict(version='0.2.21',zipCreated=False,sourceDirectory=str(R),studentsAdded=10,outfitsAdded=17,actionsAdded=387,furnitureAdded=14,installedPlayable=88,totalPlayable=149,remainingPlayable=61,outfits=186,actions=4692,furniture=179,oldResourcesUnchanged=676,resourceFiles=741,originalBodyChannelsVerified=channels,visual=visual,soak={k:soak[k]for k in ['complete','elapsedSeconds','fps','cycles','selections','errors','memoryMiB']})
(validation/'summary043.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
files=[dict(path=str(p.relative_to(base)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(base.rglob('*'))if p.is_file()]
report=dict(version='0.2.21',directory=str(base),executable=str(base/'BA Desktop Pet.exe'),zipCreated=False,bytes=sum(f['bytes']for f in files),files=files)
(T/'release043-folder.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))
