# Random Songs 随机点歌系统

一个纯命令行（CLI）的随机点歌工具：维护歌单与点歌人，随机抽一首歌、自动打开链接，
并带有可配置的**防重复播放**机制；还能直接从 **QQ 音乐歌单**拉取歌曲建单。

数据全部存放在 `main_data/` 下的 **YAML** 文件里，方便手工查看与修改。

> 本版本是在原「半迁移」代码基础上的一次完整修复：统一了数据格式与路径、重写了防重复逻辑、
> 补齐了初始化与依赖管理，使程序能在**任意 Python 3.8+ 的 Windows 10** 环境下**离线安装依赖并直接运行**；
> 并提供了**命令行静默抽歌**入口，便于与 ClassIsland 等定时工具联动。

---

## 环境要求

- Windows 10（Linux / macOS 亦可，命令换成对应的 python）
- Python 3.8 及以上
- 无需联网即可安装（依赖轮子已随仓库附带在 `wheels/`）

## 目录结构

```text
replace_random_songs_system/
├── run.py                  # 便捷入口（推荐）
├── run.bat                 # 双击启动（Windows）
├── install_offline.bat     # 离线安装依赖
├── requirements.txt        # 运行依赖
├── requirements-dev.txt    # 开发依赖
├── wheels/                 # 离线依赖轮子（PyYAML / requests 全套）
├── run_tests.py            # 一键跑测试
├── scripts/
│   ├── backup_data.py           # 备份 main_data/
│   └── migrate_json_to_yaml.py  # 旧版 JSON 数据迁移
├── src/                    # 源代码
│   ├── main.py                    # 主入口与初始化
│   ├── paths.py                   # 统一路径解析
│   ├── storage.py                 # YAML 读写（原子写入）
│   ├── console_utils.py           # 控制台 UTF-8 兼容
│   ├── config_manager.py          # 全局配置与歌单注册表
│   ├── history_manager.py         # 操作/播放历史
│   ├── song_manager.py            # 歌曲数据与统计
│   ├── requester_manager.py       # 点歌人管理
│   ├── song_operations.py         # 歌曲增删改查菜单
│   ├── playlist_manager.py        # 歌单管理
│   ├── auto_jump_manager.py       # 自动网页跳转
│   ├── duplicate_prevention_manager.py  # 防重复逻辑与菜单
│   └── qq_importer.py             # QQ 音乐歌单拉取与同步
├── tests/                  # 单元测试
├── gui/                    # Windows 桌面端（.NET 8 / WinUI 3，原生）
│   ├── RandomSongs.sln
│   ├── src/RandomSongs.Core/     # 数据与逻辑（读写同一套 main_data）
│   ├── src/RandomSongs.App/      # WinUI 3 界面
│   └── tests/RandomSongs.Core.Tests/
└── main_data/              # 运行时数据（首次运行自动生成，不入库）
```

## 安装

### 方式一：离线安装（推荐，无需外网）

1. 安装 Python 3.8+（勾选 “Add Python to PATH”）。
2. 双击运行仓库里的 **`install_offline.bat`**（或在该目录执行）：

   ```bat
   python -m pip install --no-index --find-links wheels -r requirements.txt
   ```

`wheels/` 目录内已附带 PyYAML（cp38–cp313，win64/win32）与 requests 全套依赖，
因此**在完全无法连接外网的环境里也能装上**。

### 方式二：在线安装

```bat
python -m pip install -r requirements.txt
```

## 运行

程序有两种启动方式。

### 1. 交互菜单

```bat
python run.py --gui
```

或直接双击 **`run.bat`**（它已带上 `--gui`）。

### 2. 静默抽歌（命令行 / 联动用）

不带任何参数（或只带 `--silent`）时，按当前状态随机抽一首、输出结果后立即退出，
**不显示主窗口、不等待输入**：

```bat
python run.py
```

首次运行会自动创建 `main_data/` 目录结构，并写入一个**含 5 首示例歌曲的默认歌单**
（示例点歌人均为虚构名）。之后所有数据都会以 YAML 形式保存在 `main_data/` 下。

## 命令行参数与 ClassIsland 联动

约定：**不带参数 = 静默抽歌**；带非默认参数时按参数执行；用 `--gui` 才进交互菜单。

| 参数 | 说明 |
| --- | --- |
| `--silent` / `-s` | 静默抽歌（默认行为，可不写） |
| `--gui` / `--menu` | 打开交互式主菜单 |
| `-p, --playlist <歌单>` | 指定歌单（ID 或名称），默认当前歌单 |
| `-n, --count <N>` | 抽取数量，默认 1 |
| `--jump` / `--no-jump` | 本次强制开启 / 关闭自动跳转 |
| `--jump-mode search\|custom` | 覆盖跳转模式 |
| `--url <URL>` | 自定义跳转地址（隐含 custom 模式，支持 `{query}`/`{song}`/`{artist}` 占位符） |
| `--jump-delay <秒>` | 覆盖跳转延时 |
| `--prefer-search` / `--no-prefer-search` | 忽略歌曲自带链接、一律走模式 / 有链接时优先开链接（默认） |
| `--no-save` | 不写播放记录、不改防重复状态（预览用） |
| `--reset-before` | 抽歌前先重置防重复记录 |
| `--json` | 以 JSON 输出结果 |
| `--quiet` / `-q` | 仅输出歌曲名 |
| `--list-playlists` | 列出所有歌单后退出 |
| `--qq-sync` | 抽歌前先同步 QQ 歌单（默认不联网） |
| `--version` / `-h` | 版本 / 帮助 |

**退出码**：`0` 成功；`1` 参数或歌单错误；`2` 没有可用歌曲。便于联动工具按结果分支。

### 输出格式

默认（人读）：

```text
夜曲 - 周杰伦（点歌人: 阿澈）
  链接: https://y.qq.com/n/ryqq/songDetail/xxxx
```

`--json`：

```json
{"ok": true, "playlist": "default", "playlist_name": "默认歌单", "count": 1,
 "songs": [{"id": "...", "song_name": "夜曲", "artist": "周杰伦",
            "url": "...", "requested_by": "阿澈"}]}
```

### ClassIsland 示例

在 ClassIsland 里新建一个「运行」动作，命令填仓库自带的便捷批处理即可：

```bat
"完整路径\pick.bat"
```

`pick.bat` 即静默抽歌并把结果输出到标准输出，附加参数会原样透传。
若需要结构化数据，可用：

```bat
python "完整路径\run.py" --silent --no-jump --json
```

想让它直接去 B 站搜这首歌（不依赖歌曲自带链接，避开 QQ 音乐登录态）：

```bat
python "完整路径\run.py" --jump --prefer-search --jump-mode search --jump-delay 0
```

想让它打开一个固定地址（也可是带占位符的搜索地址）：

```bat
python "完整路径\run.py" --jump --url "https://search.bilibili.com/all?keyword={query}"
```

> 说明：静默模式会按**当前配置**决定是否自动跳转。若不想在联动时打开浏览器，加 `--no-jump`；
> 想固定跳某个地址，用 `--url <URL>`。静默模式下跳转相关的提示不会写入标准输出，
> **stdout 只有抽歌结果本身**，可直接被联动工具解析。

## Windows 桌面端（gui/）· 开发中

`gui/` 是原生的 **.NET 8 + WinUI 3** 桌面端，目标是把 Windows 上的主程序从命令行迁到 GUI。
它与命令行版**读写同一套 `main_data` YAML**，两边数据互通。

环境：.NET 8 SDK。免安装自包含构建（无需另装 Windows App SDK 运行时）。

```bat
cd gui
dotnet build RandomSongs.sln          # 也可只 build src\RandomSongs.App
dotnet test tests\RandomSongs.Core.Tests
dotnet run --project src\RandomSongs.App
```

当前已实现（MVP-1）：歌单切换、歌曲列表、随机点歌、防重复、结果卡片、打开链接、按配置自动跳转。
后续：歌曲/点歌人增删改、QQ 歌单同步、设置页、历史、备份恢复等。

> 数据目录默认在 exe 同级的 `main_data`，可用环境变量 `RANDOM_SONGS_DATA` 指向别处（例如与命令行版共用）。
> 详见 [`gui/README.md`](gui/README.md)。

## 使用说明

### 主菜单

```text
1. 随机点歌
2. 重新加载歌曲列表
3. 查看统计信息
4. 点歌人管理
5. 歌曲管理
6. 查看历史记录
7. 设置
8. 退出
```

随机点歌会显示歌曲名、歌手、点歌人与链接；若开启了自动跳转，会在设定延时后打开网页。

### 设置菜单

```text
1. 歌单管理
2. 自动网页跳转设置
3. 防重复功能设置
4. QQ 歌单同步
5. 返回主菜单
```

### 歌单管理

支持：从外部文件导入、从 QQ 音乐歌单导入、创建空白歌单、删除、切换、查看。
外部文件支持 `.yaml / .yml / .json`（含 `songs` 列表）以及 `.txt`（每行 `歌名 - 歌手`）。

## 自动跳转机制

随机点歌后是否打开网页、打开什么，按以下优先级：

1. **歌曲自带链接**（`url`）→ 直接打开；**除非**开启了「优先搜索」；
2. 没有可用链接、或开启了「优先搜索」时，按**跳转模式**：
   - **搜索跳转**：用「歌名 歌手」打开 B 站搜索 `https://search.bilibili.com/all?keyword=...`；
   - **自定义 URL**：打开你填的地址，地址里可用占位符：

     | 占位符 | 展开为 |
     | --- | --- |
     | `{query}` | `歌名 歌手` |
     | `{song}` | `歌名` |
     | `{artist}` | `歌手` |

     例如 `https://search.bilibili.com/all?keyword={query}` 就相当于「自定义模式下的 B 站搜索」。

**为什么需要「优先搜索」**：QQ 音乐歌单导入的歌曲都自带 `y.qq.com` 链接，而 QQ 音乐在很多场景需要登录态。
开启「优先搜索」后，程序会忽略这些链接、直接用 B 站搜索，避免跳到一个打不开的页面。

在「设置 → 自动网页跳转设置」里可以开关自动跳转、切换模式、设置延时、开关「优先搜索」。

## 数据格式（YAML）

### 全局配置 `main_data/global/global_config.yaml`

```yaml
system_version: '2.1'
initialized_at: '2026-09-22 17:11:36'
current_playlist: default
auto_jump:
  enabled: false
  mode: search          # search | custom
  custom_url: ''        # custom 模式地址，支持 {query}/{song}/{artist}
  delay: 3
  prefer_search: false  # true = 忽略歌曲自带链接，一律走模式
qq_sync:
  enabled: true         # QQ 同步总开关
  playlist_id: ''       # QQ 歌单分享链接或 ID
  auto_on_start: true   # 启动时自动同步
playlists:
  default:
    name: 默认歌单
    description: 主歌单（含示例歌曲）
    created_at: 2026/09/22
    song_count: 5
    duplicate_prevention:
      enabled: true
      mode: time_window          # time_window | cycle
      time_window_minutes: 60
      reset_on_all_played: true
      avoid_immediate_repeat: true
      last_reset_time: null
      played_songs: []
```

### 歌曲 `main_data/play_list/<歌单ID>/songs.yaml`

```yaml
songs:
- id: 1cb3b4f0-82ab-4e0e-bf6d-e5a23fb33457   # UUID，唯一标识
  song_name: 夜曲
  artist: 周杰伦
  url: ''
  requested_by: 阿澈
  created_at: '2026-09-22 17:11:36'
  last_modified: '2026-09-22 17:11:36'
```

### 点歌人 `main_data/play_list/<歌单ID>/requesters.yaml`

```yaml
requesters:
- name: 阿澈
  email: ''
  notes: ''
```

### 日志

- 每个歌单：`play_list/<歌单ID>/play_history.log`、`operate_history.log`
- 全局：`global/global_play_history.log`、`global_operate_history.log`

格式为文本一行一条，便于直接用记事本查看：

```text
[2026-09-22 17:12:03] 播放 - 歌曲: 晴天 - 歌手: 周杰伦 - 点歌人: 小满
```

## 防重复播放机制

每首歌以 **UUID** 作为唯一标识，防重复状态按歌单独立维护。

- **两种模式**
  - `time_window`（时间窗口，默认）：窗口时长内播放过的歌不再被抽到。
  - `cycle`（整轮不重复）：一首歌在同一轮里只出现一次，全部播完才重置。
- **无可选时自动重置**（`reset_on_all_played`）：候选为空时清空记录重新开始；关闭则返回“无歌可选”。
- **避免连播同一首**（`avoid_immediate_repeat`）：始终排除“上一首”，不与它紧挨着重复。

相比旧版的改进：

1. 统一用 UUID，杜绝“自增整数 / UUID”两套标识混用；
2. 播放记录会随**歌曲删除、超出窗口、时间戳损坏**自动清理，规模有上界，不再无限膨胀；
3. 遇到一条坏记录只跳过，不会让整个点歌流程崩溃；
4. `cycle` 模式此前实际未生效，现已真正实现。

在「设置 → 防重复功能设置」里可以开关、切模式、设窗口、查看与手动重置播放记录。

## QQ 音乐歌单同步

在「设置 → QQ 歌单同步」中填入 QQ 歌单的**分享链接或纯数字 ID**，即可：

- **立即同步**：把歌单里的歌合并进当前歌单（按 歌名+歌手 去重）；
- **导入为新歌单**：直接建一个新歌单；
- 打开 `auto_on_start` 后，**每次启动自动同步**（只添加新歌，不删改已有数据）。

> 说明：该功能在运行时需要能访问 QQ 音乐的公开接口（`c.y.qq.com`）——这是本项目唯一需要联网的环节。
> 若所处网络无法访问，启动时的自动同步会**给出提示并跳过**，不影响其它功能。
> 导入后的歌曲链接形如 `https://y.qq.com/n/ryqq/songDetail/<songmid>`。

## 常见问题

- **双击 run.bat 一闪而过**：多半是依赖没装好或 Python 不在 PATH。先在命令行运行 `python --version` 确认，
  再执行 `install_offline.bat`。
- **终端里中文/emoji 显示成乱码**：请用 `run.bat` 启动，程序会自动把控制台切到 UTF-8；
  若手动 `python run.py` 启动，可先执行 `chcp 65001`。（`.bat` 文件本身保存为 GBK/ANSI 编码，以匹配 cmd 默认的解析代码页，切勿改成 UTF-8。）
- **提示“当前没有可供点播的歌曲”**：说明歌单为空，或所有歌都在防重复窗口内且关闭了自动重置。
- **QQ 同步失败**：确认网络能访问 QQ 音乐接口；离线环境下这是预期行为，可忽略。

## 测试

```bat
python run_tests.py
```

覆盖初始化、配置合并、歌曲正常化、防重复各模式与边界、歌单文件创建、QQ 歌单解析与去重等。

## 旧数据迁移

若你手上有旧版 JSON（`songs_list.json`）：

```bat
python scripts/migrate_json_to_yaml.py <旧文件路径> <目标歌单名>
```

## 备份

```bat
python scripts/backup_data.py
```

会在 `backups/` 下生成带时间戳的 `main_data_*.zip`。

## 许可证

本项目采用 MPL-2.0 许可证，详见 [LICENSE](LICENSE)。

---

## 写在后面

我是这个项目的开发者。

这个项目是我利用课余时间一点点搭建起来的——从最初简陋的脚本到现在这个还算完整的系统。每次看到有人用它点歌，我都觉得那些调试代码的夜晚特别值得。

对我来说，编程不只是写代码，更是一种表达方式。这个项目就像我的技术日记，记录了我如何把一个简单的想法变成实际可用的东西。它或许不完美，但每一行代码都是我真真实实思考过的痕迹。

感谢你花时间了解这个项目。如果它恰好对你有用，那就是对我最好的鼓励（送花花）！
