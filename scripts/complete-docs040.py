"""Append measured final results only after the locked executable's real soak."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1];T=R/'test-results';read=lambda n:json.loads((T/n).read_text('utf8'))
s=read('release040-soak.json');assert s['complete']and s['elapsedSeconds']>=1800 and not s['errors']
assert read('release040-verification.json')==read('release040-soak-input.json')
resources=read('wave14-resources.json');review=read('visual040-review.json');f=read('faces040-runtime.json')
fps=round(s['fps'],2);mem=s['memoryMiB'];channels=sum(r['unchangedAuthoredChannels']for r in resources['added'])
gpu=[m['memoryMiB']for row in s['samples']for m in row['metrics']if m['type']=='GPU']
measure=f"最终0.2.19免安装成品连续离线运行{s['elapsedSeconds']:.3f}秒、{s['cycles']}轮组合、{s['selections']}次角色切换，平均{fps} FPS，零捕获错误。预热后应用进程合计工作集{mem['min']:.1f}～{mem['max']:.1f} MiB，末两个五分钟均值{mem['previousFiveMinutes']:.2f}／{mem['lastFiveMinutes']:.2f} MiB，通过末段增长检查。GPU进程系统内存{min(gpu):.1f}～{max(gpu):.1f} MiB，此数值不是显存测量。循环覆盖新增15项家具的完整时间线、志美子／真白原版，以及鹤城、艾米和美祢的历史场景。"
text=f'''## 成品验收（2026-11-17）

82项TypeScript、29项Python测试及类型、构建、资源检查通过。369项新增普通动作（含15项待机）在成品离线加载播放，正常重启恢复角色。已逐项比对{channels:,}条原始动画通道，时间、数值及插值保持不变。676个离线文件与成品逐项哈希一致，其中原616个资源完全保留0.2.18实测内容。

成品132张表情／提起关键帧、150张家具关键帧，合计282帧、30张接触表逐页审阅；另比较60个方向候选。日向、巴旗袍、御坂美琴、律及真白原版各持续拖动23秒，窗口保持540×523逻辑像素，动作与骨骼尺寸均正常；有提起片段的服装持续循环，真白原版保持自己的待机。提起、放下与自然动作回待机均通过多帧混合验证。

新增15项家具的粒子转换报告无遗漏，静态源材质核对15个模型、27项可对应材质，没有未适配DSFX、Tint不一致或来源读取错误。程序14个运行文件与0.2.18相同，仅renderer.js增加受描述字段限制的原始Matcap材质分支；旧资源没有此字段，不进入新分支。本轮没有将282帧采样宣称为重新审阅全部旧动画。

{measure}

运行目录validation保留抽取、名单、来源、关键帧与验收摘要；完整记录在源码工作区test-results。真实多屏/DPI和登录启动未因本次纯资源增量重测；本次没有改动这些功能。
'''
p=R/'docs/ROSTER-014.md';v=p.read_text('utf8');v=v.replace('最终成品测试与30分钟稳定性结果完成后追加于此。','成品测试结果见下节。')
if '## 成品验收'not in v:v+='\n'+text
p.write_text(v,'utf8')
def prepend(file,heading,body):
 p=R/file;v=p.read_text('utf8')
 if heading not in v:p.write_text(heading+'\n\n'+body+'\n\n'+v,'utf8')
prepend('docs/VALIDATION.md','## 0.2.19 十位新增学生验收（2026-11-17）',f'15套外观、369个普通动作、15项家具；动作离线播放、重启恢复、五套持续拖动与衔接通过。282帧／30张成品接触表全部审阅，原616个资源逐文件不变。{measure} 详见[本版来源与验收](ROSTER-014.md)。')
prepend('docs/RANDOM-ROSTER.md','## 0.2.19 随机追加十位','新增安娜、巴、日向、御坂美琴、桐乃、一花、律、真白、志美子、果穗，共15套外观、369个动作、15项家具。抽取一次后固定名单，不因适配困难改抽。按保存的2026-11-17日服已实装数据计，已加入78/149位学生、剩71位，普拉娜另列NPC；[完整名单与口径](ROSTER-COVERAGE.md)。')
prepend('docs/MODEL-AUDIT.md','## 0.2.19 新增十五套外观','新增模型保留原始骨骼、面部、嘴型与光环。修复日向原版5-bit压缩权重的第三方解码问题；恢复巴完整咖啡厅靠椅，跳过同名精简预制体；补取志美子书本共享贴图；按原D3D代码适配桐乃射击场的Matcap子弹材质。完整验证与限制见[ROSTER-014](ROSTER-014.md)。')
summary=dict(version='0.2.19',actions=4305,outfits=169,furniture=165,newActions=369,newOutfits=15,newFurniture=15,playableInstalled=78,playableTotal=149,playableRemaining=71,sourceChannelsCompared=channels,framesReviewed=282,contactSheetsReviewed=30,oldResourcesUnchanged=616,fps=fps,elapsedSeconds=s['elapsedSeconds'],gpuProcessSystemMemoryMiB=dict(min=min(gpu),max=max(gpu)),memoryMiB=mem)
(T/'release040-resource-summary.json').write_text(json.dumps(summary,indent=2),'utf8');print(json.dumps(summary,indent=2))
