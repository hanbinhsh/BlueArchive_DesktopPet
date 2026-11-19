"""Finalize the audit only from the completed, version-matched test reports."""
import json
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'test-results'
def read(name):return json.loads((T/name).read_text('utf8'))
s=read('release038-soak.json');assert s['complete'] and s['version']=='0.2.17' and s['elapsedSeconds']>=1800 and not s['errors']
v=read('visual038-review.json');assert v['contactSheetsReviewed']==101
m=s['memoryMiB'];resources=read('release038-resource-summary.json')
body=f'''## 实际验收（2026-11-17）

82项TypeScript、26项Python测试通过，类型检查、构建和离线资源验证通过。最终免安装程序离线遍历145项家具725帧，另复核44个历史反馈场景440帧、20组边界／旋转场景159帧，以及16套普通角色144帧。合计1,468张真实程序截图、101张接触表均已逐页审阅；[历史反馈矩阵](HISTORY-RECHECK-038.md)区分本轮新增修复和旧问题复测。

持续拖动4角色各23秒，窗口尺寸稳定；提起／放下／自然动作结束均有混合衔接。0.25×／1×／4×相同动画时刻的表情和粒子一致；连续云／水面3轮循环及模拟暂停恢复通过。动作列表滚动、收藏星号居中、XYZ多圈和重置、主题及右键菜单测试通过。没有修改日常配置或开机启动项。

最终成品连续离线运行{s['elapsedSeconds']:.3f}秒、{s['cycles']}轮组合、{s['selections']}次角色切换，平均{s['fps']:.2f} FPS，零捕获错误。预热后进程合计工作集{m['min']:.1f}～{m['max']:.1f} MiB，最后两个五分钟均值{m['previousFiveMinutes']:.2f}／{m['lastFiveMinutes']:.2f} MiB，通过增长判据；GPU进程系统内存{resources['gpuProcessWorkingSetMiB']['min']:.1f}～{resources['gpuProcessWorkingSetMiB']['max']:.1f} MiB。GPU进程工作集并非显存测量；报告同时记录各场景实际几何／纹理数量。

只有3个GLB更改，原基础网格保持一致；599个离线文件与实测成品逐文件SHA256核对。旧版和本版同一动画时刻的对照图为validation/tsurugi038-before-after.jpg。ZIP在打包时检查CRC及逐文件内容。

验收限制：关键时刻采样不能证明全部动作每一帧均无差异，Three.js也不复刻游戏完整光照、后处理或私有随机种子。真实登录启动、真实系统休眠及本轮未发生的显示器物理拔插没有作为本轮实测通过项目；模拟暂停明确标记为模拟。未新增游戏皮肤目录覆盖声明。
'''
p=R/'docs/AUDIT-038.md';text=p.read_text('utf8').split('## 实际验收')[0]
text=text.replace('本轮将重新检查此前指定的家具视角、口型、材质、粒子方向／位置／时间线和核心交互，验证结果完成后写入下文。旧版0.2.16与新版本的结果分开保存，不以旧长测替代本轮测试。','本轮复核此前指定的家具视角、口型、材质、粒子方向／位置／时间线和核心交互；结果如下。旧版0.2.16与新版本的结果分开保存，不以旧长测替代本轮测试。')
p.write_text(text.rstrip()+'\n\n'+body,encoding='utf8')
def prepend(path,header,body):
 p=R/path;text=p.read_text('utf8')
 if text.startswith(header):return
 p.write_text(header+'\n\n'+body+'\n\n'+text,encoding='utf8')
prepend('docs/VALIDATION.md','## 0.2.17 静态泡沫与历史复核（2026-11-17）',f'82项TypeScript、26项Python测试以及类型／构建／资源检查通过。145项家具与历史反馈密集采样共1,468帧、101张接触表已审阅；四角色持续拖动、衔接、倍速与UI复测通过。最终成品真实离线长测{s["elapsedSeconds"]:.3f}秒、{s["cycles"]}轮组合，平均{s["fps"]:.2f} FPS，零捕获错误；末两段五分钟内存均值{m["previousFiveMinutes"]:.2f}／{m["lastFiveMinutes"]:.2f} MiB。详见[AUDIT-038](AUDIT-038.md)和[历史反馈矩阵](HISTORY-RECHECK-038.md)。')
prepend('docs/ASSETS.md','## 0.2.17 静态泡沫与液体（2026-11-17）','恢复鹤城泳池5片静态泡沫的3张原始纹理、扰动和透明度；修正与日奈共用水面的混合顺序、美祢液体及茶水Tint。原始表面审计覆盖139个独立家具模型、258项可对应材质，没有剩余同类DSFX／Tint缺失。仅3个GLB更改，不删网格、不改动画、不以自绘水波替代原素材。详见[AUDIT-038](AUDIT-038.md)。')
(R/'docs/WORK-IN-PROGRESS-038.md').write_text('# 038 复核完成\n\n0.2.17原资源修复、101张接触表审阅、核心交互回归及真实30分钟离线长测已完成。结果与边界见AUDIT-038.md和HISTORY-RECHECK-038.md，原始证据在test-results/*038*。随后按用户追加要求接入若藻、伊吹，保留此版实测目录与记录。\n',encoding='utf8')
print('Finalized 038 audit')
