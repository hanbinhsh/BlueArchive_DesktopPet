"""Write the shipped validation summary only from completed packaged checks."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
runtime=read('test-results/expanded-runtime.json');suite=read('test-results/wave8-runtime-suite.json')
assert runtime['complete'] and runtime['restart'] and len(runtime['results'])==100
assert len(suite)==4 and all(r['exitCode']==0 for r in suite)
for name in ['hold','transitions','expressions']:assert len(read(f'test-results/wave8-{name}.json'))==16
sampled=sum(len(r['played']) for r in runtime['results'])
text=f'''## 0.1.19 新角色、形态与动作库（2026-10-24）

- 新增优香、八云、未花、千世、绮良、忧，合计 11 套服装；补入 5 个装备／场景形态和凯伊白色剧情服的携带待机。共 41 位角色、100 个外观／形态包、2,487 个菜单动作。按 2026-10-23 的学生名单及角色模型页面核对，99 个页面条目中 97 个有本地对应；凯伊 Prototype 与未花 Cut-in 的缺项单独列明，详见模型与动作核对说明。
- TypeScript 检查、17 项核心测试、生产构建通过。全 100 包检查外部资源引用、菜单片段映射、原始事件和表情骨骼；89 个原始提起片段循环标记验证通过。逐动作采样取景边界。优香睡衣、夏场景版使用固定版本社区原版提取文件恢复骨骼轨道，同时保留官方贴图和原版事件，详情见来源说明。
- 与 0.1.18 对比，旧版 459 个常用动作的通道和采样数据、节点、几何、材质、纹理及 79 组家具模型／配置保持一致。本版未增加家具，也未重复逐场景运行全部家具。
- 使用 `release/v0.1.19/win-unpacked/BA Desktop Pet.exe` 和其实际随附资源，在离线模拟下加载全部 100 包；共试播 {sampled} 个非待机动作，包括新增 16 包的全部菜单动作、旧包每类抽样。检查渲染继续、无异常、显式返回待机；重启恢复最后选择的角色。此快速试播不等同于所有 2,487 个动作完整播放至结束。
- 新增 16 包分别进行 23 秒持续拖动采样，检查帧数、有限骨骼边界和稳定窗口尺寸；有提起动画的保持循环，其余保持自己的待机。检查提起／放下混合帧以及互动自然结束后的待机过渡。表情检查覆盖新增 16 包的待机与互动，按源轨道验证眼眉变化，按原始时间事件核对嘴型与水平翻转。
- 面板离线显示 100 张有效缩略图，逐套检查新增 16 包的说明、动作列表、分类、原始名称搜索、收藏筛选与角色切换滚动保持。新增普通动作与部分技能画面截图人工复核。动作名称搜索不影响角色搜索。
- 测试记录：`expanded-runtime.json`、`wave8-panel.json`、`wave8-hold.json`、`wave8-transitions.json`、`wave8-expressions.json`、`expanded-resources.json`、`wave8-pack-source.json`。发布脚本比对成品中全部角色文件、7 个编译文件及说明文档，ZIP 逐文件摘要与 CRC 验证见 `release-0.1.19.json`。
- 限制：本版未重新执行 30 分钟长测、物理显示器热插拔或不同 DPI 实机测试。鼠标测试使用合成输入，不能替代原生 Windows 点击穿透实测。技能粒子、攻击目标、音效和完整场景没有复现；未开放的片段与 2 个特殊模型没有标为已完成。
'''
p=R/'docs/VALIDATION.md';old=p.read_text(encoding='utf8');first,rest=old.split('\n',1)
assert '## 0.1.19' not in old
p.write_text(first+'\n\n'+text+rest,encoding='utf8')
for item in read('package.json')['build']['extraFiles']:shutil.copy2(R/item['from'],R/'release/v0.1.19/win-unpacked'/item['to'])
print('Final validation document written and all seven documents copied')
