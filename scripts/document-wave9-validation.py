"""Write the shipped validation summary from completed packaged checks."""
import json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads((R/p).read_text(encoding='utf-8-sig'))
runtime=read('test-results/wave9-runtime.json');suite=read('test-results/wave9-runtime-suite.json')
assert runtime['complete'] and runtime['restart'] and len(runtime['results'])==10
assert len(suite)==4 and all(r['exitCode']==0 for r in suite)
for name in ['hold','transitions','expressions']:assert len(read(f'test-results/wave9-{name}.json'))==10
sampled=sum(len(r['played']) for r in runtime['results'])
text=f'''## 0.1.20 初音未来与随机五位角色（2026-10-24）

- 加入初音未来，以及随机抽取的茜、三森、御伽、佐天泪子、萌绘，共 10 套外观、213 个菜单动作；累计 47 位角色、110 个外观／形态包、2,700 个动作。抽样种子及候选名单保存于 `wave9-selection.json`。本批均使用官方原版资源。
- TypeScript 检查、17 项核心测试、生产构建通过。全部 110 包通过资源引用和动作映射校验；新增 10 包逐动作比对原始骨骼通道、插值和采样数据，并检查嘴型事件、眼眉轨道、光环依赖和取景边界。旧版 380 个角色资源文件及 7 个编译文件逐字节保持一致，79 组家具互动未改动。
- 使用 `release/v0.1.20/win-unpacked/BA Desktop Pet.exe` 及随附资源，在离线模拟下加载新增全部 10 包，试播全部 {sampled} 个非待机菜单动作，检查持续渲染、无异常和显式返回待机；重启恢复角色。快速试播不等同于所有动作完整播放至结束，旧版 100 包未重复逐动作运行。
- 新增 10 包分别持续拖动 23 秒，检查帧数继续增长、有限骨骼边界和稳定窗口大小。8 套有原版提起动作并保持循环，初音未来和佐天泪子保持自己的待机。验证互动自然结束后的过渡，以及可用的提起／放下过渡；按原始轨道和事件检查眼眉变化、嘴型及水平翻转。
- 面板离线加载全部 110 张缩略图，逐套检查新增 10 包说明、动作列表、分类、原始名称搜索、收藏及切换后滚动保持。新增角色的待机、互动、提起及部分技能截图人工复核。
- 原始资源限制：初音未来本来没有光环；初音未来、佐天泪子没有独立提起片段。本版不含演唱音频、完整舞台、技能粒子或攻击目标。6 个需要额外场景的片段未开放，详见模型与动作核对说明。御伽源数据中指向不存在的第 11 个渲染器的 4 个事件已精确记录，不猜测替换为其他脸部网格。
- 测试记录：`wave9-runtime.json`、`wave9-panel.json`、`wave9-hold.json`、`wave9-transitions.json`、`wave9-expressions.json`、`wave9-resources.json`、`wave9-pack-source.json`。成品全部资源和说明文件比对、ZIP 逐文件摘要和 CRC 验证见 `release-0.1.20.json`。
- 限制：本版未重新执行 30 分钟长测、物理显示器热插拔或不同 DPI 实机测试。鼠标测试使用合成输入，不能替代原生 Windows 点击穿透实测。
'''
p=R/'docs/VALIDATION.md';old=p.read_text(encoding='utf8');first,rest=old.split('\n',1)
assert '## 0.1.20' not in old
p.write_text(first+'\n\n'+text+rest,encoding='utf8')
for item in read('package.json')['build']['extraFiles']:shutil.copy2(R/item['from'],R/'release/v0.1.20/win-unpacked'/item['to'])
print('Final validation document written and all seven documents copied')
