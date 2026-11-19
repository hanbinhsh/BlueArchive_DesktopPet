# 0.2.22 已完成交付验证

当前用户三项任务：千明常服眼睛重叠、亚津子喷泉按参考图调整角度、再加6位角色。继续自主做到完成，用户不希望反复说继续。AGENTS.md只交付运行文件夹/exe，不ZIP，不子代理。

随机固定6位时雨、朱莉、丽、伊吕波、好美、海香；共10外观（roster-wave16.json），来源快照2026-11-17。已安装并建成release/v0.2.22/win-unpacked/BA Desktop Pet.exe，当前196套/4935动作/189家具，94/149学生、剩55，NPC普拉娜另列=95UI组。新增243普通动作、10家具、40资源文件。旧741中只有千明model.glb/f210356_0.glb/thumbnail.png与atsuko_swimsuit/character.json四项修复，其余737字节一致。成品781资源。版本0.2.22已写package+lock及README/docs/ROSTER-016、ROSTER-COVERAGE等。

修复千明：CH0238原事件7/8应Face01/Face02，当前prefab位于6/7，旧代码误指Face02/Halo。scripts/renderer_event_layout.py中央映射已用于prepare-roster/expand-actions/prepare-furniture主角与搭档。只改显示映射，原15792普通+402家具通道/网格/材质/骨骼不变。修复隔离.assets/repair044/chiaki，修复前源报告chiaki044-face-source.json，after证明chiaki044-repair.json，普通及公告板成品画面已实看，眼睛正常。喷泉仅yaw从π/4改π/2，人物位于花丛左边且脸/相机可见，参考图角度。已写scripts/furniture-character-view-yaw.json与现有角色manifest，个人旋转不重置。

新增阶段 .assets/wave16-final。普通10套已定向CRC校验、全Avatar导出、真实channel guard、嘴图/halo处理，扩展265候选经121时刻取景，最终243（场景依赖排除另记）。112697原动画通道值/时间/插值逐项相同（wave16-resources.json），20模型534030加权顶点检查通过(wave16-skin-integrity.json)。10家具全ready，外部25根FX、角色/常驻5额外根补全，全部omitted0/source errors0。Iroha泳装双人沙浴搭档是已加入的ibuki_swimsuit学生20060，不是皋月；不要错误加partner。merge-furniture-wave16保留本批组的partner profile，export-furniture包含ibuki_swimsuit；旧搭档UI资源未修改。

新适配修正：resolve-furniture.pointer用resolve_cached补齐已缓存的樱花椅meshCAB d7...；static_fx_meshes支持没有PS模板、只有原静态网格的温泉水面中性单实例；温泉时雨原脸部Sweat随机rate(.35,.85)已用本地Unity2022.3探针验证，particle_emission.py支持固定seed60Hz rate随机采样+240Hz积分，未宣称原生私有RNG逐位相同。Unity探针源码.assets/unity036/Assets/Editor/EmissionProbe044.cs，数据unity044-emission.csv/证明JSON/log。纯转换代码改动，程序15运行文件全部保持0.2.21（release044-program-identity.json）；无需重新npm build。Python32项、TS83、typecheck/资源检查已通过。温泉时雨Prop/Halo原布局正确，不要误套脸映射。

审计里sandbath pos是原生Emission=false、Renderer=false、无子节点空叶，audit-persistent16已加disabledLeafExclusions，原CAB/ID记录，不能伪造粒子。wave16-persistent-audit unexplained0、embedded-final-audit missing0、static044无遗漏。原初审文件wave16-embedded-initial-audit与persistent-initial-audit保留；导出补漏export-embedded-wave16.py只读初审。重建FX必须先外部prepare（APPEND=0），再embedded APPEND一次，最后apply-activation（本批0项）。不要重复叠加。远程deps头扫描首轮missing d7是已缓存mesh，不是未解决；resolve_cached已实际取回，后续FX3贴图+嵌入2贴图均CRC校验source.errors0。

视觉已真正查看：10普通缩略图1接触表（Juri改后已重新查看）、40家具四向3表、喷泉8角度1表、Rei/沙浴0和5秒16帧2表、成品12家具（10新+千明/喷泉）120帧12表、11套面部（10新+千明）93帧11表，共287独立最终帧/30表。final044-*、faces044-*、visual044-review.json。补查发现打工朱莉同类脸错位：原6/7切Face/Face01，旧代码指Face01/Halo，已中央映射/阶段+安装+成品修复，只显示改动，11758普通/447家具通道不变。juri044-face-repair.json/newfaces044-source-layout.json，Juri缩略图、9脸帧、家具10帧重拍并覆盖正确，faces044-runtime.json已合入juri044-face-final结果。不要拿最初白色叠眼的旧帧作最终。

视角在wave16-view-selection.json与全局map保存。后续补查把Rei发球机和Iroha泳装单人/双人沙浴各额外+π/2，保留正面；改后JSON已同步stage/characters/成品。120帧新角度已重拍，额外报告final044-redo-runtime.json（4场景包括Juri）。Rei接触表看上去贴近格边，但实际原PNG bbox164..592 in678px，完整人物未裁切，已看原PNG确认。Umika面具架角色本来面向陈列架，默认保留展示面具正面，类似原Maki画板自然背向。

最终短测已全部通过：wave16-runtime.json complete/restart true，11外观290动作；hold044.json、transitions044.json各3外观，持续拖动与过渡正常；newfx044-loops.json三个完整场景分别0.5×/2×循环均完成且errors为空。资源锁、15程序文件同前版的证明均已确认，无需重建。

最终真实稳定性验证通过：release044-soak.json complete true，1810.409秒，41轮组合／34次角色切换，28.6794FPS，errors[]。预热后工作集977.86～1316.08MiB，倒数第二个5分钟均值1152.37MiB，最后5分钟1091.49MiB。GPU进程工作集与逐场景Three.js几何／纹理计数见release044-resource-summary.json，不将进程系统内存称为显存。

scripts/finalize-folder044.py已运行成功（exit0）。ROSTER-016、VALIDATION与成品说明已更新；39项验证JSON、30接触表与Unity探针CSV已放入成品validation。release044-folder.json记录993个交付文件、4262480063字节（3.97GiB）及SHA256。最终目录无ZIP，本版未生成压缩包。源代码继续位于本工作区。

交付路径：G:/Projects/BA/release/v0.2.22/win-unpacked/BA Desktop Pet.exe。用户三项任务均完成；同类检查额外修复打工朱莉脸部映射。新增时雨、朱莉、丽、伊吕波、好美、海香，共10套外观/243动作/10家具；当前94/149位学生、196外观/4935动作/189家具，剩余55位，统计依据2026-11-17保存名单。个人旋转不强制重置，喷泉新默认可点“恢复角度”查看；退出旧版再运行新程序。无需进一步重建或重复测试。
