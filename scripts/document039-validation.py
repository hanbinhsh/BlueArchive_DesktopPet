"""Write final validation numbers only after the new executable's completed soak."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results'
def read(n):return json.loads((T/n).read_text('utf8'))
s=read('release039-soak.json');assert s['complete']and s['version']=='0.2.18'and s['elapsedSeconds']>=1800 and not s['errors']
m=s['memoryMiB'];a=read('release039-resource-summary.json')
body=f'''## 成品验收（2026-11-17）

82项TypeScript、26项Python测试及类型／构建／资源检查通过。128个新增动作（含4项待机）在最终免安装成品离线播放，正常重启后角色恢复；角色表情／提起36帧、5项家具50帧共7张接触表全部审阅。对比20个视角候选后选定默认朝向。四套各持续拖动23秒，窗口始终540×523逻辑像素；提起、放下与自然动作回待机均有多帧过渡。初次拖动探针被额外按下／松开事件打断，改在屏幕外、不抢焦点的隔离窗口重测全部四套后通过，未将被打断的记录记为通过。

已逐项比对新增角色67,312条原始动画通道，插值方式、时间与数值不变。静态表面源检查覆盖144个独立家具模型、265项可对应原始材质，没有同类DSFX／Tint遗漏或来源读取错误。616个离线文件与成品逐项哈希一致，其中原599个资源及15个程序运行文件与0.2.17完全相同，因此保留前轮历史问题复核证据；没有用本轮86帧冒充重新审阅所有旧动画。

最终0.2.18成品再次连续离线运行{s['elapsedSeconds']:.3f}秒、{s['cycles']}轮组合、{s['selections']}次角色切换，平均{s['fps']:.2f} FPS，零捕获错误。预热后进程合计工作集{m['min']:.1f}～{m['max']:.1f} MiB，最后两个五分钟均值{m['previousFiveMinutes']:.2f}／{m['lastFiveMinutes']:.2f} MiB，通过增长判据。GPU进程系统内存{a['gpuProcessWorkingSetMiB']['min']:.1f}～{a['gpuProcessWorkingSetMiB']['max']:.1f} MiB，并非显存测量。新沙浴的单／双人完整时间线及鹤城、日奈、美祢、艾米等历史场景均在循环中覆盖。

来源、排除片段、视觉截图及运行数据随源码包validation提供。仍以关键时刻采样与明确来源对应为验收范围，不宣称与游戏完整光照／后处理逐像素一致；原始技能演出舞台、音效等未作为新增内容。
'''
p=R/'docs/ROSTER-013.md';text=p.read_text('utf8').split('## 成品验收')[0].replace('成品实测结果完成后补充于此。','成品实测结果如下。');p.write_text(text.rstrip()+'\n\n'+body,'utf8')
p=R/'docs/VALIDATION.md';head='## 0.2.18 若藻与伊吹成品验收（2026-11-17）'
if not p.read_text('utf8').startswith(head):p.write_text(head+f'\n\n新增4套原版外观、128个动作、5项家具；全部动作离线播放与重启恢复通过，86张成品关键帧、7张接触表逐页审阅，四套持续拖动及衔接通过。最终成品真实离线长测{s["elapsedSeconds"]:.3f}秒、{s["cycles"]}轮组合，平均{s["fps"]:.2f} FPS，零捕获错误；末两段五分钟内存均值{m["previousFiveMinutes"]:.2f}／{m["lastFiveMinutes"]:.2f} MiB。原有599个资源及15个运行文件与0.2.17完全相同，保留前轮1,468帧复核证据。详见[新增角色验收](ROSTER-013.md)及[历史反馈矩阵](HISTORY-RECHECK-038.md)。\n\n'+p.read_text('utf8'),'utf8')
print('Finalized 0.2.18 evidence')
