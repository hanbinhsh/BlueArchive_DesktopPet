"""Install the one-resource phone hotfix and prepare a directory-only release."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];T=R/'test-results';read=lambda p:json.loads(p.read_text('utf8'))
proof=read(T/'ichika042-resource-proof.json');assert proof['complete']
def sha(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
inventory=read(T/'release040-resources.json');target=R/'characters/ichika/f10206_0.glb'
for row in inventory:assert sha(R/'characters'/row['path'])==row['sha256'],row['path']
assert sha(target)==proof['beforeSha256'];shutil.copy2(R/'.assets/phone042/ichika/f10206_0.glb',target)
assert sha(target)==proof['afterSha256']
for name in ['package.json','package-lock.json']:
 p=R/name;v=read(p);v['version']='0.2.20'
 if name=='package-lock.json':v['packages']['']['version']='0.2.20'
 else:v['build']['extraFiles'].append({'from':'docs/FIX-042.md','to':'FIX-042.md'})
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
p=R/'README.md';s=p.read_text('utf8');start=s.index('当前版本：');end=s.index('\n\n',start)
s=s[:start]+'当前版本：**0.2.20**。补齐一花大运动会裁判椅的官方手机聊天、取景、照片保存和闪光效果。角色数量保持169套外观、4,305个动作、165项家具。详情见[本次修复](docs/FIX-042.md)。'+s[end:]
s=s.replace('`release/v0.2.19/win-unpacked/BA Desktop Pet.exe`','`release/v0.2.20/win-unpacked/BA Desktop Pet.exe`')
p.write_text('## 0.2.20 一花裁判椅手机画面\n\n恢复角色骨骼下遗漏的官方屏幕特效，保留原始自拍眼部动作。仅更改一项家具GLB，普通角色模型及其他资源保持0.2.19不变。\n\n'+s,'utf8')
text='''# 0.2.20 一花裁判椅手机画面

修复大运动会裁判椅中手机屏幕缺少内容的问题。画面来自官方JP r96原始资源，包含聊天窗口、相机取景、MomoFriends照片、一花自拍、保存画面和闪光。

原始FX_my_autumnsports_01_chair_03_Phone_Emo_01直接挂在一花bone_Phone下，由角色动画在0.033333335秒启用；此前只处理了家具时间线外部生成的3组特效，漏掉这组角色内部特效。现补齐30个原粒子实例，保留原始贴图、网格、图集帧、延迟、局部对齐、单面剔除与骨骼跟随。共享材质缺项通过原始包中的CAB依赖定向补取，按大小和CRC验证，没有生成替代屏幕图片。

此次只替换ichika/f10206_0.glb。原骨骼、所有已存在几何、384条动作通道、口型与启用曲线保持不变；自拍时的原始睁眼保留。前一轮普通待机的结论仍适用于普通待机，不用于判断家具拍照片段。

详细证据位于validation/ichika042-resource-proof.json、ichika042-embedded-source.json、ichika042-phone-adaptation.json。最终成品验证结果在完成后补入。

默认仅提供可运行文件夹，不生成ZIP；源代码与完整验证记录留在工作区。
'''
(R/'docs/FIX-042.md').write_text(text,'utf8')
print('Installed one furniture GLB; prepared version 0.2.20')
