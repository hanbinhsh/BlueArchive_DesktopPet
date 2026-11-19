"""Finalize the verified phone resource hotfix, without producing archives."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';base=R/'release/v0.2.20/win-unpacked'
read=lambda n:json.loads((T/n).read_text('utf8'))
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
v=read('release042-verification.json');assert v['unchangedPreviousFiles']==675 and v['version']=='0.2.20'
assert sha(base/'resources/app.asar')==v['appAsarSha256']and sha(base/'BA Desktop Pet.exe')==v['executableSha256']and sha(base/'resources/native/wheel-forwarder.exe')==v['wheelHelperSha256']
for row in read('release042-resources.json'):assert sha(R/'characters'/row['path'])==sha(base/'resources/characters'/row['path'])==row['sha256']
assert len(read('release042-program-identity.json')['identicalRuntimeFiles'])==15
loops=read('phone042-loops.json');assert loops['complete']and loops['version']=='0.2.20'and not loops['errors']and [c['speed']for c in loops['cycles']]==[1,1,2,.5]
eye=read('ichika042-eye-pose-proof.json');assert eye['complete']and eye['sampledTimes']==520 and eye['maxComponentDifference']<1e-4
assert all(not r['omitted']for r in read('ichika042-phone-adaptation.json'))and not read('ichika042-embedded-source.json')['errors']
review=read('phone042-visual-review.json');assert review['complete']and review['finalFramesReviewed']==35 and review['finalContactSheetsReviewed']==4
assert 'pass 82'in(T/'release042-core-tests.log').read_text('utf8')and'Ran 29 tests'in(T/'release042-python-tests.log').read_text('utf8')
body=f'''## 成品复测

最终0.2.20程序在离线状态完成4次整段场景／互动／回待机，速度依次为1×、1×、2×、0.5×，共约{sum(c['seconds']for c in loops['cycles']):.2f}秒，零捕获错误，场景缓存最多2项。四方向35帧、4张接触表已逐页查看，聊天内容贴合屏幕，保留原取景、闪光和照片保存时序。

520个时刻、54条眼部／眉毛通道与独立采样的原始动画相比，最大分量误差{eye['maxComponentDifference']:.9g}，自拍睁眼保持原样。旧32个网格、388条动画通道以及全部原口型、显示曲线保持不变。82项TypeScript、29项Python测试通过。

676个离线资源中仅一花裁判椅的GLB改变，其余675个逐文件保持0.2.19；15个程序运行文件字节一致。此修复采用针对该场景的循环与倍速验证，未将0.2.19的30分钟记录冒充本版长测。
'''
p=R/'docs/FIX-042.md';s=p.read_text('utf8').replace('最终成品验证结果在完成后补入。','成品复测结果见下节。')
if '## 成品复测'not in s:s+='\n'+body
p.write_text(s,'utf8')
def prepend(file,heading,text):
 p=R/file;s=p.read_text('utf8')
 if heading not in s:p.write_text(heading+'\n\n'+text+'\n\n'+s,'utf8')
prepend('docs/VALIDATION.md','## 0.2.20 裁判椅手机画面','补齐一花角色骨骼下遗漏的30个官方手机特效实例。0.5×／1×／2×完整循环与回待机通过，35帧／4张四视角接触表已查看；520个眼部姿势采样保持原始自拍动作。仅一项家具GLB改变，其余675个资源与15个程序运行文件不变；[来源与复测](FIX-042.md)。')
prepend('docs/FURNITURE.md','## 0.2.20 一花裁判椅手机','恢复原始聊天、取景、照片保存、自拍图和闪光；原始眼部动作保留。区别于外部家具时间线，屏幕效果原本直接挂在角色骨骼下，现按原启用曲线转换。详见[FIX-042](FIX-042.md)。')
prepend('docs/ASSETS.md','## 0.2.20 一花手机屏幕','新增原始角色内嵌特效的网格、图集和照片，来源为官方JP r96 CH0071预制体与共享材质。定向取回缺少的材质CAB，CRC与大小验证通过。未使用生成图代替屏幕；[来源与修复](FIX-042.md)。')
package=json.loads((R/'package.json').read_text('utf8'));assert package['version']=='0.2.20'
for entry in package['build']['extraFiles']:
 p=base/entry['to'];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/entry['from'],p)
docs=base/'docs';docs.mkdir(exist_ok=True)
for p in(R/'docs').glob('*.md'):
 if not p.name.startswith('WORK-IN-PROGRESS'):shutil.copy2(p,docs/p.name)
p=base/'使用说明.md';p.write_text(p.read_text('utf8').replace('`release/v0.2.20/win-unpacked/BA Desktop Pet.exe`','`BA Desktop Pet.exe`'),'utf8')
validation=base/'validation';validation.mkdir(exist_ok=True)
for name in ['release042-verification.json','release042-resources.json','release042-program-identity.json','ichika042-resource-proof.json','ichika042-embedded-source.json','ichika042-fx-dependencies.json','ichika042-phone-adaptation.json','ichika042-eye-pose-proof.json','phone042-loops.json','phone042-visual-review.json','finalphone042-runtime.json','wave14-census.json']:
 shutil.copy2(T/name,validation/name)
for p in T.glob('finalphone042-contact-*.jpg'):shutil.copy2(p,validation/p.name)
shutil.copy2(T/'phone042-before-after.jpg',validation/'phone042-before-after.jpg')
summary=dict(version='0.2.20',zipCreated=False,changedResources=v['changedResources'],unchangedPreviousFiles=675,identicalRuntimeFiles=15,cycles=loops['cycles'],errors=loops['errors'],review=review,sourceDirectory=str(R))
(validation/'summary042.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),'utf8')
files=[dict(path=str(p.relative_to(base)),bytes=p.stat().st_size,sha256=sha(p))for p in sorted(base.rglob('*'))if p.is_file()]
report=dict(version='0.2.20',directory=str(base),executable=str(base/'BA Desktop Pet.exe'),zipCreated=False,bytes=sum(f['bytes']for f in files),files=files)
(T/'release042-folder.json').write_text(json.dumps(report,indent=2),'utf8');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))
