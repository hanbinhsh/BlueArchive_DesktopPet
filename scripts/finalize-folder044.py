"""Verify and document the runnable 0.2.22 folder; never build archives."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.22/win-unpacked'
read=lambda n:json.loads((T/n).read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
v=read('release044-verification.json');assert(v['version'],v['resources'],v['unchangedPreviousFiles'])==('0.2.22',781,737)
for file,key in [('resources/app.asar','appAsarSha256'),('BA Desktop Pet.exe','executableSha256'),('resources/native/wheel-forwarder.exe','wheelHelperSha256')]:assert sha(base/file)==v[key]
for row in read('release044-resources.json'):assert sha(R/'characters'/row['path'])==sha(base/'resources/characters'/row['path'])==row['sha256']
runtime=read('wave16-runtime.json');assert runtime['complete']and runtime['restart']and not runtime['errors']and len(runtime['results'])==11 and sum(r['available']for r in runtime['results'])==290
faces=read('faces044-runtime.json');assert faces['complete']and not faces['errors']and len(faces['results'])==11
assert read('juri044-face-final.json')['complete']and not read('juri044-face-final.json')['errors']
assert len(read('final044-runtime.json'))==12 and len(read('final044-redo-runtime.json'))==4
assert all(r['status']=='ready'for r in read('wave16-furniture-adaptation.json'))
assert all(not r['omitted']for r in read('wave16-fx-adaptation.json')+read('wave16-embedded-adaptation.json'))
assert not read('wave16-embedded-source.json')['errors']and not read('wave16-embedded-final-audit.json')['missing']and not read('wave16-persistent-audit.json')['unexplained']
assert not read('static044-source-audit.json')['errors']and read('wave16-skin-integrity.json')['complete']
assert len(read('chiaki044-repair.json'))==2 and len(read('juri044-face-repair.json'))==2
assert all(r['changedOnlyVisibility']for r in read('chiaki044-repair.json')+read('juri044-face-repair.json'))
loops=read('newfx044-loops.json');assert loops['complete']and not loops['errors']and len(loops['cycles'])==3
holds=read('hold044.json');transitions=read('transitions044.json');assert len(holds)==len(transitions)==3 and all(not r['errors']for r in transitions)
assert 'pass 83'in(T/'release044-core-tests.log').read_text('utf8')and'Ran 32 tests'in(T/'release044-python-tests.log').read_text('utf8')
visual=read('visual044-review.json');assert visual['complete']and visual['faceFramesReviewed']==93 and visual['furnitureFramesReviewed']==120
program=read('release044-program-identity.json');assert len(program['identicalRuntimeFiles'])==15 and not program['changedRuntimeFiles']
soak=read('release044-soak.json');assert soak['complete']and soak['version']=='0.2.22'and soak['elapsedSeconds']>=1800 and not soak['errors']and soak['fps']>=20
census=read('wave16-census.json');assert(census['installedPlayable'],census['remainingPlayable'],census['outfits'],census['actions'],census['furniture'])==(94,55,196,4935,189)
native=read('wave16-resources.json');channels=sum(r['unchangedAuthoredChannels']for r in native['added']);assert channels==112697
groups=defaultdict(list)
for s in soak['samples']:groups[(s['character'],s['diagnostics']['scene'])].append(s)
gpu=[p['memoryMiB']for s in soak['samples']for p in s['metrics']if p['type']=='GPU']
resources=dict(elapsedSeconds=soak['elapsedSeconds'],fps=soak['fps'],totalProcessWorkingSetMiB=soak['memoryMiB'],gpuProcessWorkingSetMiB=dict(min=min(gpu),max=max(gpu)),note='GPU process working set is system RAM, not measured VRAM; geometry/texture figures are live Three.js resource counts.',scenes=[dict(character=k[0],scene=k[1],samples=len(ss),cycles=sorted({s['cycle']for s in ss}),resources={n:dict(min=min(s['diagnostics']['memory'][n]for s in ss),max=max(s['diagnostics']['memory'][n]for s in ss))for n in ['geometries','textures']})for k,ss in sorted(groups.items())])
(T/'release044-resource-summary.json').write_text(json.dumps(resources,indent=2),'utf8')
m=soak['memoryMiB'];body=f'''## 最终成品验收

最终0.2.22程序离线启动，10套新增外观的243个动作与千明47个动作共290项逐一播放、切换角色与重启恢复通过。11套角色的93个面部时刻已查看，千明与打工朱莉的睁眼／眯眼不再同时显示。千明公告板与朱莉松饼桌同时修复；原动画通道、骨骼、几何与材质保留。

10项新家具及千明／亚津子2项回归场景共120帧、12张接触表已查看。另查看40个四向画面、喷泉8个角度、发球机／双人沙浴16个起始和中段角度，以及10张新缩略图；合计287个最终采样画面、30张接触表。朱莉修复后的9个面部及家具10帧、缩略图重新生成并复核。人物朝向随原动作自然变化，面具架保留陈列面与角色挑选面具的原姿势。

千明公告板2×、温泉时雨浴缸0.5×、打工朱莉桌2×三个完整场景／互动循环通过。三套外观各23秒持续拖动、提起放下／自然回待机过渡通过；温泉时雨没有原生提起片段，拖动保留其自己的待机。83项TypeScript、32项Python、类型检查及全资源检查通过。

真实连续运行{soak['elapsedSeconds']:.2f}秒，完成{soak['cycles']}轮家具／互动组合、{soak['selections']}次角色切换，平均{soak['fps']:.2f} FPS，零捕获错误。预热后总进程工作集{m['min']:.1f}～{m['max']:.1f} MiB；倒数第二个5分钟均值{m['previousFiveMinutes']:.1f} MiB，最后5分钟{m['lastFiveMinutes']:.1f} MiB，通过末期增长检查。GPU进程工作集和按场景的几何／纹理计数见release044-resource-summary.json，不等同于独立测量的显存。

新增112,697条原始动画通道的值、时间与插值逐项相同；20个新增模型的534,030个带权重顶点检查通过。781资源中新增40项、旧资源4项指定修复，其余737项保持0.2.21；15个程序运行文件字节相同，滚轮桥接按同一源码重编译。仅交付可运行文件夹，没有创建程序或源码ZIP。
'''
p=R/'docs/ROSTER-016.md';s=p.read_text('utf8').replace('最终成品验收完成后补入。','最终成品验收见下节。')
if '## 最终成品验收'not in s:s+='\n'+body
p.write_text(s,'utf8')
def prepend(file,title,text):
 p=R/file;s=p.read_text('utf8')
 if title not in s:p.write_text(title+'\n\n'+text+'\n\n'+s,'utf8')
prepend('docs/VALIDATION.md','## 0.2.22 六位学生与眼部修复',f'新增243动作及千明47动作离线逐项播放、重启恢复通过；93个面部、120个家具时刻及额外角度已查看。三套倍速／长拖／过渡通过；83项核心、32项Python测试通过。真实{soak["elapsedSeconds"]:.1f}秒循环约{soak["fps"]:.2f} FPS，零捕获错误；[完整验收](ROSTER-016.md)。')
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.22'
for entry in package['build']['extraFiles']:
 p=base/entry['to'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/entry['from'],p)
docs=base/'docs';docs.mkdir(exist_ok=True)
for p in(R/'docs').glob('*.md'):
 if not p.name.startswith('WORK-IN-PROGRESS'):shutil.copy2(p,docs/p.name)
p=base/'使用说明.md';p.write_text(p.read_text('utf8').replace('`release/v0.2.22/win-unpacked/BA Desktop Pet.exe`','`BA Desktop Pet.exe`'),'utf8')
validation=base/'validation';validation.mkdir(exist_ok=True)
evidence=['release044-verification.json','release044-resources.json','release044-program-identity.json','wave16-selection.json','wave16-census.json','wave16-acquisition.json','wave16-original-structure.json','wave16-framing.json','wave16-resources.json','wave16-skin-integrity.json','wave16-view-selection.json','wave16-furniture-adaptation.json','wave16-fx-adaptation.json','wave16-embedded-source.json','wave16-embedded-adaptation.json','wave16-embedded-final-audit.json','wave16-persistent-audit.json','wave16-embedded-fx-dependencies.json','static044-source-audit.json','chiaki044-face-source.json','chiaki044-repair.json','juri044-face-repair.json','newfaces044-source-layout.json','repairs044-resource-changes.json','fountain044-view-selection.json','faces044-runtime.json','juri044-face-final.json','final044-runtime.json','final044-redo-runtime.json','facing044-runtime.json','wave16-runtime.json','visual044-review.json','newfx044-loops.json','hold044.json','transitions044.json','unity044-emission-proof.json','release044-soak.json','release044-soak-cases.json','release044-resource-summary.json']
for n in evidence:shutil.copy2(T/n,validation/n)
for pattern in ['wave16-normal-contact.jpg','wave16-angle-options-*.jpg','fountain044-options.jpg','facing044-options-*.jpg','final044-contact-*.jpg','faces044-contact-*.jpg']:
 for p in T.glob(pattern):shutil.copy2(p,validation/p.name)
shutil.copy2(T/'unity044-emission.csv',validation/'unity044-emission.csv')
summary=dict(version='0.2.22',zipCreated=False,sourceDirectory=str(R),studentsAdded=6,outfitsAdded=10,actionsAdded=243,furnitureAdded=10,installedPlayable=94,totalPlayable=149,remainingPlayable=55,outfits=196,actions=4935,furniture=189,oldResourcesUnchanged=737,resourceFiles=781,changedOldResources=v['changedResources'],nativeChannelsVerified=channels,visual=visual,soak={k:soak[k]for k in ['complete','elapsedSeconds','fps','cycles','selections','errors','memoryMiB']})
(validation/'summary044.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
files=[dict(path=str(p.relative_to(base)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(base.rglob('*'))if p.is_file()]
report=dict(version='0.2.22',directory=str(base),executable=str(base/'BA Desktop Pet.exe'),zipCreated=False,bytes=sum(f['bytes']for f in files),files=files)
(T/'release044-folder.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))
