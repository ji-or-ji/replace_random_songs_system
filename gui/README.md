# RandomSongs · Windows 桌面端（.NET 8 / WinUI 3）

原生 Windows 桌面端，目标是逐步取代命令行作为 Windows 上的主程序。
它与 Python 版**读写同一套 `main_data` YAML**，两边数据直接互通：可以先用命令行版准备歌单，
再用 GUI 点歌，反之亦然。

## 环境

- .NET SDK 8（本项目用 8.0.425 验证）
- 无需另装 Windows App SDK 运行时：应用按**免安装自包含**方式构建（`WindowsPackageType=None` + `WindowsAppSDKSelfContained`）

## 结构

```text
gui/
├── RandomSongs.sln
├── src/
│   ├── RandomSongs.Core/          # 数据与逻辑（不依赖 UI）：模型 / YAML 存储 / 服务
│   │   ├── Models.cs              # 与 Python 版字段一一对应（YamlMember 显式指定）
│   │   ├── AppPaths.cs            # 统一路径解析
│   │   ├── YamlStore.cs           # 原子读写 YAML
│   │   └── Services/              # Config / Song / Playlist / Prevention / History / AutoJump / AppInitializer
│   └── RandomSongs.App/           # WinUI 3 界面
│       ├── App.xaml(.cs)
│       └── MainWindow.xaml(.cs)
└── tests/
    └── RandomSongs.Core.Tests/    # Core 单元测试（xunit）
```

## 构建与运行

```bat
cd gui
dotnet build RandomSongs.sln
dotnet test tests\RandomSongs.Core.Tests
dotnet run --project src\RandomSongs.App
```

构建产物（免安装 exe）：

```text
src\RandomSongs.App\bin\x64\Debug\net8.0-windows10.0.19041.0\win-x64\RandomSongs.App.exe
```

## 数据目录

决定顺序：

1. 环境变量 `RANDOM_SONGS_DATA`
2. 可执行文件同级的 `main_data`（可写时）
3. `%LOCALAPPDATA%\RandomSongs\main_data`

要与命令行版/ClassIsland 共用数据，把 `RANDOM_SONGS_DATA` 指向项目根目录下的 `main_data` 即可。

## 当前进度（MVP-1）

已实现：

- 歌单列表与切换（下拉框）
- 当前歌单的歌曲列表
- 随机点歌（复用与 Python 一致的防重复逻辑：时间窗口 / 整轮不重复、避免连播同一首）
- 结果卡片（歌名 / 歌手 / 点歌人 / 链接）
- 打开链接；按 `auto_jump` 配置自动跳转（含 `prefer_search` 与 `{query}` 占位符）

## 后续（MVP-2+）

- 歌曲、点歌人增删改
- QQ 音乐歌单拉取与自动同步
- 设置页（防重复 / 自动跳转 / QQ 同步）
- 历史记录查看
- 歌单备份与恢复、导入导出
- 与 CUI 规划一致的更完整菜单结构

## 互通注意

Python（PyYAML）按 YAML 1.1 解析，会把 `2026-09-22 21:27:33` 这种**短横线**时间串读成 `datetime`，
而不是字符串，进而导致 `play_time` 解析失败。因此 .NET 侧统一用**斜杠格式** `yyyy/MM/dd HH:mm:ss`
写时间（斜杠形式不是 YAML 时间戳，双方都读成字符串）；Python 侧的解析同时接受两种格式。
`CompatibilityTests` 会校验能读取 Python 写出的 YAML。
