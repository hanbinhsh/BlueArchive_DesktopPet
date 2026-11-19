# 0.2.19：十位随机学生增量

状态：已完成并交付可运行文件夹。最终长测1801.583秒、51轮组合、46次角色切换，29.01 FPS，零捕获错误；末两个五分钟内存均值938.55／942.15 MiB。完整验收说明、目录校验和资源清单均已同步，未生成ZIP。

用户当前要求：再加入10位随机未添加学生，并报告还剩多少；默认仅交付可运行文件夹，不创建ZIP。没有授权子代理。

已加入安娜、巴、日向、御坂美琴、桐乃、一花、律、真白、志美子、果穗；15套外观、369个动作、15项家具。实际角色目录169套、4305个动作、165项家具。按2026-11-17保存的日服已实装名单，已加入78/149位学生、未加入71位，普拉娜NPC另列。完整未加入名单为ROSTER-COVERAGE.md；抽取已固定，不重抽。

已完成官方资源转换、Hinata压缩权重修复与逐顶点证明、Shimiko书本共享依赖补全、Tomoe完整靠椅预制体和旗袍提起拼写映射、Kirino原始Matcap子弹材质、家具四方向选定。全部普通动作离线成品播放、重启恢复、五套持续拖动及过渡验证通过；132张表情帧和150张家具帧／30张接触表均已实际查看。

最终文件夹：release/v0.2.19/win-unpacked/BA Desktop Pet.exe。未创建压缩包。

锁定成品：app.asar SHA256 ab75a070238e7ddc5e85bd6e26a4882a672438bb6fd9f0f762936ed2f4fadafe；exe SHA256 66de2b77cc3791145dfe48d7976a62a217d2965f62a35719dffc7f88e2fbc000。676个资源与工作区逐文件相同，其中原616个文件保持0.2.18不变。14个运行文件不变，仅renderer.js增加受材质描述限制的Matcap分支。82项TypeScript、29项Python、类型和资源检查通过。

最终30分钟真实离线长测已结束，记录test-results/release040-soak.{jsonl,json,log}，complete=true。使用release040-soak-cases.json循环15项新增家具、两位无家具的原版角色，以及鹤城、艾米、美祢。运行期间没有重建payload、改动characters或并行启动另一GPU测试。

长测通过后已依次完成：

1. python -X utf8 scripts/complete-docs040.py（写入实际帧率、内存和测试结果）
2. python -X utf8 scripts/finalize-folder040.py（校验payload、同步说明与小型验收证据、生成目录哈希清单；不创建ZIP）
3. 检查exe真实存在、目录报告和来源／覆盖文档，然后更新本进度为完成并回复用户。

不要重复运行install-wave14.py；已经安装并选定默认朝向。源码继续保留在G:/Projects/BA。
