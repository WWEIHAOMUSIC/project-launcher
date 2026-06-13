# 📦 Project Launcher

**跨平台开源项目启动器** — 一键发现、管理、启动本机所有开源项目。

各系统有独立的扫描脚本，干净无交叉。  
自动扫描 Git 仓库、Docker 容器和已安装的应用，生成漂亮的本地 Web 面板。

| macOS | Windows |
|-------|---------|
| `scan.py` | `scan_windows.py` |
| `server.py` | `server.py`（通用） |
| LaunchAgent 开机自启 | `start.bat` / `start.ps1` |

![Screenshot](./screenshot.png)

## ✨ 功能

- 🔍 **自动扫描** — Git 仓库、Docker 容器、已安装应用
- ⭐ **GitHub Stars** — 自动抓取仓库 Star 数
- 🟢 **实时状态** — 检测服务运行/停止，脉冲指示器
- ⚡ **一键打开** — 点击直达本地服务（localhost:xxxx）或网页
- 📊 **系统状态** — 主机名、运行时间、内存、磁盘
- 🏷️ **分类浏览** — Git仓库 / Docker / 桌面应用 / 已收藏
- 🔄 **实时刷新** — 点击"刷新扫描"重新发现项目

## 🚀 快速开始

### macOS

```bash
git clone https://github.com/WWEIHAOMUSIC/project-launcher.git
cd project-launcher
python3 server.py
# 浏览器自动打开 http://localhost:9876
```

### Windows

```powershell
# 方式一：双击 start.bat
# 方式二：右键 start.ps1 → 使用 PowerShell 运行
# 方式三：命令行
cd project-launcher
python server.py
# 浏览器打开 http://localhost:9876
```

> 💡 Windows 首次运行防火墙弹出时，点击"允许访问"。

## 📁 项目结构

```
project-launcher/
├── index.html              # 面板前端（通用）
├── server.py               # 本地服务器（自动检测平台，调用对应扫描脚本）
├── scan.py                 # macOS 扫描脚本
├── scan_windows.py         # Windows 扫描脚本
├── start.bat               # Windows 快捷启动
├── start.ps1               # Windows PowerShell 启动
├── com.project-launcher.plist  # macOS 开机自启（可选）
├── bookmarks.json          # 收藏项目配置（可选）
└── README.md
```

## ⚙️ 配置

### GitHub API 限流

未认证每小时 60 次查询。设置 Token 提升至 5000 次：

```bash
# macOS
export GITHUB_TOKEN="ghp_your_token_here"

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_your_token_here"
```

### 自定义端口

```bash
python server.py --no-open   # 不自动打开浏览器
# 修改 server.py 中的 PORT 变量可换端口
```

## 🔧 跨平台功能矩阵

| 功能 | macOS (`scan.py`) | Windows (`scan_windows.py`) |
|------|-------------------|----------------------------|
| Git 仓库扫描 | ✅ `~/` `~/Documents/` | ✅ `~/` `~/Documents/` `~/Desktop/` |
| Docker 容器 | ✅ `lsof` 端口检测 | ✅ `netstat` 端口检测 |
| 应用发现 | Homebrew Cask `/Applications/` | 开始菜单 `.lnk`/`.url` |
| 系统主机名 | `scutil --get ComputerName` | `%COMPUTERNAME%` |
| 系统内存 | `sysctl` + `vm_stat` | `wmic os` |
| 系统磁盘 | `df -h` | `wmic logicaldisk` |
| 运行时间 | `uptime` | `wmic os get LastBootUpTime` |

## 🛠️ 技术栈

- **前端**：纯 HTML + CSS + Vanilla JS（零依赖）
- **后端**：Python 3 标准库 `http.server`
- **扫描**：Python 3（Git/Docker/系统 CLI）

## 📄 License

MIT License — 自由使用、修改、分发。

---

⭐ 如果觉得有用，给个 Star 吧！
