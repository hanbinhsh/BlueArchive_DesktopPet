# 构建与可运行目录

目标平台：Windows x64。运行免安装包无需 Node.js；只有开发构建需要 Node.js、npm 以及 Windows 自带的 .NET Framework C# 编译器（用于很小的滚轮转发辅助程序）。

默认交付可直接运行的文件夹，源码保留在本工作区；只有用户明确要求时才生成程序或源码 ZIP。若另建源码目录，可把同版本成品目录的 `resources/characters` 复制到源码根目录，最终应存在 `characters/<角色ID>/character.json` 和对应 GLB。

在源码根目录运行：

```powershell
npm ci
npm run typecheck
npm test
npm run build
npm start
```

开发运行使用 `.dev-profile`，不会读取或覆盖正式使用配置，也不能更改登录启动项。自动化脚本使用 `BA_TEST_DATA` 指定独立配置目录。

生成 Windows x64 可运行文件夹（不创建压缩包）：

```powershell
npm run pack
```

输出目录包含 `BA Desktop Pet.exe` 和完整运行资源，保持目录内容完整即可运行。仅在明确需要压缩包时执行 `npm run pack:zip`。

`package-lock.json` 固定依赖版本。首次安装依赖或打包可能需要下载 Electron；成品运行只读取本地资源。打包时必须保留 `resources/native/wheel-forwarder.exe`、完整 `resources/characters` 和 Electron 运行库。

## 目录

- `src/`：主进程、受限 preload、设置界面、动画与组合播放。
- `native/WindowWheel.cs`：只转发桌宠窗口收到的滚轮消息。
- `tests/`：配置、随机规则、倍速、道具及启动项核心测试。
- `scripts/`：构建、资源处理与运行验证；历史资源导出脚本按各自说明使用。
- `docs/`：操作、资源来源、历史修复及验收说明。
- `validation/`：本版本主要验证记录；原始工作目录记录位于 `test-results/`。

完整项目与已准备的资源仍保留在工作目录 `G:/Projects/BA`。
