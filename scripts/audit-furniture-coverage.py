"""Match installed furniture scenes to source timeline profiles and prior wardrobe."""
import hashlib, json, pathlib, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
characters = sorted((read(p) for p in (ROOT/'characters').glob('*/character.json')), key=lambda c: c['id'])
profiles = read(ROOT/'.assets/furniture-profiles.json')
adapted = read(ROOT/'.assets/furniture-adaptation.json')
index = read(ROOT/'.assets/furniture-index.json')['entries']
public = {c['id'] for c in characters}
profiles = [p for p in profiles if p['character'] in public]
key = lambda p: (p['character'], p['furnitureId'], p['group'], p['studentTrack']['name'] if isinstance(p['studentTrack'], dict) else p['studentTrack'])
assert len({key(p) for p in profiles}) == len(profiles)
assert {key(p) for p in profiles} == {key(p) for p in adapted}
assert all(r['status'] == 'ready' for r in adapted)
assert {(e['character'], e['furnitureId']) for e in index} == {(p['character'], p['furnitureId']) for p in profiles}
scenes = {(c['id'], f['model']) for c in characters for f in c.get('furniture', [])}
assert scenes == {(r['character'], r['model']) for r in adapted}
for character, model in scenes:
    assert (ROOT/'characters'/character/model).is_file()

parity = []
with zipfile.ZipFile(ROOT/'release/BA-Desktop-Pet-0.1.17-win-x64.zip') as old:
    for c in characters:
        prefix = 'resources/characters/'+c['id']+'/'
        if prefix+'character.json' not in old.namelist():
            assert c['id'] in read(ROOT/'scripts/roster-wave7.json')
            continue
        previous = json.loads(old.read(prefix+'character.json'))
        assert {k:v for k,v in c.items() if k != 'furniture'} == {k:v for k,v in previous.items() if k != 'furniture'}, c['id']
        for name in [c['model'], 'thumbnail.png']:
            raw = (ROOT/'characters'/c['id']/name).read_bytes()
            assert raw == old.read(prefix+name), (c['id'], name)
        parity.append({'character':c['id'], 'modelSha256':hashlib.sha256((ROOT/'characters'/c['id']/c['model']).read_bytes()).hexdigest(), 'modelAndThumbnailUnchanged':True, 'normalManifestUnchanged':True})
report = {
    'sourceSnapshot':'2026-10-21', 'officialResourceVersion':'JP r96 patch 33',
    'wardrobePacks':len(characters), 'supportedPacks':sum(bool(c.get('furniture')) for c in characters),
    'distinctFurniture':len({p['furnitureId'] for p in profiles}), 'interactions':len(scenes),
    'unadaptedMappedInteractions':[],
    'packs':[{'id':c['id'], 'name':c['name'], 'furniture':[{'id':f['id'], 'name':f['name'], 'note':f.get('note',''), 'duration':f['duration']} for f in c.get('furniture', [])]} for c in characters]
}
(ROOT/'test-results/furniture-coverage.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
(ROOT/'test-results/furniture-wardrobe-parity.json').write_text(json.dumps(parity,indent=2),encoding='utf-8')
table = ['| 角色／服装 | 已适配家具互动 |', '| --- | --- |']
for c in report['packs']:
    table.append('| '+c['name']+' | '+('；'.join(f['name'] for f in c['furniture']) or '本次资源映射中没有对应家具')+' |')
doc = '''# 家具互动说明 · 0.1.18

已检查当前全部 PACKCOUNT 个角色／服装包，其中 SUPPORTED 套适配了 DISTINCT 件官方家具、INTERACTIONS 组互动动作。双人／多人场景包含原版要求的参与角色，按同一时间轴同步播放。

## 使用

右键桌宠或托盘 → **家具互动**，选择当前服装的家具；也可以在 **角色与动作** 窗口的家具互动区点击按钮。

- 家具与角色整体显示，循环播放该组原版动作；单击场景可从头播放。
- 拖动移动整组场景，动作继续播放。Shift＋拖动水平旋转，Ctrl＋拖动垂直旋转，滚轮缩放。
- 家具模式暂停自动走动、随机动作和眼神跟随，保留原设置；普通动作按钮暂时禁用。
- 点击 **收起家具，恢复桌宠** 返回普通模式。切换服装或重新启动也会退出家具模式。
- 较长的火车等场景会整体缩小以保持完整可见，可用滚轮放大；对着电视／机器的角色可能背向镜头，可旋转查看。
- 加载错误会显示提示，保留收起家具、恢复与托盘退出入口。

## 覆盖范围

以下按 2026-10-21 保存的学生／家具数据和已取得的官方 JP r96 patch 33 资源核对。没有映射不等同于断言该角色在任何版本都没有家具；未用其他角色或自制模型填补。

TABLE

另有 7 套必要同伴资源仅随家具场景出现：尼禄原版、晴奈新年、亚子礼服、樱子偶像、美祢偶像、莉音临战、花子泳装。它们不增加衣橱中的 84 套独立可选角色计数。

## 来源与复现

模型、贴图、骨骼、口型／显隐事件及互动时间轴来自[官方资源目录](https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json)。家具对应关系参考 [SchaleDB 学生数据](https://schaledb.com/data/en/students.json)和[家具数据](https://schaledb.com/data/cn/furniture.json)，随后以官方 PlayableDirector 和 Animator 绑定核验；社区数据本身不代替模型来源。

源文件缓存位于 `.assets`。`index-furniture.py` 建立映射，`acquire-furniture.py` 选择依赖并校验 CRC，`resolve-furniture.py` 解析分支及参与者，`export-furniture.py` 使用带 Euler 曲线与外部时间轴绑定支持的导出器导出，`prepare-furniture.py` 以 30 Hz 合成场景。多人所需角色列在 `scripts/furniture-partners.json`，通过已有角色转换流程放入 `.assets/furniture-partners`，其中铃美魔法少女已于 0.1.16 加入公共衣橱，其余仅用于家具同伴。

家具 GLB 与正常 `model.glb` 分开，保留原版贴图、骨骼和动作；原有 65 套角色包（含 66 组家具）与 0.1.17 逐字节一致；另新增 19 个外观包及 13 组家具互动。材质透明模式按原始材质属性处理，未统一裁掉不透明贴图中的 alpha 数据。时间轴保留片段偏移、速度、显隐与嘴型；同伴光环使用各自的跟随参数。

0.1.15 按原始 MeshFilter 补回可见静态几何体，并核对同名节点的局部变换；按原始单骨骼索引恢复家具和家具场景中角色道具的权重。取景忽略已缩至极小的远处道具，按每个可见网格自身的动画边界计算，避免递归计入隐藏子网格。48 件家具的默认视角经四方向画面对照后单独配置，保存在 `scripts/furniture-view-yaw.json`（数值单位为 π）。

专用 Unity 粒子、音效及全部 Unity 着色器效果尚未复现。泳装妃咲的水面采用原始静态网格与 `_SurfaceColor` 透明颜色，尚无原版深度折射和水波着色。0.1.16 修复泳装日奈泳池的白色水面：按原始 MX/Water 材质的 `_BaseColor` 显示蓝色半透明水面，同样尚无原版折射和水波。本版展示家具与角色的模型动画，不承诺与游戏完整特效画面逐像素一致。

开发验证入口：`node scripts/audit-furniture.mjs`、`python scripts/audit-furniture-coverage.py`、`node scripts/furniture-test.mjs`、`node scripts/furniture-controls-test.mjs`、`node scripts/furniture-views.mjs`。运行时无需 Python、Node.js 或联网；详细实测范围见随包验收记录。
'''.replace('TABLE', '\n'.join(table)).replace('PACKCOUNT',str(report['wardrobePacks'])).replace('SUPPORTED',str(report['supportedPacks'])).replace('DISTINCT',str(report['distinctFurniture'])).replace('INTERACTIONS',str(report['interactions']))
(ROOT/'docs/FURNITURE.md').write_text(doc,encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'packs'},indent=2))
