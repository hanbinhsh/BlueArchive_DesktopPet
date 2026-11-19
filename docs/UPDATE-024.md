## 0.2.4 模型修复与家具补充（2026-10-29）

修复青叶脸部显隐事件错位、温泉千夏遗漏的动态口型，以及制服妮露头发的透明材质。保留全部原有动作曲线。

新增 54 项官方家具互动，累计 140 项；角色数量仍为 148 套外观。新增场景经过实际加载、两个时间点截图和每段 121 个采样时刻的几何检查。35 项核心测试通过；实际免安装成品复测三套角色通过。未进行本版 30 分钟稳定性测试。

尚未完成：御隐的作战桌动画启用一个旧版编号的物体，当前模型中尚未对上，未发布该场景。10 月 28 日的日富美／梓赛车服装仍在原版资源适配核对中，本包没有加入或宣称支持。

资源与核对记录：
- 模型来源：原始 JP r96 patch 33，材质和原始事件保留。
- 1.74 新目录：https://prod-clientpatch.bluearchiveyostar.com/r97_s71wespocqarqo4ywey2/Windows_PatchPack/BundlePackingInfo.json ，已下载目标新增模型候选的独立资源，尚未发布。
- 社区模型页 2026-10-29 快照中，日富美、梓仍仅列原版和泳装。
- 新版客户端的表格索引构建在 Cpp2IL 下载阶段失败；不据此断言新服装资源不存在。
- 测试记录：visual-repair-regression.json、furniture-update-assets.json、furniture-update-adaptation.json、update024-packaged-smoke.log。
