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
│   │   └── Services/              # Config / Song / Playlist / Prevention / History / AutoJump / QqPlaylist / Import / Backup / AppInitializer
│   └── RandomSongs.App/           # WinUI 3 界面
│       ├── App.xaml(.cs)
│       ├── MainWindow.xaml(.cs)   # NavigationView 导航
│       └── Pages/                 # PickPage / StatsPage / PlaylistsPage / SongsPage / RequestersPage / SettingsPage
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

## 当前进度（MVP-5）

GUI 已追上命令行版的功能，并新增了「从文件夹批量导入」与「本地播放模式」。
界面为 NavigationView + 六个页面。

已实现：

- **随机点歌**：歌单切换、当前歌单歌曲列表、随机点歌、防重复、结果卡片、打开链接、
  按配置自动跳转；启用本地播放时直接播放本地文件
- **统计信息**：总统计（歌曲数 / 累计播放 / 点歌人分布）、搜索（歌名 / 歌手 / 点歌人 / UUID）、
  历史记录（本歌单 / 全局 × 播放 / 操作）
- **歌单管理**：切换、新建、重命名、删除（含数据目录）、
  从文件导入（yaml / json / txt）、**从文件夹批量导入（自动识别歌名 / 歌手）**、从 QQ 歌单导入、
  备份单个 / 备份全部（zip 到数据目录同级的 `backups/`）
- **歌曲管理**：添加 / 编辑 / 删除歌曲（含本地文件路径）
- **点歌人**：添加 / 重命名（同步更新歌曲引用）/ 删除
- **设置**：防重复、自动跳转、**本地播放模式**、QQ 同步、数据目录

## 后续

- 从备份恢复、增量备份
- 批量操作 / 批量导入（CSV / Excel）
- 从模板新建、从已有歌曲建单
- 旧版 JSON 数据迁移（GUI 内）
- 用户权限管理、模板管理、主题
- NuGet 离线包 + 镜像配置（照顾无外网环境）

## 互通注意

### 文件名解析（从文件夹导入）
支持 <code>歌手 - 歌名</code>、<code>歌名 - 歌手</code>、<code>歌手《歌名》</code>、<code>[歌手] 歌名</code>、
<code>歌名 (歌手)</code> 以及带音轨号前缀（<code>01. …</code>）等常见形式；
若某一侧命中「已知歌手」（来自现有歌单的歌手名），会自动校正被调换的顺序。
导入前会显示解析预览，并可切换「歌手 - 歌名 / 歌名 - 歌手」顺序重新扫描。

### 本地文件与本地播放
歌曲新增可选字段 `local_path`（本机音频文件路径）。启用「本地播放模式」后，
抽到带本地文件（且文件存在）的歌会直接用系统默认播放器播放；否则按自动跳转处理。
Python 版同样识别该字段（原样保留）并支持同样的本地播放。

### 时间戳
Python（PyYAML）按 YAML 1.1 解析，会把 `2026-09-22 21:27:33` 这种**短横线**时间串读成 `datetime`，
而不是字符串，进而导致 `play_time` 解析失败。因此 .NET 侧统一用**斜杠格式** `yyyy/MM/dd HH:mm:ss`
写时间（斜杠形式不是 YAML 时间戳，双方都读成字符串）；Python 侧的解析同时接受两种格式。
`CompatibilityTests` 会校验能读取 Python 写出的 YAML。
