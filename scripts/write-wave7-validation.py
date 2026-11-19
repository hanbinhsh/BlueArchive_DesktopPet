"""Write the release entry only after all six runtime checks complete."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
read=lambda name:json.loads((R/f'test-results/{name}.json').read_text(encoding='utf-8-sig'))
suite=read('wave7-runtime-suite');assert len(suite)==6 and all(x['exitCode']==0 for x in suite)
assert len(read('hold'))==len(read('expressions'))==len(read('transitions-packaged'))==2
baseline=read('wave7-before-size-fix')
assert len(baseline['hold'])==len(baseline['expressions'])==len(baseline['transitions-packaged'])==19
assert len(read('furniture-runtime'))==13
section='''## 0.1.18 新增十位角色及默认大小修正（2026-10-23）

- 新增日富美、瞬、心奈、小春、美游、圣娅、胡桃、夏、美代、泉奈，共 19 个外观包；当前为 35 位角色、84 个可选外观。按 2026-10-21 保存的名单核对已收录角色的实装服装，范围内无缺项；泳装瞬幼女形态另列为额外形态。
- 新增模型的 41,914 条骨骼动画通道、关键帧时间、插值和原始事件与官方导出数据一致。19 套光环参数逐项对照原始组件。普通动作取景共检查 648 个样本；日富美、泉奈另按每动作 61 个时间点验证。日富美的取景排除缩到几乎不可见的远处武器；泉奈待机恢复正常缩放，胜利跳跃通过独立镜头平滑拉远，结束后恢复。实际运行验证正常大小、完整跳跃和镜头复位。
- 84 包结构、表情骨骼绑定和源提起循环审计通过；19 套口型 UV 检查通过。TypeScript 检查、16 项核心测试、生产构建通过。旧版 262 个角色资源文件（65 包、含 66 组家具）与 0.1.17 逐字节一致。运行时新增可选角色取景配置及镜头平滑过渡，目前仅日富美、泉奈使用。
- 使用 `release/v0.1.18/win-unpacked/BA Desktop Pet.exe` 测试 19 个新增外观的全部已适配动作、动作结束恢复、拖动、透明区域命中检测、断网切换和重启恢复。每套完成连续 23 秒提起采样，原版提起动作保持循环，窗口和画布尺寸稳定。
- 日富美、心奈、泳装美游、胡桃的首次持续提起测试分别记录到 `lostpointercapture`，随后按程序逻辑返回待机；中断触发原因尚未确认，复测通过。首次输入与动画样本分别保存在 `wave7-*-first-hold-trace.json`，没有把这些首次中断记为通过。
- 19 套待机／互动的眼睛、眉毛、嘴型按各自源轨道验证；提起、放下及互动自然结束返回待机均检查多个动画混合帧。角色面板离线加载 84 张缩略图，新增 19 个角色／动作列表和切换时滚动位置保持检查通过。
- 以上 19 套普通动作、持续提起、表情和过渡检查最初在大小修正前完成，快照为 `wave7-before-size-fix.json`。大小修正后的最终程序重新检查日富美、泉奈的全动作、23 秒持续提起、表情、三种过渡、离线与重启恢复，并重新检查 13 组新增家具和 84 项角色面板；没有把修正前的结果冒充最终构建的全量复测。
- 新增 13 组官方家具互动，合计 61 件家具、79 组互动，覆盖 60 个外观包。新增场景通过四方向画面对照并单独设置默认视角；打包程序中逐组检查播放、多个时间点画面、离线加载和收起返回待机。泳装小春含泳装花子同伴。全部 79 个场景完成几何／动画边界审计。
- 未在本版重复物理显示器插拔、不同 DPI 启动、原生系统穿透验证或新的 30 分钟长测。0.1.17 的 30 分钟离线连续运行记录保留在下一节及 `release-0.1.17.json`，不计作本版的新长测。合成输入检查不等于原生 Windows 点击穿透实测。
- 打包资源、文档、编译文件与源码产物一致，最终 ZIP 逐文件比对并校验 CRC。完整验证快照为 `test-results/release-0.1.18.json`。Unity 专用粒子、音效和完整水面折射／水波着色仍未复现。

'''
p=R/'docs/VALIDATION.md';text=p.read_text(encoding='utf8')
assert '## 0.1.18 ' not in text
p.write_text(text.replace('# 验收记录\n\n','# 验收记录\n\n'+section,1),encoding='utf8')
print('Wrote completed runtime validation entry')
