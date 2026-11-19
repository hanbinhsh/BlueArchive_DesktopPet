"""Keep the increment's sources, counts and limitations reviewable."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results';read=lambda p:json.loads(p.read_text('utf8'))
specs=read(R/'scripts/roster-wave14.json');cs={k:read(R/'characters'/k/'character.json')for k in specs};census=read(T/'wave14-census.json')
def prepend(file,heading,body):
 p=R/file;s=p.read_text('utf8')
 if heading not in s:p.write_text(heading+'\n\n'+body+'\n\n'+s,'utf8')
table='| 外观 | 原始模型 | 普通动作 | 家具 |\n| --- | --- | --- | --- |\n'
for k,(prefix,name)in specs.items():table+=f"| {name} | {prefix} | {len(cs[k]['actions'])} | {len(cs[k].get('furniture',[]))} |\n"
body='随机新增10位未安装学生：安娜、巴、日向、御坂美琴、桐乃、一花、律、真白、志美子、果穗；包含15套外观、369个普通动作、15项家具互动。一花泳装的双人打西瓜包含已适配的泳装萌绘搭档。\n\n当前169套外观、4,305个普通动作、165项家具；按2026-11-17保存的日服已实装名单，已加入78/149位学生，未加入71位，普拉娜NPC单列。详见[新增角色与验证](docs/ROSTER-014.md)和[未加入名单](docs/ROSTER-COVERAGE.md)。'
prepend('README.md','## 0.2.19 随机新增十位角色',body)
p=R/'README.md';s=p.read_text('utf8');start=s.index('当前版本：');end=s.index('\n\n',start)
s=s[:start]+'当前版本：**0.2.19**。合计169套外观、4,305个普通动作、165项家具。保留0.2.18的历史修复与全部616个原有资源。新增角色及统计口径见 [ROSTER-014](docs/ROSTER-014.md)和[角色覆盖表](docs/ROSTER-COVERAGE.md)。'+s[end:]
s=s.replace('`release/v0.2.18/win-unpacked/BA Desktop Pet.exe`','`release/v0.2.19/win-unpacked/BA Desktop Pet.exe`');p.write_text(s,'utf8')
prepend('docs/ASSETS.md','## 0.2.19 十位新增学生（2026-11-17）','使用官方JP r96缓存目录中的原始模型、贴图、骨骼、动画及事件；按所需角色和家具提取，不下载整库。新增15套外观，原616个资源逐文件保持不变。来源、转换修复与限制见[ROSTER-014](ROSTER-014.md)。')
prepend('docs/COSTUMES.md','## 0.2.19 十位学生增量',table+'\n本次15套覆盖所选十位在名单中的全部已实装外观，不据此宣称其他所有学生的服装均已完整。')
prepend('docs/FURNITURE.md','## 0.2.19 十五项新增互动','新增机械工程学工作台、波浪纹靠椅、演讲桌、日向两项座椅及泳装日光浴床、MomoFriends周边摊位、瓦尔基丽射击训练场、救生员椅、裁判椅、单人／双人打西瓜、雕刻台、夏日遮阳伞、百鬼夜行周边展示架。真白常服与志美子在此数据中没有绑定家具。当前165项；视角及特效验证见[ROSTER-014](ROSTER-014.md)。')
text='# 0.2.19 随机新增十位学生\n\n'+body.replace('docs/','')+'\n\n'+table+'''
## 来源和转换

名单快照保存于2026-11-17，英文与中文[SchaleDB数据](https://schaledb.com/data/en/students.json)的SHA256、固定抽取种子和候选池见wave14-selection.json。模型来自官方JP r96已缓存补丁目录，角色包大小及CRC核验见wave14-acquisition.json；角色原始骨骼、面部默认值、片段和光环资料见wave14-original-structure.json。

普通动作保留原时间、插值及数值。371个候选经每段121个时刻的取景检查，排除日向和一花泳装各1段需技能场景的片段，实际开放369个。真白原版原始资源没有提起片段，拖动时保持她自己的待机，不用其他角色动作代替。巴旗袍原提起片段拼作Fomation，已按原名称映射。志美子的书本补取原始共享材质／贴图依赖。

日向原版压缩网格的318个四影响权重，受第三方解码器将5-bit整数余量误作浮点余量的影响；现直接从原始打包流恢复(31-累计整数)/31，保留原骨骼索引。对7614个源顶点及其每个材质面的实际GLB权重逐项验证，没有丢弃顶点或任意重归一化。

新增15项家具。巴靠椅选择完整咖啡厅预制体，避免同名精简依赖体的空网格；保留真正在原预制体中为空的节点。桐乃射击场的子弹使用原始主贴图、Matcap贴图和法线；着色计算按缓存原始D3D程序转写，保留原粒子时序。新增Matcap分支只在含该描述的材质启用。所有时间线粒子记录均无遗漏，常驻粒子与原始启用轨道另行核对。四方向比较后选择默认视角；果穗面向周边柜的原场景保留观看柜内展示品的视角。

## 验收范围

本版只重验新增内容和受新Matcap分支影响的场景，不将关键帧采样表述为与游戏完整光照、技能舞台、音效及后处理逐像素一致。原616个离线资源保持0.2.18逐文件一致。

最终成品测试与30分钟稳定性结果完成后追加于此。默认仅交付可运行文件夹，不创建程序或源码ZIP。
'''
(R/'docs/ROSTER-014.md').write_text(text,'utf8')
print('Documented',len(cs),'outfits')
