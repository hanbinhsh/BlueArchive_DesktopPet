# 0.2.21 已完成

本次固定随机10位：绘里、丽奈、庚、渚、椿、晴、千明、芹娜、亚津子、皋月。新增17套/387普通动作/14家具，实际186套/4692动作/179家具，88/149学生，剩61，NPC普拉娜另列。65个新增文件、旧676个逐文件保持0.2.20。741资源均与成品一致。不要重跑安装，不要把旧expanded-ready覆回。

已交付文件夹release/v0.2.21/win-unpacked/BA Desktop Pet.exe，没有ZIP。最终全文件hash见test-results/release043-folder.json，总大小4011946607字节。docs/ROSTER-015.md及成品ROSTER-015.md含来源、排除片段与完整验收；ROSTER-COVERAGE.md有未加入名单。

离线387动作+重启、147面部姿势、14新+3旧家具170时刻、56四向、17缩略图共390帧/39接触表均已查看。4套23秒拖动与平滑过渡、手机4倍速循环和新FX3倍速循环通过。83TS+29Python、typecheck/全资源检查通过。149851条原始body通道值/时间/插值相同，31模型667530带权重顶点检查通过。

真实1837.098秒稳定性43完整组合/42切换，29.31275FPS，errors[]，内存预热后745.5～1151.2MiB，前5分钟995.9、最后5分钟979.5MiB，通过稳定性检查。详见release043-soak.json/resource-summary.json。

关键修复：Eri全Avatar路径表BA_COMPLETE_PATH_CACHE=1恢复39动画；prepare-roster真实通道guard；Serina医疗包依赖；泳装亚津子相机/闪光3内嵌根和喷泉1常驻根（初审文件须保留），native23粒子补齐；庚4个原始骨骼轨迹拖尾与晴露营原双扭曲火焰分支（原D3D）。仅renderer.js改变，14运行文件保持0.2.20，337旧模型没有启用新分支。一花手机旧GLB保持不变。wave15-final隔离stage已完成，characters是当前正确资源。所有测试独立配置，不改日常设置/启动项，不移动实际鼠标。

最终整理脚本finalize-folder043.py已成功执行。下一次增量以release043-resources.json锁旧资源；不要重新打包压缩文件，AGENTS.md要求默认只文件夹。
