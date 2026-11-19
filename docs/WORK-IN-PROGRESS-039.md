# 039 已完成目录交付

最终0.2.18真实离线长测已完成：1801.644秒、33轮组合、30次角色切换，28.89FPS，errors=[]；工作集792.8～1231.5MiB，末两段五分钟均值913.71／961.88MiB，通过增长判据。所有角色／家具／历史复核及新增内容的验证完成。

用户最后要求今后默认不自动生成程序或源码压缩包，已记录AGENTS.md并将npm run pack改为目录构建，pack:zip保留显式选项。本轮不生成0.2.18 ZIP。直接运行release/v0.2.18/win-unpacked/BA Desktop Pet.exe，源码在工作区；只使用finalize-folder039.py进行目录验证和说明同步。程序asar/exe和616个资源保持受测内容不变。最终清单为test-results/release039-folder.json。

双人沙浴的粉发头部、沙堆和帽子已通过Yostar原发布图核对一致，不是额外错误。参考图与元数据已留存。

以下为已完成的历史过程，不再执行旧待办、重复长测或创建ZIP。

用户要求先修复鹤城泳池和复核历史问题，再加入若藻、伊吹；明确不要提前结束让其发继续。无子代理授权。工作区G:/Projects/BA。

038已全部完成：0.2.17已实际30分钟离线长测1801.509秒、44轮、29.355FPS、零错误，末五分钟均值888.797/866.701MiB。145家具725帧+44专项440帧+20边界159帧+16普通脸144帧=1468帧，101张接触表全部实际查看。根因5片鹤城静态泡沫OPAQUE纯白缺原3纹理，修DSFX透明和2999/3000顺序；日奈共用水面、美祢液体/Tint一起修，仅3GLB。82TS26Python过，139独立家具258原材质无剩余同类问题。docs/AUDIT-038和HISTORY-RECHECK-038完整。zip已生成验证：release/BA-Desktop-Pet-0.2.17-win-x64.zip (1202432336bytes,SHA cc343ebb91e150ce710e8a17a889360bcade59e755c5d1ceaa6f13d71eddc8d1)，source.zip3301090bytes。test-results/tsurugi038-before-after.jpg已查看。无需再运行旧安装器或旧打包覆盖。

039新内容已完成适配并构建0.2.18（release/v0.2.18/win-unpacked）。4包wakamo/Wakamo_Original、wakamo_swimsuit/CH0175、ibuki/Ibuki_Original、ibuki_swimsuit/CH0347。fresh学生data与用户wiki快照wave13-selection，4外观JP已实装；wiki尚无Ibuki swim。原始官方r96bundleCRC验证wave13-acquisition，4角色34/30/50/14动作=128新增，154外观3936动作150家具。Waka原版正确戴面具、原MouthRenderer=0,index=-1，无独立口型，profile显式noMouthAtlas验证；Cafe_Wakamo_Original root通过强制绑定自己全部原动作。新3个普通角色有mouth atlas。67,312个通道与原生源逐数值相同。

5新家具Waka f3108_0沙发，swim f4201_0音乐盒，Ibuki f210330_0书桌，swim f211311_0单人、f211311_1双人沙浴。隐藏搭档Iroha swimsuit官方学生10148、CH0346，.assets/furniture-partners/iroha_swimsuit适配，不在角色菜单。沙浴完整时间线55.833s保留原后30s休息。sourceControl FX全部适配无omitted，persistent唯一漏候选是音乐盒FX_...原Object_Idle单独分组，不应在互动叠加，原ActivationTracks已应用。5家具从4角度比较，均选yaw pi/4，defaultcfg按character写入。新5家具最终50帧+四角色9frames各=36，共86帧7张最终接触表全部实际查看，visual039-review.json。初步stage5接触表和20角度大图也已看，不混入最终数量。

四角色最终成品全部128动作已播放（124手动+4idle），离线与重启恢复通过wave13-packaged-runtime.json；faces039-runtime 4角色36帧通过；final039-runtime 5家具50帧通过。hold039初次可见窗口被额外实体pointerdown/up打断Ibuki的捕获（hold039-interference.json），不能记为程序bug或通过；改屏幕外且setFocusable(false)的hold039-test后四套各23秒全通过（hold039.json），尺寸540x523稳定，pickup循环。transitions039.json四套提放/自然结束多帧混合全通过。没有TS运行代码更改，新构建的15个dist运行文件与0.2.17完全一致（wave13-program-identity.json），旧599资源逐文件相同；新17文件，合计616。

type/build/assets82TS26Python全部过，unit039/type039/build039/assets039/python039.logs。static039源审计扩展为144独立家具、265项原材质，zero errors/DSFX/Tint遗漏。resources和曲线验证wave13-resources.json。

构建第一次默认Electron缓存因sandbox EPERM rename失败，已使用本地node_modules/electron/dist和workspace ELECTRON_BUILDER_CACHE重新成功。pack039.log最终成功，别用第一次失败结果。verify-release039锁定version0.2.18/app.asar 9419da4a7278b24dc9ba6dac6196bbe640b7f91b557687f1673ae8b611419855 / exe 786005f9ea6819667debf381ac5d68cf807a9aff97cbf013e6d0182cf19add63 /616资源。release039-soak-input.json为开测前锁定。

## 正在运行真实30分钟长测，不能提前结束

session70567（exec_command/writestdin），test-results/release039-soak.log/jsonl，完后.json。13cases文件soak039-cases.json，覆盖全部5新家具（沙浴各58s完整）和鹤城60、日奈40、美祢70、艾米50、爱理、茜、忧、八云，循环约11分钟。最近日志5min进入鹤城，零错误。不要同时跑GPU测试，CPU审图/文档可用。每次wait<=60s，保持用户更新。

最终打包脚本scripts/package-release039.py已创建，门控新30min、616资源哈希、老599不变、15程序文件相同、124手动动作+4idle、脸/家具/拖动/衔接/原材质/审图/核心测试；成品ZIP每文件SHA+CRC，源码ZIP附两轮证据和新7张接触表。尚未执行，因为长测未完。源/成品路径为release/BA-Desktop-Pet-0.2.18-win-x64.zip与-source.zip。不得先宣称完成。

文档scripts/document039-validation.py已创建，等长测完成后运行summarize-soak039.py→document039-validation.py→package-release039.py。源docs/ROSTER-013、README/ASSETS/COSTUMES/FURNITURE已经新增内容；ROSTER最后验收段目前占位，final writer填真实fps等，VALIDATION补0.2.18。写完文档再打包，打包时刷新extraFiles无需改asar。打包前可更新本检查点为完成，打包中不要修改源文件。

额外沙浴视觉疑问已澄清：通过GameWith转载的Yostar原发布图（.assets/sandbath039-official-release-reference.jpg）实际查看，粉发头部、沙堆、后方帽子与小物均与官方一致。未修改正确原资源。证据复制到test-results并附wave13-reference.json，ROSTER-013已加来源链接，package-release039也包含参考图与元数据。

下一步：继续监听长测，必要时用剩余时间核对只读诊断；结束后读取json确认complete、>=1800、errors[]、FPS和内存判据。运行summarize/document/pack039，等待ZIP完整生成并CRC/哈希通过。确保测试app结束。最终简短中文交付0.2.18免安装ZIP/源码/复核记录，说明泡沫漏材质根因，已加若藻伊吹四外观128动作5家具，给对照图链接。不要让用户继续、不要提前final。技能/CUA未用。
