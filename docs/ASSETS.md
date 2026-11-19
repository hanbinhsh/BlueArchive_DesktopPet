## 0.2.25 十五位学生与同类隐患修复

原始官方 JP r96 模型、贴图、骨骼动画与家具时间线按需提取并 CRC 校验，详见[ROSTER-017](ROSTER-017.md)。

## 0.2.22 六位学生与资源修复

原始官方模型与事件，按需提取；修复千明事件索引，补齐静态水面与内嵌汗滴。详见[ROSTER-016](ROSTER-016.md)。

## 0.2.21 原始特效补齐

泳装亚津子的原生相机屏幕、闪光和喷泉常驻粒子已恢复；庚大锅拖尾与晴咖啡桌火焰增加对应原生分支。原149851条body通道保持原数值，旧676资源保持字节一致。详细来源与验收见[ROSTER-015](ROSTER-015.md)。

## 0.2.21 十位学生增量

使用官方JP r96原始模型、贴图、骨骼、动画与事件，按需提取与校验。旧676项资源保持逐文件一致，来源和转换记录见[ROSTER-015](ROSTER-015.md)。

## 0.2.20 一花手机屏幕

新增原始角色内嵌特效的网格、图集和照片，来源为官方JP r96 CH0071预制体与共享材质。定向取回缺少的材质CAB，CRC与大小验证通过。未使用生成图代替屏幕；[来源与修复](FIX-042.md)。

## 0.2.19 十位新增学生（2026-11-17）

使用官方JP r96缓存目录中的原始模型、贴图、骨骼、动画及事件；按所需角色和家具提取，不下载整库。新增15套外观，原616个资源逐文件保持不变。来源、转换修复与限制见[ROSTER-014](ROSTER-014.md)。

## 0.2.18 若藻与伊吹（2026-11-17）

新增4套官方原始模型及其自带骨骼、原动作曲线、材质和光环。若藻常服原始预制体戴面具且不含口型图集；其余3套保留原始口型事件。另适配5项家具，双人沙浴的伊吕波作为场景搭档。原有599个资源保持0.2.17逐文件一致。来源与限制见[ROSTER-013](ROSTER-013.md)。

## 0.2.17 静态泡沫与液体（2026-11-17）

恢复鹤城泳池5片静态泡沫的3张原始纹理、扰动和透明度；修正与日奈共用水面的混合顺序、美祢液体及茶水Tint。原始表面审计覆盖139个独立家具模型、258项可对应材质，没有剩余同类DSFX／Tint缺失。仅3个GLB更改，不删网格、不改动画、不以自绘水波替代原素材。详见[AUDIT-038](AUDIT-038.md)。

## 0.2.16 原始显示状态与时间线补全（2026-11-17）

当前仍为150套外观、3,808个普通动作、145项家具互动。本版修正原始隐藏Renderer、玻璃透明度、实体手机显隐、泡沫遮罩色彩空间、网格粒子旋转及短曲线循环；补回蜡烛、茶杯蒸汽、6个场景的常驻粒子和内部导演时间线。27项变更资源均保留原人物／家具基础几何，无生成图片或同人模型替代。

蒸汽缺失依赖从官方资源目录定位单个bundle，范围读取并校验CRC；源记录、原生Unity探针、27项安装差异和艾米视频关键帧随源码包validation提供。完整验证数据与限制见 [本版记录](AUDIT-037.md)。

## 0.2.15 家具与粒子复核（2026-11-16）

当前为150套外观、3,808个普通动作、145项家具互动。八云原始手机与分段时序、View背景光深度、网格波浪枢轴、爱理音符发射阶段、家具视角、街机剔除和水面连续时钟已修正；21项资源变更经过备份与基础几何完整性核验。

79项TypeScript测试、21项Python测试、类型与资源检查通过。实际成品断网遍历145项家具、435张关键帧；另完成30分钟（1801.608秒）连续47轮组合，平均29.38 FPS，零捕获错误。进程合计工作集约713～1114 MiB，最后两个五分钟均值858.64／899.90 MiB，通过增长判据。完整证据、原始水面表现与验收边界见 [本版核验记录](AUDIT-036.md)。历史版本的待办状态不代表当前版本状态。

## 0.2.14 对话框与叹气粒子修复（2026-11-14）

修正重复次数 0 被误判成不发射的问题，保留原始粒子数量上限；修复拉伸图案方向。忧书桌对话框恢复原始烦恼线团，同时核对其他相关家具。详见 [AUDIT-034.md](AUDIT-034.md)。

## 0.2.13 剩余家具特效补全（2026-11-14）

补回温泉千夏、泉奈、玛丽共 9 个特效入口。修正同名预制体选择、变换节点识别和合法空父节点处理；当前适配清单没有导出遗漏。仅 3 个家具 GLB 改动，原始几何和动画不变。详见 [AUDIT-033.md](AUDIT-033.md)，该记录更正了 0.2.12 对这 9 项来源缺失的判断。

# 角色资源记录

## 0.2.12 家具特效核对

当前安装清单为 150 套外观、3,808 个普通动作、145 项家具互动；以下旧版本段落中的数量为当时记录。

本轮从已缓存的原版家具资源核对 105 套时间线、387 个特效根节点，原始材质／贴图依赖无缺失。136 个家具入口使用这些时间线，其中 133 个入口的适配清单没有遗漏；另 3 个入口共 9 条控制轨道缺少原始挂接对象，具体见 [本版排查记录](AUDIT-032.md)。9 个特殊卧室／龙椅入口另行验证。

原始纹理、网格及动画仍保留，未使用同人重建或生成图片替代游戏资源。美祢杯口遮挡和舞台地面遮挡是桌宠端的适配。导出过程及依赖定位工具位于 `scripts/export-cafe-effects.py`、`prepare-cafe-effects.py`、`source_dependencies.py`；源码包 `validation/full032-final-adaptation.json` 记录每个入口的结果。源码包不重复收录游戏模型，重建时从免安装包的 `resources/characters` 复制。

## 0.2.1 新增

本批随机新增鹤城、艾米、南、花子、䌷，9 套外观与 268 个普通动作。当前累计 52 位角色、119 套外观／形态、2,961 个普通动作。旧资源保持不变。完整列表、原始事件限制及核对依据见 [角色库说明](LIBRARY.md)。

## 0.1.22 原版卧室家具来源

日奈睡衣新增 `field_833_zone01` 中的 `Prop_Field_833_Zone01_Bed_Mesh`、`Prop_Field_833_Zone01_Windowsofa_Mesh`，来源为既有官方 JP r96 patch 33 资源目录。所需依赖按 bundle 获取，新增纹理由 `FullPatch_029.zip` 校验大小和 CRC 后提取。床四段 Day00–Day03、沙发 Start/Ing/End 与角色 `Field_Player_NP0009_Cafe_Prop_Field_833_Zone01_*` 按官方时间轴组合，嵌入 GLB，可离线加载。

每个 GLB 的 `BA_furniture.sourceTimeline` 记录原时间轴；完整绑定与 clip-in 记录见源码目录 `test-results/bedroom-composition.json`，导出和转换脚本为 `export-bedroom-prefab.py`、`prepare-bedroom-interactions.py`。本版没有改变任何原有角色 `model.glb`。


## 0.1.20 来源补充

新增 10 包均使用官方 JP r96 patch 33 的原版资源。原包和 bundle 已按目录提供的大小与 CRC 校验；三森、萌绘泳装所需的原版光环依赖一起打包。没有使用同人重建或借用其他角色的动画。

支援角色的一些自身动画未被咖啡厅控制器引用，转换时通过明确的原始片段名单补充绑定；相机、无人机、士兵和专用道具片段排除。御伽有 4 个原始事件引用不存在的第 11 个渲染器；本版保留原始事件记录，仅忽略这些无目标的事件，不将它们错误映射到脸部或其他网格。证据：`wave9-otogi-bindings.json`、`wave9-body-clip-scope.json`。

## 0.1.19 来源补充

新增 16 个外观／形态包并扩充原版动作，官方资源版本 JP r96 patch 33。下载仅限所需资源包，文件大小与 CRC 已核验。

优香睡衣、夏乐队场景版的骨骼轨道恢复使用角色模型页面的社区原版提取文件，版本固定为 BlueArchiveModels 提交 `525ae0faeb0a89f54ef4023f3be3692dcb529e51`。官方模型、贴图、口型及显隐事件保留；未使用同人重建模型。包描述中包含动画参考 URL 与摘要。恢复报告分别为 `test-results/yuuka-pajama-reference-recovery.json` 和 `test-results/natsu-nonweapon-reference-recovery.json`。完整逐项来源与限制见 [模型与动作核对](MODEL-AUDIT.md)。

## 0.1.18 新增十位角色（2026-10-21）

新增日富美、瞬、心奈、小春、美游、圣娅、胡桃、柚鸟夏、樱井美代、泉奈，共 19 个外观包。逐项官方模型前缀见 `scripts/roster-wave7.json`；服装对应关系见随包《服装核对表》。模型和动作来自官方 JP r96 patch 33 资源，按角色获取，并校验目录中的文件大小和 CRC；没有使用同人替代模型。

新增动作的骨骼轨道、关键帧时间、插值及原始事件与导出数据逐项核对。泳装瞬幼女形态的脸部切换按原版目标索引映射到两张脸，避免误隐藏光环。泉奈原版两段旧动画中的索引 4 显隐事件在当前仅有四个渲染器的预制体中没有目标：记录为未解析旧事件，保留其他事件和原始动画，不随意绑定到其他物体。

乐队夏的糕点道具有重合顶点分别属于不同骨骼，导出合并顶点会丢失绑定信息；已从原始顶点、三角形和单骨骼索引重建。日富美取景排除原始动画缩到几乎不可见并停在脚下远处的武器。泉奈恢复正常整体缩放，胜利动作保留完整跳跃，使用独立动作镜头平滑拉远并在动作结束后恢复；没有改写跳跃轨道。

13 组新增家具依官方时间轴和完整预制体合成，泳装小春场景包含泳装花子同伴。家具预制体中同名的内部网格与根节点以 PlayableDirector 区分；材质槽读取原始渲染器覆盖值。新增家具与普通角色模型分别存储。Unity 专用粒子、声音和完整水面着色效果仍未移植。

核对快照：`.assets/students-audit-2026-10-21.json`、`.assets/catalog-audit-2026-10-21.json`。可复现脚本为 `prepare-wave7.py`、`verify-wave7-resources.py` 及家具转换脚本；验证记录在 `test-results`。旧版 65 个角色包保留，未重新转换。

## 已交付角色

芹香（Serika Original）SD 模型及咖啡厅、胜利、编队等动画，来自游戏官方 JP Windows 资源，非同人重建模型。

- 资源目录：<https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json>
- 本次目录：`r96`，`PatchVersion 33`。
- 提取器：<https://github.com/ZM-Kimu/Blue-Archive-Asset-Downloader>，固定提交 `ac4598977abb46cf11574446fe799aed59842b3a`。
- 导出器：该项目配套的 AssetRipper 补丁版，导出 GLB 而非重建模型。
- 下载包按目录中的大小和 CRC32 校验；逐个解包后的 bundle 再校验大小和 CRC32。
- 本地原始下载记录：`.assets/acquisition.json`；导出结果：`.assets/serika-result.json`。

所用分包为 `FullPatch_026.zip`、`FullPatch_088.zip`、`FullPatch_090.zip` 和 `FullPatch_Prologue_000.zip`。普拉娜候选资源另来自 `FullPatch_037.zip`；其最初导出缺少动画；0.1.4 已通过绑定原版 Timeline 动画修复，详见下文。

交付 `characters/serika/model.glb` 含 3 个网格、2 个皮肤绑定、7 张内嵌贴图，动画如下：

| 用途 | 原版动画 |
| --- | --- |
| 待机 | `Serika_Original_Cafe_Idle--d69cb34870957c8d` |
| 点击互动 | `Serika_Original_Cafe_Reaction--35ea8b5684584e69` |
| 原地走路 | `Serika_Original_Cafe_Walk--755e18332209d08f` |

GLB SHA-256：`43dc35c8e64b94bd191df759429599a3f2c6631e80884d255b56db80a76e89af`。

## 适配内容

1. 保留原版网格、蒙皮、骨骼关键帧；原始咖啡厅模型已能导出待机、互动与行走。
2. 游戏顶点颜色实际用于着色遮罩，不能直接视为 GLB 基础色；移除该基础色映射，使用 `KHR_materials_unlit` 显示原贴图。
3. 将眼睛和嘴部的独立三角形分为标准 GLB 材质。嘴部使用共享贴图 `Character_Mouth`，保留 `_MouthTileTex` 的缩放，按角色 MonoBehaviour 中 MouthDefaultUV=(0.25, 0.5) 设置默认 UV，再按原始动画事件平移采样位置，保留透明遮罩。
4. 原导出器遗漏静态光环网格；从原版 `Serika_Halo` 网格恢复到 prefab 已有的 `Serika_Original_Halo` 节点，使用原版光环贴图与材质颜色。
5. 所有数据和贴图内嵌到 GLB。运行时不加载网络地址。

此转换没有导出游戏专用着色器；光照、描边和其他材质效果与游戏并非逐像素一致。骨骼动作和嘴部事件均来自原版资源。0.1.0 误用了共享材质的预览 UV；0.1.1 暂时使用固定闭嘴；0.1.2 恢复角色脚本的默认 UV，并播放官方口型事件。

## 复现

需要 Python 3.12、.NET 10 SDK，及指定提交的提取器。将提取器克隆到 `tools/asset-downloader`，建立 `.venv` 后安装该项目及 `UnityPy`、`Pillow`。

1. 执行 `scripts/fetch-candidates.py`，获取固定目录中候选角色与共享贴图的分包，完成 CRC32 校验后只保留相关 bundle。
2. 按提取器官方工作流准备其 AssetRipper 补丁源码，构建 `AssetRipperExporter.csproj`，输出到 `.assets/exporter`。构建需通过 `-p:AssetRipperSource=<补丁源码目录>` 指定源码。
3. 执行 `scripts/export-candidates.py`，生成 `.assets/exported` 下的候选 GLB。
4. 执行 `scripts/prepare-serika.py`，生成经过上述适配的角色包。
5. 执行 `npm run verify-assets`，核对文件结构、内嵌资源、动画及哈希。

资源服务地址可能随版本变化；此脚本固定到本次核验的目录，不自动追踪最新版本。原始分包、工具缓存不随程序发布。

游戏素材版权属于 NEXON Games／NEXON／Yostar 等原权利人；工具代码的许可不改变游戏素材的权利归属。本次成品用于用户的本机自用。

## 0.1.2 官方动作与口型事件

额外启用 Victory_Start（胜利）、Normal_Reload（换弹）、Formation_Pickup（编队提起），共 6 个动画。模型来源从咖啡厅子预制体改为同一角色完整 Serika_Original 导出，保留同一原版骨架。

原始 AnimationClip.m_Events 中的 SetMouthTile 已由导出器保存在 scenes[0].extras.BAAD_unity_animation.clips[].events，旧播放器未读取。适配脚本将事件时间和整数参数写入角色描述，按当前动作时间选择口型，不另造时间轴。

咖啡厅互动：0 → 402、0.13333334 → 701、0.86666673 → 703、1.1666667 → 602、2.4 → 402。胜利动作另有 3 个事件，编队提起有 1 个事件。无事件的动作采用默认 402。图集参数按百位为自底向上的行、余数为列换算；402 对应预制体的 (0.25, 0.5) 默认偏移。

已用 UnityPy 直接核对原始 bundle 的 6 组动画事件与 4 个角色预制体默认值，时间误差小于 1e-6 秒；记录在 test-results/mouth-source.json。verify-assets 另核对描述中的事件与 GLB 导出元数据一致。仅解释 SetMouthTile，不执行原始资源中任意脚本或音频事件。

## 0.1.3 新年服装

新增官方 Serika_Newyear，目录 characters/serika_newyear。源资源仍为上述 r96 patch 33 官方目录，从已缓存 FullPatch_026、088、090 中按 CRC32 核对并选取 11 个相关 bundle，没有下载整库。

资源含原版新年衣服、头发、扫帚、御币、武器及其蒙皮与动画。原始材质明确引用 Serika_Original 的脸部、眼睛、光环贴图；武器 SkinnedMeshRenderer 引用 Serika_Original_Weapon 材质，适配时据此补齐依赖，并使用新年服装自身的眉毛颜色。不是将新衣服贴在原版骨架上重建。

保留 Cafe_Idle、Cafe_Reaction、Cafe_Walk、Formation_Pickup 四个动画及其 SetMouthTile 事件。新年 MouthDefaultUV=(0,0.375)，默认图集基准为 300；待机动画在 0 秒指定 704，所以实际待机口型按 704 显示。

GLB SHA-256：a1d5e39d00547f800ab3748f1d85df930e414e7d5a1705f28583a317ea442102。共 5 个网格、4 个蒙皮绑定、9 张内嵌贴图。

复现：先完成原版资源步骤，再依次执行 scripts/fetch-candidates.py --newyear、scripts/export-candidates.py --newyear、scripts/prepare-serika.py --newyear。新年包复用的原版贴图必须保留在原始导出目录。资源记录 .assets/newyear-acquisition.json；原始嘴部事件核对记录 test-results/mouth-source-newyear.json。技能粒子效果与音频仍不启用。


## 0.1.4 全部目标角色与服装

| 角色包 | 官方资源名 | 动作数 | 模型类型 |
| --- | --- | --- | --- |
| 普拉娜原版 | Plana_Original_Mesh | 5 | 正常比例 NPC |
| 纯子原版 | Zunko_Original | 6 | SD |
| 纯子新年 | CH0192 | 6 | SD |
| 芹香原版 | Serika_Original | 6 | SD |
| 芹香新年 | Serika_Newyear | 4 | SD |
| 芹香泳装 | CH0189 | 4 | SD |

范围核对：当前 SchaleDB 英文、日文角色表（https://schaledb.com/data/en/students.json 与 https://schaledb.com/data/jp/students.json）和本次官方 r96 patch 33 目录。纯子只有原版、新年；芹香有原版、新年、泳装；普拉娜只找到原版 NPC。未把 2D 剧情立绘换装列成可用 3D 服装，也不保证未来游戏版本不会增加新服装。

新增分包 FullPatch_010、086、089，并复用 026、090 和既有普拉娜 037；只抽取所需 bundle。下载与 bundle 的大小、CRC32 记录见 `.assets/roster-acquisition.json`。每个最终 GLB 的 SHA256、骨骼及动画统计见 `test-results/assets.json`，以该文件为当前版本准据，前文旧哈希仅属历史版本。

纯子与泳装芹香：`scripts/prepare-roster.py` 从原版材质指针补齐贴图，分离嘴部图集并保留 SetMouthTile；按官方 Enable/DisableChildRenderer 事件切换脸部，避免多个表情叠加。CH0192 动画保留旧渲染器索引 9/10，与当前 prefab 遍历顺序不一致，适配器显式映射至 Face01/Face 两个表情网格；实际待机及提起画面已检查。技能粒子实例化事件不执行。

普拉娜：`scripts/build-plana-exporter.py` 在隔离的导出器源码副本中，把原始 AroPla_Cacha_02 动画绑定到原始 Plana_Original_Mesh 骨架；没有重新制作动作。`scripts/prepare-plana.py` 保留五个可独立播放片段、原脸部网格、眼睛贴图与可见性曲线；独立光环以官方初始变换为基准附到头骨，并向上校正 0.26 模型单位以露出 NPC 头发，随角色运动。此模型是正常比例 NPC，不冒充 SD 小人，也没有伪造 Formation_Pickup。待机持有的平板及其他附件保留原版资源。

复现新增包：先完成既有依赖，再运行 `scripts/acquire-roster.py`，分别运行 `scripts/prepare-roster.py junko`、`junko_newyear`、`serika_swimsuit`。普拉娜额外构建上述导出器，以 `.assets/plana-animated-request.json` 导出到 `.assets/exported/plana-animated`，运行 `scripts/prepare-plana.py`（需要 numpy）。最后运行 `npm run verify-assets` 与 `node scripts/roster-test.mjs`。运行成品仍不需要这些提取工具。


## 0.1.5 光环跟随

检查五套 SD 角色的原始 HaloRoot：没有独立光环变换动画轨道，而是 MonoBehaviour 的 FollowTarget 指向 Bip001 Head。原版组件还保存 TargetRelativePosition/Rotation、ClampMinOffset/ClampMaxOffset、FollowPositionPower、FollowRotationPower 等参数。旧版只恢复静态网格，因此角色动作时光环保持在固定位置。

运行 `scripts/prepare-halo-follow.py` 可从原 bundle 提取这些参数，写入 GLB 的 scenes[0].extras.BA_halo_follow；原始核验记录为 test-results/halo-source.json。播放器使用原偏移和限位，按帧率无关的插值实现跟随。该实现依据序列化参数重现跟随行为，不声称与游戏编译脚本逐帧完全一致。普拉娜沿用其头骨绑定，随原版骨骼动画运动。

重新生成五套 SD GLB 后需再次执行该脚本，最后运行 verify-assets。所有参数随 GLB 内嵌，运行时不连接网络。


## 0.1.6 提起循环与面部核验

直接读取 Unity AnimationClip.m_MuscleClip.m_LoopTime，五套 SD 服装的 Formation_Pickup 均为 true。此前播放器统一 LoopOnce/clampWhenFinished，导致拖动约 0.67～14.33 秒后不再播放新姿势；现在拖动时使用 LoopRepeat，菜单单次预览仍结束后返回待机。没有合成新的提起动作。

scripts/audit-expressions.py 核对了六包全部已启用动作中的眉毛、眼部、嘴部骨骼、变形目标、顶点蒙皮权重、口型事件及非骨骼曲线；结果写入 test-results/expression-source.json。眉毛/眼睑使用原版骨骼轨道，嘴部主要使用 SetMouthTile；本批启用片段没有变化的 morph weight 轨道。眉毛轨道不只是存在于文件里，其目标骨骼确实影响蒙皮顶点。

scripts/expressions-test.mjs 在真实播放器采样待机、互动，以及普拉娜眨眼/微笑，确认眉毛和眼部节点变换实际变化，并记录口型和可见性变化。结果见 test-results/expressions.json。

纯子原版 Cafe_Idle 没有变化的眼部/眉毛轨道，因此该动作中不自动眨眼；其互动、行走与胜利有原版面部动画。部分短提起动作的脸部本来就是固定表情，循环不会凭空增加眨眼。普拉娜的 Idle 也没有眨眼，但有独立原版 Blink 片段：现由桌宠在空闲 6 秒后触发，时间安排属于本程序，不宣称是原游戏调度。

未移植的部分仍包括原版技能粒子/音频、专用着色器材质效果。审计记录中的 material.path_0x8F353710_kPSVSpL 等未解析曲线没有冒充已恢复；骨骼眉毛/眼睑、口型、面部可见性和光环跟随分别验证。


## 0.1.7 新增角色与服装

按本地已校验的 r96 Patch 33 官方目录及角色表，共新增 12 套，原有 6 套保留。光、望在该目录中只有原版；不将 2D 图片或同人模型算作可用服装。

| 角色包 | 名称 | 原始模型 |
| --- | --- | --- |
| `iori` | 依织 · 原版 | `Iori_Original` |
| `iori_swimsuit` | 依织 · 泳装 | `CH0064` |
| `mutsuki` | 睦月 · 原版 | `Mutsuki_Original` |
| `mutsuki_newyear` | 睦月 · 新年 | `Mutsuki_Newyear` |
| `mutsuki_dress` | 睦月 · 礼服 | `CH0246` |
| `kisaki` | 妃咲 · 原版 | `CH0139` |
| `kisaki_swimsuit` | 妃咲 · 泳装 | `CH0356` |
| `hina` | 日奈 · 原版 | `Hina_Original` |
| `hina_swimsuit` | 日奈 · 泳装 | `CH0063` |
| `hina_dress` | 日奈 · 礼服 | `CH0230` |
| `hikari` | 光 · 原版 | `CH0242` |
| `nozomi` | 望 · 原版 | `CH0243` |

获取记录：`.assets/expansion-acquisition.json`。复现：`scripts/acquire-expansion.py`、`prepare-roster.py <角色包>`，最后运行 `prepare-halo-follow.py`。导出时加载共享材质／纹理依赖，避免缺失材质被合并。妃咲椅子共享贴图来自 FullPatch_001.zip 的 `my_event072_throne` 贴图 bundle，CRC32 2739437791。

新增各套保留原版嘴型事件、眼睛及眉毛骨骼、可见性曲线和光环跟随参数；提起片段的原始循环标志均为真。礼服睦月和原版妃咲各提供 4 个已绑定动作，其余新增服装各 6 个。菜单仅展示已绑定动作。运行器仍不复现粒子、音频和全部 Unity 专用着色器效果。


## 0.1.9 新增资源与修正

本次增加 16 套官方服装，映射见 `scripts/roster-wave3.json`：梓 2、真纪 2、小雪 2、玛丽 3、玲纱 2、宫子 2、佳代子 3。来源仍为 JP r96 patch 33，并非同人模型。按指定角色下载分包，记录在 `.assets/wave3-acquisition.json`。

体操服玛丽共用 CH0184_GymProp 材质与贴图，已从官方 CH0184 依赖补齐；记录在 `.assets/mari-dependency-acquisition.json`。小雪两套服装共用 Izuna_Original 包中的嘴部图集。重建入口 `acquire-wave3.py` 包含这些依赖，之后逐套执行 `prepare-roster.py`，最后执行 `prepare-halo-follow.py`。

新年睦月原嘴部网格混合使用零／非零顶点透明度。旧转换漏掉 6 个三角形，导致其误采样眼睛贴图；现按完整连通 UV 区域分离嘴部，未删掉原模型几何。露营真纪道具原网格只有单根骨骼索引、无权重通道；现按原网格位置恢复单骨骼 100% 权重，纠正导出器生成的错误混合权重。修复名单记录于 GLB extras.BA_rigid_skin_repairs。

眼睛追随是程序提供的可选轻微瞳孔位移，不宣称是游戏原版眼神跟随逻辑。原版眉毛、眼睑和嘴部事件仍由动画驱动。技能粒子、描边和专用着色器仍未完整复刻。

妃咲常服的椅子、桌子、麻将和武器同样恢复原版单骨骼权重。原版提起通过 bone_accroot 缩放隐藏道具；程序不再对进入提起动作做 0.18 秒淡入，防止中间缩放状态显露黄色椅子。没有删除椅子或修改原版动画关键帧。


## 0.1.10 资源修复

玲纱原版及小雪原版／睡衣的 AniEvt_EnableChildRenderer / DisableChildRenderer 事件保留原始时序，改为映射至实际的两套脸部网格。此前直接按当前 prefab 枚举顺序取编号，会误切正常脸、光环或道具。映射见 prepare-roster.py 的 face_event_layouts。

小雪两套官方 EyeMouth 材质的 _MouthTileCols 与 _MouthTileRows 均为 4；角色描述增加可选 mouth.columns / rows，老包默认 8。转换与播放均使用原材质的图集尺寸。

玛丽原版 Cafe_Idle 使用原始 EulerRotation 轨道，旧导出器仅输出四元数轨道，造成缺失旋转而呈 A-pose。scripts/build-euler-exporter.py 在隔离目录构建补丁版导出器，采样原始 Hermite 曲线为 60 FPS，按原曲线 RotationOrder 转成四元数，并保留相邻四元数符号连续。玛丽的 XYZ 旋转顺序不能用默认 ZXY 代替。未替换为互动动画，也未手工重做姿态。

重建玛丽：先 build-euler-exporter.py，再用 .assets/euler-exporter/AssetRipperExporter.dll 执行 .assets/mari-request.json，随后 prepare-roster.py mari 与 prepare-halo-follow.py。重新下载脚本已选择该补丁版导出器。


## 0.1.11 道具过渡

本版未删除或改写原版动画，也没有永久隐藏椅子。独立道具蒙皮与身体／脸部共用的骨骼排除在道具修正之外。身体保留 Three.js 局部 TRS 混合；道具在角色坐标系中混合完整骨骼矩阵，避免父骨骼 0.001 倍与子骨骼补偿放大在普通局部混合中产生巨大中间尺度。原版片段中的道具运动及显隐事件仍照常播放，过渡结束恢复原片段的精确姿态。

源代码：`src/prop-transitions.ts`；全量资源审计：`node node_modules/tsx/dist/cli.mjs scripts/audit-prop-transitions.mts`。审计比较每个道具骨骼的过渡尺寸与两端原始姿态，涵盖待机与每个可选动作的双向切换及三个起始时刻。


## 0.1.12 新增角色（2026-10-18）

新增 11 套官方资源，清单与内部编号见 `scripts/roster-wave4.json`。小桃、小绿各有原版／女仆，爱丽丝有原版／女仆／临战，凯伊为原版，时有原版／兔女郎／临战。服装名称参考[官方女仆与兔女郎公告](https://bluearchive.jp/news/newsJump/453)及[凯伊、爱丽丝临战公告](https://bluearchive.jp/news/newsJump/628)；模型、贴图和动画实际来自既有 JP r96 patch 33 官方资源目录。

- 下载和 CRC 校验证据：`.assets/wave4-acquisition.json`；只提取目标角色及必需依赖。
- 时原版使用 `CH0187_CafeOnly` 官方预制体，避免把战斗机甲作为咖啡厅服装显示；该预制体没有的战斗身体切换事件不套用到咖啡厅身体。
- 凯伊道具与临战时武器存在位置重合但骨骼不同的顶点，使用原始位置、UV 和法线联合确定单骨骼绑定；不猜测权重。
- 爱丽丝等光环不使用原始顶点色去乘暗贴图；同名发光／描边材质优先按当前预制体引用选择。
- 光 `CH0242_Cafe_Idle` 在 0 秒调用 `SetHorizontallyFlippedMouthTile(602)`；玲纱 `CH0167_Cafe_Idle` 在 0 秒调用 `SetMouthTile(704)`。玲纱材质保存的 X 缩放为 -0.5，转换时先规范化基础 UV，再由动画事件控制是否水平翻转，避免越过图集格子。
- `SetMouthTileToDefault` 也按原始默认值处理；口型是否翻转随每次普通／翻转命令重置，不继承前一个动作。

重建：运行 `scripts/acquire-wave4.py`，逐项运行 `scripts/prepare-roster.py <id>`，再运行 `scripts/prepare-halo-follow.py` 与 `scripts/refresh-mouth-events.py`。Euler 导出器由 `scripts/build-euler-exporter.py` 构建。

## 0.1.14 家具与同步互动（2026-10-19）

从同一官方 JP r96 patch 33 资源中解析咖啡厅 PlayableDirector 的学生、家具与多人分组绑定，新增 48 件家具、64 组可选互动，覆盖 46 个既有角色包。普通模式的 55 套 GLB 和缩略图与 0.1.13 逐字节一致，描述文件仅新增家具列表。

每个家具场景独立保存为 GLB，动作、口型、显隐和光环保留各参与者的原始绑定。复用公共材质时按实际预制体引用补齐，保留原始 alpha 混合与颜色透明度；未把所有家具材质统一当作透明裁切。七位必需同伴只随家具出现，不扩充可选角色衣橱。

临战爱丽丝窗户使用 `FX/Stencil/Mask Simple` 与 `MX/E-CafeStencil`。核验原始 Shader 后保留其不输出颜色、GreaterEqual／Replace 写入和 NotEqual 测试规则，按原材质顺序绘制；辅助网格不参与场景取景和鼠标命中。没有删除窗框或用白色网格代替遮罩。官方 Shader 获取记录见 `.assets/furniture-shader-acquisition.log`，状态快照见 `test-results/retractwindow-shader.json` 与 `retractwindow-out-shader.json`。

家具列表、来源、重建步骤及尚未复现的粒子／音效范围见 [FURNITURE.md](FURNITURE.md)。审计记录为 `.assets/furniture-adaptation.json`、`test-results/furniture-coverage.json` 和 `test-results/furniture-wardrobe-parity.json`。

## 0.1.13 星野、白子与爱露（2026-10-18）

新增 10 包，映射见 `scripts/roster-wave5.json`。模型、贴图、骨骼及动画来自官方 JP r96 patch 33。衣装名称与实装情况另参考[临战星野与白子 Terror 官方公告](https://bluearchive.jp/news/newsJump/628)、[爱露礼服公告](https://bluearchive.jp/news/newsJump/538)、[爱露新年公告](https://bluearchive.jp/news/newsJump/513)。

- 星野：Hoshino_Original、Hoshino_Swimsuit、CH0258_01（临战）。CH0258_01 和 CH0258_02 使用相同的咖啡厅待机、走路与互动片段；攻防模式按一套衣装计数，保留 CH0258_01 原版提起与胜利动作。
- 白子：Shiroko_Original、Shiroko_RidingSuit、CH0188（泳装）、CH0263（Terror）。Terror 的身体、头发、脸部和眼睛纹理共用官方 NPC EN0002 资源；EX 透明部件还引用绫音原版纹理，均按原材质引用补齐。
- 爱露：Aru_Original、Aru_Newyear、CH0240（礼服）。各包保留原版面部骨骼和嘴型事件。
- 星野原版部分材质引用公共 effectsfreezed-material 资源；补齐后重新导出，没有用单色材质顶替。

下载分包及 CRC 校验记录：`.assets/wave5-acquisition.json`，额外依赖定位记录：`.assets/wave5-extra-dependencies.json`。获取入口 `acquire-wave5.py` 支持指定包名及 `--assets-only`；正式重建时先获取所需资源，再逐包执行 `prepare-roster.py`，最后执行 `prepare-halo-follow.py`。

全部角色服装清单见 [COSTUMES.md](COSTUMES.md)。核对以重新获取的 2026-10-18 日服已实装学生数据为范围，普拉娜 NPC 单独列出；不把同衣装的战斗模式、家具姿势或仅有立绘的装束当成独立 SD 服装。

## 0.1.16 铃美（原版／魔法少女）

新增 `Suzumi_Original` 与 `CH0325` 两套官方模型，规格保存在 `scripts/roster-wave6.json`。原版按需取得 FullPatch_026、FullPatch_090、Prologue_000、Prologue_001 中的角色及依赖；下载／CRC 记录见 `.assets/wave6-acquisition.json`。原版 AnimatorOverrideController 引用共享序章控制器，补齐原始外部 CAB 后导出六个动作，未使用其他角色动画代替。

魔法少女铃美从已有官方家具同伴源资源重新转换为公共角色包；两套均保留默认口型与原始口型事件、脸部骨骼、原始提起循环和光环跟随参数。`test-results/wave6-halo-source.json` 保存光环来源。魔法少女两组家具时间轴来自官方 210385 家具，其中一组包含魔法少女玲纱；原版在本次数据映射中没有对应家具。

泳装日奈家具的 `my_poolparty_01_b_poolwater` 使用官方 `MX/Water` 着色器，通用 `_Color` 不是实际水色。本版按 `_BaseColor` = (0, 0.8226874, 1, 0.5450981) 映射为 GLB 半透明水面；保留原始几何体。这是原始颜色与透明度的兼容显示，尚未移植 Unity 的折射和水波。`test-results/furniture-alpha-audit.json` 对照源材质检查颜色；`test-results/release-delta.json` 证明原有 55 套普通模型、63 组其他家具模型及其描述／缩略图均与 0.1.15 一致。

## 0.1.17 剧情／装备／光环外观（2026-10-21）

新增 8 包的官方模型映射见 `scripts/roster-extras.json`，精确片段映射见 `scripts/extra-costume-profiles.json`。共 7 项服装／装备外观与 1 项光环变体，均来自 JP r96 patch 33 已核验源包；不删除旧模型附件来伪造剧情服装。

小桃／小绿使用 NP0267／NP0268 的原模型与各自互动。日奈睡衣使用 Player_NP0009 内的 Field_Player_NP0009；原预制体 Animator 没有绑定控制器，通过导出清单显式绑定该场景角色自身的 Field_Player_NP0009_* 片段，保留完整路径、骨骼、口型和显隐事件。没有套用其他日奈服装的提起动作。时机械装甲采用原 Boss 模型；凯伊与爱丽丝选用对应剧情模型，保留持武器姿态。

重建：先保留审计获取的 `.assets/selected`、`.assets/costume-audit`、`.assets/costume-variants` 源 bundle，再运行 `export-extra-costumes.py` 和 `prepare-extra-costumes.py`。导出使用现有包含 Euler 旋转支持的本地 exporter 与显式片段绑定接口；输出首先位于 `.assets/extra-costume-ready`，验证后才复制到 `characters`。`extra-costumes-binding-evidence.json` 记录绑定清单；`test-results/extra-costume-halos.json` 记录各自官方光环跟随参数。

小桃／小绿的场景互动片段带有固定场景放置偏移。转换时只将 Bip001 平移轨道的固定偏移对齐各自待机首帧，保留动作中的位移差、三次插值切线和所有旋转／缩放轨道，避免互动时移出桌宠窗口。每个偏移记录于 GLB 的 `BA_scene_placement_offsets`；`verify-extra-costumes.py` 逐通道对照原导出数据，`audit-extra-framing.mts` 检查各动作六个时间点的取景边界。

新增包均保留原版面部骨骼、嘴型图集与事件。场景／战斗动画没有的桌宠提起动作不合成、不冒名；这些包拖动时保持待机，动作面板显示说明。粒子、攻击弹道与声音不包含在此次适配范围内。
