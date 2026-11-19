# 037 已完成的修复与验收（2026-11-17）

0.2.16修复和回归已完成。27项资源变更：resources037-installed(17)、resources037-blocks-installed(4)、resources037-persistent-installed(6)，变更前备份.assets/pre037；人物和家具基础几何核验通过。

82项TS、24项Python测试及类型、构建、资源检查通过。145家具/435帧遍历、15页审图完成；后续10个资源另补38帧，专项43帧、艾米3循环/模拟暂停恢复、106预制体常驻粒子排查通过。最终unexplained为空。

实际0.2.16断网长测1801.496秒、48轮、46次切换，平均29.46 FPS，零捕获错误；末两个五分钟内存均值916.51/886.78 MiB，通过增长判据。release037-soak与resource-summary保存原始证据。

交付脚本package-release037.py校验测试程序和599资源哈希，生成Windows免安装包与源码包，再做ZIP CRC及逐文件SHA-256检查。交付结果以test-results/release037.json为准。源代码包不重复收录游戏缓存，复制免安装包resources/characters即可构建。

修复明细与精度限制见AUDIT-037.md。测试使用独立配置，没有改动日常设置和启动项；未做真实登录启动/物理多屏拔插。旧0.2.15包保留。
