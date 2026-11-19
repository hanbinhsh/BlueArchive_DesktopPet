import hashlib,json,shutil,sys,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def files(root):return {f.relative_to(root).as_posix():f for f in root.rglob('*') if f.is_file()}
p=read('package.json');assert p['version']=='0.1.22'
folder=R/'release/v0.1.22';unpacked=folder/'win-unpacked';exe=unpacked/'BA Desktop Pet.exe'
runtime=read('test-results/bedroom-packaged-runtime-run.json');assert runtime['complete'] and runtime['offline'] and runtime['count']==7
controls=read('test-results/bedroom-packaged-controls.json');assert all(v is True for k,v in controls.items() if k!='executable')
scroll=read('test-results/bedroom-packaged-scroll.json');assert scroll['complete'] and not scroll['errors'] and len(scroll['results'])==8
for report in [runtime,controls,scroll]:assert Path(report['executable']).resolve()==exe.resolve()
package=read('test-results/bedroom-package.json');assert package['appAsarSha256']==sha(unpacked/'resources/app.asar')
assert len(read('test-results/assets.json'))==110 and len(read('test-results/bedroom-assets.json'))==7
assert read('test-results/bedroom-menu-audit.json')['explicitUnpairedFurnitureActions']==0
source=files(R/'characters');old=files(R/'release/v0.1.21/win-unpacked/resources/characters');actual=files(unpacked/'resources/characters')
assert source.keys()==actual.keys()
for name,path in source.items():assert sha(path)==sha(actual[name]),name
assert not old.keys()-source.keys()
changed=[name for name in old if sha(old[name])!=sha(source[name])];added=sorted(source.keys()-old.keys())
assert changed==['hina_pajamas/character.json'],changed
assert len(added)==7 and all(n.startswith('hina_pajamas/bedroom_') and n.endswith('.glb') for n in added)
if '--prepare-docs' in sys.argv:
    doc=R/'docs/VALIDATION.md';s=doc.read_text(encoding='utf8')
    if '## 0.1.22 ' not in s:
        first,rest=s.split('\n',1)
        note='''## 0.1.22 日奈睡衣家具修复（2026-10-25）

- 夏的乐队场景“伸懒腰”对照官方重新导出的 10.9 秒片段，保留原有姿态；正式包文件与 0.1.21 逐字节一致。
- 日奈新增两件卧室家具、七组原版同步时间轴；人物使用既有模型和动作。家具薄面补上背面显示，并修正默认视角。七项普通菜单动作移到家具互动，总数为 2,693 个普通动作与 86 组家具互动。
- TypeScript 检查、17 项核心测试、生产构建、110 个角色资源校验通过。七个家具 GLB 各采样 121 个时刻：变换有限、无重复动画目标、无异常尺寸尖峰、纹理全内嵌。开发验证和实际 0.1.22 成品均离线加载七项家具，捕获多个时间点画面检查同步关系。
- 成品通过拖动保持播放、单击重播、循环、空白穿透、旋转、缩放、置顶、面板收起恢复自动设置，以及损坏家具副本报错后恢复普通桌宠的测试。动作面板八项滚动回归通过。
- 七个编译运行文件与 0.1.21 完全一致。原角色资源仅日奈睡衣清单改变，新增七个家具 GLB；其余原有资源包括夏场景形态完全一致。没有重复 30 分钟长测或物理多屏／DPI 测试。
- 证据：`bedroom-composition.json`、`bedroom-assets.json`、`bedroom-menu-audit.json`、`bedroom-packaged-runtime-run.json`、`bedroom-packaged-controls.json`、`bedroom-packaged-scroll.json`、`bedroom-package.json`。最终 ZIP 的 CRC 和逐文件摘要校验见 `release-0.1.22.json`。

'''
        doc.write_text(first+'\n\n'+note+rest,encoding='utf8')
    for item in p['build']['extraFiles']:shutil.copy2(R/item['from'],unpacked/item['to'])
for item in p['build']['extraFiles']:assert (R/item['from']).read_bytes()==(unpacked/item['to']).read_bytes()
if '--prepare-docs' in sys.argv:
    print('Packaged tests, unchanged runtime, resource delta and documents verified');sys.exit(0)
archive_path=folder/'BA-Desktop-Pet-0.1.22-win-x64.zip';expected=files(unpacked)
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    names=[e.filename for e in archive.infolist() if not e.is_dir()]
    assert len(names)==len(set(names)) and set(names)==expected.keys()
    for name in names:
        assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
        with archive.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(expected[name])
report={'version':'0.1.22','bytes':archive_path.stat().st_size,'sha256':sha(archive_path),'matchedFiles':len(expected),'changedCharacterFiles':changed,'addedCharacterFiles':added,'unchangedCharacterFiles':len(old)-len(changed),'zipCrc':True,'newSoak30Minutes':False}
(R/'test-results/release-0.1.22.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
dest=R/'release'/archive_path.name;shutil.copy2(archive_path,dest);assert sha(dest)==report['sha256']
print(json.dumps(report,ensure_ascii=False,indent=2))
