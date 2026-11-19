# 角色包

每个子目录放置 `character.json` 和自包含的 GLB。GLB 必须包含贴图、骨骼、待机和互动动画，不加载外部网络资源。

描述文件字段：`id`（小写字母/数字/横线）、`name`、`model`（同目录 GLB 文件名）、`source: {url, description}`、`scale`（正数）、`yaw`（弧度）、`animations: {idle, interact}`（GLB 中的实际动画名）。

仅完成资源核验的角色包才应放入此目录。程序没有角色包时显示错误，不使用替身角色。

可选 `actions: [{id, label, clip}]` 声明中文动作二级菜单。`id` 必须唯一；`idle`、`interact` 对应基础动画映射。待机循环，其余动作播放一次后回到待机。

可选 `mouth: {material, defaultTile, columns?, rows?, events}` 声明原版口型图集，行列默认各为 8，也支持小雪的 4×4 图集。`events` 以 GLB 动画名为键，值为按时间排序的 `[{time, tile, flipped?}]`；时间单位为秒，取自原始口型事件。`tile` 的百位为自底向上的行，余数为列（均从 0 开始）。GLB 嘴部基础 UV 应规范化到 `defaultTile`，原材质的负缩放不直接烘焙为跨格坐标。

`SetMouthTile` 转为普通事件，`SetHorizontallyFlippedMouthTile` 带 `flipped: true`，`SetMouthTileToDefault` 使用 `defaultTile`。运行时按活动动画时间平移或在指定格内水平翻转；普通事件清除之前的翻转状态，切换动作时重新采样。没有事件的动作使用默认嘴型，不自行生成口型。
