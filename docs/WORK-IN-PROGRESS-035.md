# 035 当前工作进度（2026-11-15，发布验收中）

用户要求持续修复，不要让其反复发“继续”。自动审批期间曾两次返回额度错误，最新重试已恢复，**目前不应按额度阻塞停工**。没有开启子代理。

## 已合入并打包

- `characters` 已安装 36 个改动文件（31 GLB、5 个朝向 JSON）。备份 `.assets/pre035`，清单 `test-results/resources035-installed.json`；不要重复运行要求 old 哈希的首次安装命令。
- 原角色／家具几何逐项比较无变化，资源引用验证通过：`stage035-verification.json`。
- 实际候选 `release/v0.2.14-final/win-unpacked/BA Desktop Pet.exe` 已生成；尚未 ZIP 或交付。旧 `release/v0.2.14` 是034候选，不能混用。
- 新修复记录 `docs/AUDIT-035.md`，README指向它；package extraFiles 已含035文档。说明中的成品验收／30分钟仍待更新。
- 最后代码修改是 billboard 的旋转顺序：`inverse(parentWorld) * cameraWorld * authoredRotation * Y(pi)`。此前 Y(pi) 放在 authored 前会反转 roll，导致忧黄色扇形跑进光环。最终 `glyph035b` 图像已核验，忧三扇形位于脸侧，其他7场景未见新问题。`finalcards035` 八云金卡、红叉同样核验在气泡内。

## 当前验证

- 75 项 TS 测试、17 项 Python 测试、类型检查通过（最后日志 unit035/type035/python035）。
- `cloud035-runtime.json` complete=true：真实循环3次、边界检查26次、最大位移0.00881793；模拟 powerMonitor suspend/resume 暂停恢复通过。源码测试使用独立配置。
- 原问题逐项截图：detail035（Airi/Akane/Maki及其他6场景）、stretched035（最终喷火纵向pivot修正）、check035（视角/冰泳池旋转）、glyph035b（最终共用glyph）、finalcards035（最终金卡）。
- 24个官方FxBillboard节点应用于13模型、18入口；billboard035 36张截图已看，未见明显错误。但其中多数不是气泡出现时刻，另有定时glyph测试。
- `packaged035` 实际免安装包正在离线遍历145家具×3帧：会输出 `packaged035-runtime.json`。日志 `packaged035-preview.log`。主进程脚本session 44351（可能已完成）。
- 打包资源哈希比对脚本session 71902（可能已完成），输出 `release035-resources.json` / `release035-verification.json`，记录app.asar哈希。最终ZIP必须验证这些哈希。

## 必须继续的工作

1. 等145入口成品遍历完成，检查全部错误日志、图像 contact sheets；修任何发现的回归，修改代码后必须重建并重测对应项。
2. 对艾米旋转水面、心奈咖啡摇杯、桔梗站坐水面做连续/密集回归（已有多帧，但尚无最终包动态测试）。对旧美祢倒水杯口遮挡、日奈沙发和妃咲衔接做重点复测。
3. **实际候选包30分钟长测尚未开始**。使用 `scripts/release034-soak.mjs`（已支持 BA_SOAK_CASES），设置 BA_SOAK_TAG=release035-soak，BA_SOAK_CASES=test-results/soak035-cases.json，BA_EXECUTABLE=release/v0.2.14-final/win-unpacked/BA Desktop Pet.exe，BA_CHARACTERS=同包resources/characters。19组自动组合覆盖本次问题，cloud53秒可跨角色循环。独立配置，不改日常启动项。不要把034旧长测当作035结果。
4. 在长测期间整理最终验证文档、交付脚本，不进行第二个GPU密集测试以免干扰帧率测量。每分钟左右有意义更新；可分析现有截图和日志。
5. 更新 `docs/VALIDATION.md`、`docs/ASSETS.md`、`AUDIT-034.md`（说明034与035同属最终0.2.14，旧“只更新13GLB”只针对前一子批）。最终版本仍0.2.14。
6. 写新的 `scripts/package-release035.py`，**不要用旧package-release034.py**。它硬编码旧app.asar、旧资源和旧长测。新脚本应以release035验证和完整资源哈希为准，长测实际elapsed>=1800、complete、errors空才交付ZIP。可在验证结束后仅刷新包内文档，不改被测代码/资源。
7. 生成 `release/BA-Desktop-Pet-0.2.14-win-x64.zip` 和源码ZIP，检查ZIP CRC和逐文件哈希，最后自包含中文答复给用户下载路径，说明爱丽丝沙发气泡原始就有旋转、未虚构全游戏光照/私有随机序列。不能宣称逐帧完全等同游戏。

## 实现重点

- `src/particle-streams.ts`按原始m_VertexStreams打包Custom数据；`cafe-smoke.ts`/`furniture-fx.ts`在CPU传uniform，program cache不因排列变化而必须不同，对应测试已改为比较每材质uniform。
- `cafe-particles.ts`：View/Facing镜像与roll顺序、flip保留pivot中心、stretched轴向pivot与leading-tip锚定；不要回退为直接负scale而不补pivot。
- `src/fx-billboard.ts`整组看相机，**group不做Y半周**，单个particle才做几何镜像修正。
- Eimi：`static_fx_meshes.py` + exporter MeshRenderer/nested Timeline，`apply-nested035.py`29曲线；保留源嵌套shader参数动画。
- `apply-infinite035.py`补Hoshino/Eimi/Kikyou/Mine Recorded覆盖轨道；`apply-activation035.py`补Kokona启用区间。
- `fx_hierarchy.py`/`apply-sub-hierarchy035.py` 保留子发射器原始world rotation（额外影响泳装星野、新年佳代子、新年芹香）；Airi从源重建已经应用。
- `src/pool-water.ts`和`apply-pool-water035.py`还原MX/Water。原始三张纹理、D3D证据位于 .assets/water-shaders/MX_Water-*；缺失共享纹理已用ZIP Range精确获取，.assets/pool035-acquisition.json。`glb.py compact`已支持以Tex结尾的自定义texture引用。
- `scripts/furniture-character-view-yaw.json`已同步Kisaki龙椅1、小桃绿木制TV、Rio/Toki战斗场景角度。
- `verify-stage035.py`初次对比依赖旧characters；已安装后重跑要改为读pre035作为baseline。
- `audit-shared-glyphs035.py`准备8场景15帧。因PowerShell Junction失败，改为复制相关角色到 `.assets/fx035-glyph-test`（测试只读资源）。最终runtime用installed/packaged即可，别再写错路径fx035-test-all。
