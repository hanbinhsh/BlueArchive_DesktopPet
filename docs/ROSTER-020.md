# 0.2.29 家具穿模与水波修复 + 随机新增十位学生

修复花江圣诞壁炉兔子／礼盒穿模掉出底部问题、修复惠的浴缸两只橡皮鸭水波缺失与随鸭子倾斜问题（并顺手补齐 4 件同类常驻家具粒子特效），同时随机新增 10 位未安装学生：美咲、明里、绫音、心、泉、纱织、纱绫、静子、琴音、月咏，共 21 套外观、494 个普通动作及 18 项咖啡厅家具互动（含心／琴音单人与双人潜水池、纱织泳装 DJ 表演主舞台、美咲泳装海滩躺椅和小桌子、月咏龟背竹白色花盆与礼服简易更衣室等）。当前合计 281 套外观、6,862 个普通动作、295 项家具；按保存的日服已实装名单已加入 140/149 位学生，仅余 9 位，普拉娜、雪乃与妮可 · 探索另列。

| 外观 | 原始模型 | 普通动作 | 家具 |
| --- | --- | --- | --- |
| 美咲 · 原版 | Misaki_Original | 30 | 1 |
| 食蜂操祈 · 原版 | CH9997 | 38 | 1 |
| 美咲 · 泳装 | CH0268 | 14 | 1 |
| 明里 · 原版 | Akari_Original | 42 | 0 |
| 明里 · 新年 | CH0196 | 8 | 1 |
| 绫音 · 原版 | Ayane_Original | 7 | 1 |
| 绫音 · 泳装 | CH0176 | 15 | 1 |
| 心 · 原版 | CH0368 | 42 | 2 |
| 泉 · 原版 | Izumi_Original | 32 | 0 |
| 泉 · 泳装 | Izumi_Swimsuit | 25 | 0 |
| 泉 · 正月 | CH0197 | 9 | 1 |
| 纱织 · 原版 | Saori_Original | 34 | 1 |
| 纱织 · 泳装 | CH0266 | 35 | 1 |
| 纱织 · 礼服 | CH0259 | 28 | 1 |
| 纱绫 · 原版 | Saya_Original | 7 | 0 |
| 纱绫 · 便服 | Saya_Casual | 8 | 0 |
| 静子 · 原版 | Shizuko_Original | 6 | 1 |
| 静子 · 泳装 | CH0180 | 12 | 1 |
| 琴音 · 原版 | CH0369 | 45 | 2 |
| 月咏 · 原版 | CH0114 | 33 | 1 |
| 月咏 · 礼服 | CH0297 | 24 | 1 |

## 缺陷修复与同类排查

- **花江 · 圣诞 圣诞壁炉（`hanae_christmas/f207308_0`）**：原版动画在装盒与装袋结束阶段会将兔子与三只礼盒下移至地面 `Y < 0` 下方隐藏，在无地面遮挡的桌宠窗口中表现为穿过盒子与圣诞袋底部掉落；现为道具材质与独立克隆礼盒材质补齐 `BA_liquidReceiver` 地面裁切（含描边同步裁切）并钳制负缩放超调，同时补齐炉内常驻火焰粒子 `FX_my_event13_fireplace_FireLoop`。
- **惠 温泉柏木浴缸（`megu/f6301_0`）**：为 `Duck01` 补齐原本常驻在预制体下、未挂入时间线控制轨的水平水波粒子 `FX_my_hotsprings_woodenbathtub_duck_01_Bubble` 并固定发射高度至水面；修正 `src/cafe-particles.ts` 中 `m_RenderAlignment === 1`（World）粒子在跟随父骨骼旋转或桌宠旋转时的姿态计算，使其始终平行于水面；同时为 `Duck02` 静态水波网格烘焙反旋转与水面高度，使两只鸭子下方的水波均严格与水面平行。
- **同类常驻家具粒子与渲染事件排查**：排查并补齐 `kanna/f207313_0` 咖啡热气（`FX_my_event15_table_Smoke_01`）、`pina_guide/f210368_0` 电视光效（`FX_my_event078_videotelevision_TV_Loop_1`）与本批 `akari_newyear/f210334_0` 水桶水花（`FX_my_event065_ricecakemakingset_Water_Loop`）；修正 `tsukuyo`／`tsukuyo_dress` 渲染器事件索引映射；修正 `saori_dress` 在咖啡厅待机与豪华全身镜中隐藏战斗专用副武器（`Saori_Original_Handgun`／`CH0259_HandGrenade_Mesh`）以与 `CH0259_CafeOnly` 一致。
- **随机十位新学生**：种子与候选池见 `test-results/wave20-selection.json`；全部 21 套新外观与 18 项新家具（含补齐 `misaki_swimsuit` 实际互动预制体 `my_event083_beachsunbed`）均通过骨骼通道一致性校验与四向实机截图复核。
- 本版默认仅交付可运行文件夹（`release/v0.2.29/win-unpacked/BA Desktop Pet.exe`），不创建 ZIP 压缩包。
