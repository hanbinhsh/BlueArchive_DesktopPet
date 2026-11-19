# 036 最终检查点（2026-11-16）

修复及成品验收已完成，详见 AUDIT-036.md。实际0.2.15离线145家具/435帧回归及30分钟47轮组合长测通过。最终ZIP由 package-release036.py 生成并进行CRC/逐文件SHA-256校验；只有全部校验成功后才写入 test-results/release036.json。该结果文件记录最终交付文件的路径、大小与哈希。

禁止用旧 release/v0.2.14-final 交付本轮修复。新免安装包为 release/BA-Desktop-Pet-0.2.15-win-x64.zip，源码包为对应source.zip。旧版本保留。
