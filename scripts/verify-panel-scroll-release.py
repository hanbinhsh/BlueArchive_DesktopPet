import hashlib,json,shutil,sys,zipfile
from pathlib import Path,PurePosixPath
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read('package.json');assert p['version']=='0.1.21'
folder=R/'release/v0.1.21';unpacked=folder/'win-unpacked'
test=read('test-results/panel-scroll-packaged.json');assert test['complete'] and not test['errors'] and len(test['results'])==8
assert Path(test['executable']).resolve()==(unpacked/'BA Desktop Pet.exe').resolve()
for r in test['results']:
    assert abs(r['before']['aside']-r['after']['aside'])<=2 and abs(r['before']['page']-r['after']['page'])<=2
source=read('test-results/panel-scroll-package.json');assert source['changed']==['panel.js'] and source['appAsarSha256']==sha(unpacked/'resources/app.asar')
roots=[R/'characters',R/'release/v0.1.20/win-unpacked/resources/characters',unpacked/'resources/characters']
expected={f.relative_to(roots[0]) for f in roots[0].rglob('*') if f.is_file()}
for root in roots[1:]:
    assert expected=={f.relative_to(root) for f in root.rglob('*') if f.is_file()}
    for name in expected:assert sha(roots[0]/name)==sha(root/name),name
if '--prepare-docs' in sys.argv:
    doc=R/'docs/VALIDATION.md';s=doc.read_text(encoding='utf8');assert '## 0.1.21' not in s
    first,rest=s.split('\n',1)
    text='''## 0.1.21 动作面板滚动修复（2026-10-24）

- 在 0.1.20 成品复现点击下方动作后右侧面板滚动从约 1910 像素降到 8 像素。原因是指令响应重建动作列表，导致滚动容器高度短暂缩小。
- 播放动作时保留已有按钮，仅刷新禁用状态；收藏重排、设置和角色状态更新后恢复右侧与页面滚动位置。家具列表使用一次性替换，避免清空期间高度塌缩。
- TypeScript 检查、17 项核心测试、生产构建通过。开发版及打包后的 0.1.21 均通过八项滚动检查：下方动作、重复播放、收藏重排、自动设置、分类结果、搜索结果、只看收藏以及切换角色后播放；也检查角色切换保持页面位置。测试使用离线模拟和独立配置，不修改日常配置。
- 新成品中仅 `panel.js` 发生代码变化，其余六个编译文件和全部角色资源与 0.1.20 完全一致。角色数量、动作、家具和渲染行为没有调整；未重复整套角色动画、30 分钟长测或物理 DPI 测试。
- 证据：`panel-scroll-before.json`、`panel-scroll-fixed.json`、`panel-scroll-packaged.json`、`panel-scroll-package.json`。发布压缩包逐文件摘要及 CRC 校验结果见 `release-0.1.21.json`。

'''
    doc.write_text(first+'\n\n'+text+rest,encoding='utf8')
    for item in p['build']['extraFiles']:shutil.copy2(R/item['from'],unpacked/item['to'])
for item in p['build']['extraFiles']:assert (R/item['from']).read_bytes()==(unpacked/item['to']).read_bytes()
if '--prepare-docs' in sys.argv:
    print('Packaged scroll regression, runtime delta, unchanged resources and documents passed');sys.exit(0)
archive_path=folder/'BA-Desktop-Pet-0.1.21-win-x64.zip'
files={f.relative_to(unpacked).as_posix() for f in unpacked.rglob('*') if f.is_file()}
with zipfile.ZipFile(archive_path) as archive:
    assert archive.testzip() is None
    entries=[e.filename for e in archive.infolist() if not e.is_dir()]
    assert len(entries)==len(set(entries)) and set(entries)==files
    for name in entries:
        assert not PurePosixPath(name).is_absolute() and '..' not in PurePosixPath(name).parts
        with archive.open(name) as f:assert hashlib.file_digest(f,'sha256').hexdigest()==sha(unpacked/name)
report={'version':'0.1.21','bytes':archive_path.stat().st_size,'sha256':sha(archive_path),'matchedFiles':len(files),'unchangedCharacterFiles':len(expected),'zipCrc':True,'scrollTest':test,'source':source,'newSoak30Minutes':False}
(R/'test-results/release-0.1.21.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
destination=R/'release'/archive_path.name;shutil.copy2(archive_path,destination);assert sha(destination)==report['sha256']
print(json.dumps({k:v for k,v in report.items() if k not in ['scrollTest','source']},indent=2))
