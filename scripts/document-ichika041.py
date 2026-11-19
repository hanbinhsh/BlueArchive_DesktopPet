"""Record the authored closed-eye idle and verified open-eye interaction."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib
R=Path(__file__).resolve().parents[1];T=R/'test-results'
read=lambda p:json.loads(p.read_text('utf8'))
source=read(T/'ichika041-source.json');runtime=read(T/'ichika041-runtime.json')
assert source['complete']and source['matchedEyeAndBrowChannels']==2712
assert runtime['complete']and not runtime['errors']and len(runtime['results'])==2
for row in runtime['results']:
 assert all(len(a['frames'])==12 for a in row['actions'][:3])
 assert row['actions'][3]['changedEyeBones']and row['actions'][3]['samples'][-1]['action']=='idle'
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
verification=read(T/'release040-verification.json');base=R/'release/v0.2.19/win-unpacked'
assert sha(base/'resources/app.asar')==verification['appAsarSha256']and sha(base/'BA Desktop Pet.exe')==verification['executableSha256']
resources=read(T/'release040-resources.json')
for item in resources:
 if Path(item['path']).parts[0]in ['ichika','ichika_swimsuit']:
  assert sha(base/'resources/characters'/item['path'])==sha(R/'characters'/item['path'])==item['sha256']
canvas=Image.new('RGB',(1120,440),(31,38,47));draw=ImageDraw.Draw(canvas)
cases=[('ichika','idle',0,'Original: idle'),('ichika','interact',4,'Original: interaction 2.33s'),('ichika_swimsuit','idle',0,'Swimsuit: idle'),('ichika_swimsuit','interact',4,'Swimsuit: interaction 3.11s')]
for i,(key,action,frame,label)in enumerate(cases):
 im=Image.open(T/f'ichika041-{key}-{action}-{frame}.png').convert('RGBA');im=im.crop(im.getbbox());im.thumbnail((274,405));canvas.paste(im,(i*280+(280-im.width)//2,28),im);draw.text((i*280+5,7),label,fill='white')
canvas.save(T/'ichika041-idle-vs-interaction.jpg',quality=95)
report=dict(complete=True,version='0.2.19',matchedEyeAndBrowChannels=2712,framesReviewed=72,contactSheetsReviewed=6,findings=['Both original Cafe_Idle clips retain a closed-eye smiling pose throughout the sampled full cycle.','Both Cafe_Reaction and Formation_Pickup contain rendered open-eye poses.','Real-time interactions move eye bones and return to idle with eye following enabled.','Existing character assets and executable hashes unchanged.'],productChangeRequired=False)
(T/'ichika041-review.json').write_text(json.dumps(report,indent=2),'utf8')
text='''# 一花眼部核对（0.2.19，2026-11-17）

结论：一花原版与泳装的原始咖啡厅待机均保持闭眼微笑。当前版本的互动和提起片段均能睁眼，未发现眼部动画漏挂或显示层持续覆盖。

核对了两套外观全部53个可选普通动作的2,712条眼部／眉毛通道；节点、路径、插值、时间和值与原始JP r96导出一致，Unity事件与原始属性曲线元数据一致。CH0071_Cafe_Idle约2秒，CH0292_Cafe_Idle约4秒；每段待机、互动和提起各取12个时刻，共72帧／6张接触表，均已逐页查看。

在实际0.2.19免安装exe内完整播放互动，并启用眼睛追随鼠标，两套均正常变化、结束后回到各自待机。原版互动0.58、1.75、2.33秒等采样可见睁眼，泳装互动0.78～3.89秒等采样可见睁眼，后半段还包含单眼眨眼。提起片段同样存在短暂睁眼。

本次没有改写原始待机、模型或程序。核对前后exe、app.asar及两套角色资源的SHA256保持已验收0.2.19的值，无需重新生成程序或压缩包。

来源与原始通道证明：test-results/ichika041-source.json；成品实测：ichika041-runtime.json；逐帧曲线摘要：ichika041-eye-curves.json；审阅记录：ichika041-review.json。可见对照如下，每套分别为待机与互动睁眼。

![两套外观的待机与互动对照](../test-results/ichika041-idle-vs-interaction.jpg)
'''
(R/'docs/CHECK-ICHIKA-041.md').write_text(text,'utf8')
print('Confirmed authored closed-eye idle; open-eye interactions work; existing product unchanged')
