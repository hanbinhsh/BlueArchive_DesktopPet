# 剧情／NPC 外观扩大核对 · 2026-10-20

## 0.1.19 补充形态

新增爱丽丝临战（携带武器）、凯伊原版（携带道具）、凯伊原版（剧情战斗）、时临战（剧情战斗）、夏乐队（场景动作）。另给已有凯伊白色剧情服补入原版携带待机，未重复创建相同服装。小桃、小绿白色外套仍对应模型页面的 Battle 形态。

页面中的凯伊 Prototype 无动画；未花 Cut-in 仅有技能演出，缺少独立桌宠待机。二者不列入可选角色，也不算已适配完成。完整对照见 [模型与动作核对](MODEL-AUDIT.md)。

0.1.18 补充：本次新增的泳装瞬幼女形态使用官方 `CH0355_02`，作为泳装的额外形态独立提供。下文保留 0.1.17 的审计记录；当前总数为 35 位角色、84 个外观包，包含 9 个学生表以外的额外外观。当前名单见《服装核对表》。

**2026-10-21 更新：下列 7 项服装／装备外观与白子 Terror 剧情光环，已加入 0.1.17，共新增 8 包。** 正式包名称和动作见 `scripts/roster-extras.json`、`scripts/extra-costume-profiles.json`，目前合计 65 包。

正式版已绑定小桃／小绿各自的原始互动、日奈睡衣专用场景待机／互动／走路／思考／拾取物品，以及凯伊、爱丽丝、时的对应战斗动作。时轻装、白子剧情光环版有原版提起；其余新增外观没有提起片段，拖动时保持各自待机。白色剧情服等名称用于描述外观，不视为新可招募学生。

**0.1.16 没有收录所有官方 3D 外观。** 之前“无缺项”只表示已安装的角色在可招募学生名单中的服装齐全，不能将它扩大为所有剧情、NPC、战斗或场景外观都已添加。

本次重新获取学生数据，24 位已收录学生对应的 56 个服装／形态包仍然齐全，加上普拉娜共 57 包。官方客户端服务器配置指向的 r96 目录仍为 patch 33，与项目缓存目录逐项相同。逐角色清单见 [服装核对表](COSTUMES.md)。

## 本次补齐的外观

| 角色 | 原版资源 | 外观 | 0.1.17 状态 |
| --- | --- | --- | --- |
| 小桃 | NP0267 | 白色外套、粉色围领、双侧小辫，无猫耳耳机 | 已加入 |
| 小绿 | NP0268 | 白色外套、绿色围领、双侧小辫，无猫耳耳机 | 已加入 |
| 日奈 | Field_Player_NP0009 / NP0009_Body | 场景专用粉色波点睡衣 | 已加入 |
| 凯伊 | CH0335_Carrier / CH0335_Scenario_01 | 白色剧情服，无原版发箍和校服外套 | 已加入 Scenario_01；两模型算同套外观 |
| 爱丽丝 | CH0334_Carrier / CH0334_Scenario | 临战卸下外部装甲的形态 | 已加入 Scenario；属于装备状态差异 |
| 时 | CH0187 的 A 身体 | 轻装战斗形态，与咖啡厅的长裙女仆装不同 | 已加入 |
| 时 | CH0187 的 B 身体 / Toki_CNC_MG_Boss | 带头部护具和大型机械部件的装甲形态 | 已加入 Boss 模型；不另算一套 |
| 白子 Terror | CH0263_Scenario01 | 相同服装、不同光环外形 | 已加入独立光环变体 |

小桃、小绿已从官方包导出实际模型，在隔离的核对目录 `.assets/costume-preview` 渲染，并与用户提供的 BV14HkjBhEEC 视频封面截图核对，外套、围领、辫子和不戴耳机的外观一致。视频网页返回 HTTP 412，核对依据是用户上传的封面截图，而不是声称已观看视频。这里使用外观描述；不把资源代号当成已公布的可招募服装名，也不凭背景推断具体剧情章节。

这两套并非删除原版耳机得到的自制变体；它们有独立的原始身体、头发、脸部网格、贴图和动画。源资产按包及 bundle 的 CRC 核验，记录在 `.assets/costume-audit-2026-10-20-acquisition.json`。

- NP0267：找到 Idle、Walk、Interaction01、Interaction02、Interaction01_Idle 五个源片段。
- NP0268：找到 Idle、Walk、Interaction01 三个源片段。
- 2026-10-20 的核对预览仅绑定 Idle、Walk；0.1.17 已完成两人的上述全部原始互动绑定和成品验证。检查的角色源包中没有找到 Formation_Pickup，因此不提供提起动作。
- 日奈 NP0009 已核实独立身体节点、材质及粉色波点衣服贴图，并使用 Hina_Halo。0.1.17 已绑定专属场景片段，包含待机、互动、思考、拾取物品、走路。
- 凯伊的 Carrier 与 Scenario_01 不只是名字近似：身体几何与材质内容摘要均一致；它们与已安装校服版不同，合并记一套白色剧情服。
- 爱丽丝 Carrier 保留与已装临战版相同的身体／外部装甲网格，但其原始待机片段在 0 秒关闭 `CH0334_Arms_Body`；实际渲染显示没有大型肩部、腿部装甲。Scenario 则提供相似的简化装备外观与持武器姿态。这里按装备形态计缺项，不冒称新推出的可招募皮肤。
- 时的 `CH0187_CafeOnly` 是当前桌宠的长裙女仆装，`CH0187` 包含 A／B 两种战斗身体。`Toki_CNC_MG_Boss` 的 B 身体与 `CH0187` 的 B 身体网格、材质内容相同；Boss 的机械装甲已实际渲染核对。

2026-10-20 的核对阶段只制作隔离预览，没有加入公开 `characters` 目录。2026-10-21 根据用户要求将其正式适配；上文旧预览的限制不代表新增正式包仅有静态或行走动作。

## 已排除的重复服装与附件差异

| 变体 | 实际核对结果 |
| --- | --- |
| 时临战 CH0333_Scenario | 身体几何、衣服材质与已安装 CH0333 相同；动作和道具不同，不计新衣服 |
| 凯伊 CH0335_Carrier2、CH0335_Scenario_02 | 实际渲染仍是已安装原版的发箍、领带、外套与长裤；动作、武器／道具不同 |
| 白子 Terror CH0263_Scenario01 | 身体几何与衣服材质完全相同，但光环外形不同；0.1.17 单列提供光环变体，不计新服装 |
| 星野临战 CH0258_01／02、Enemy／EchelonOnly 与同族 `_en0004` 等 | 引用比较没有检出新的衣服网格／材质组合；不因技术后缀重复计算服装 |

本轮完成 11 组实际网格／材质内容对照，以及 16 张独立渲染视图：10 个技术变体、日奈静态模型、5 个已装基准模型。对照计算包含顶点、UV、三角形、材质参数及解码后的贴图像素，避免仅因 CAB／PathID 不同而误报。核对视图保留源显隐默认值与所选片段的显隐轨道。

### 核对图片

- [凯伊白色剧情服](../test-results/costume-audit_kei_carrier.png)／[已安装原版](../test-results/costume-kei.png)
- [爱丽丝卸甲形态](../test-results/costume-audit_aris_carrier.png)／[已安装临战](../test-results/costume-aris_battle.png)
- [时轻装战斗](../test-results/costume-audit_toki.png)／[机械装甲](../test-results/costume-audit_toki_boss.png)／[已安装女仆装](../test-results/costume-toki.png)
- [白子 Terror 剧情光环](../test-results/costume-audit_shiroko.png)／[已安装光环](../test-results/costume-shiroko_terror.png)
- [日奈睡衣静态模型](../test-results/costume-audit_hina_static.png)

## 核对范围与结论

本次按全部 24 位已收录学生的官方代号、名字，以及已确认的 NP0009／NP0267／NP0268，扫描了 162 个相关预制体 bundle，得到 366 个相关根预制体（包含重复包装、特效和场景对象，并非 366 套衣服）。另有场景玩家／NPC 预制体清单。记录见 `test-results/costume-source-variants.json`、`test-results/costume-prefab-inventory.json` 和 `.assets/field-prefabs-audit.json`。

**审计发现的上表 7 项服装／装备形态和 1 项光环变体现已加入。** 这 7 项不是 7 套新可招募皮肤。已完成上述有差异的具名技术变体核对，但没有将无法按已知角色代号关联的所有 NPC、技能演出资源或仅有 2D 的插图统一审完，因此不承诺全资源库绝无其他外观。

## 来源与复核

- [官方资源目录](https://prod-clientpatch.bluearchiveyostar.com/r96_nvji95owgkbcxlmkb8mi/Windows_PatchPack/BundlePackingInfo.json)：保存为 `.assets/catalog-audit-2026-10-20.json`。
- [SchaleDB 学生数据](https://schaledb.com/data/en/students.json)：社区整理的可招募名单，保存为 `.assets/students-audit-2026-10-20.json`，不是 NPC 全集。
- 核对报告：`test-results/costume-extras-2026-10-20.json`。
- 几何／材质对照：`test-results/costume-geometry-comparison.json`；渲染记录：`test-results/costume-variant-render.json`。
- 复核命令：`python scripts/audit-costumes.py --date 2026-10-20`，随后 `python scripts/audit-costume-extras.py`。完整重新提取需依次运行 `audit-costume-variants.py`、`export-costume-variants.py`、`prepare-costume-variant-previews.py`、`compare-costume-geometry.py`，再使用独立的 `costume-variant-preview.mjs` 查看。隔离预览不是正式角色包，不通过普通角色加载器安装。
