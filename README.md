# 📦 Project Launcher

**跨平台开源项目启动器** — 一键发现、管理、启动本机所有开源项目。

自动扫描 Git 仓库、Docker 容器和已安装的应用，生成漂亮的本地 Web 面板。  
支持 **macOS** 和 **Windows**。

![Screenshot](./screenshot.png)

## ✨ 功能

- 🔍 **自动扫描** — Git 仓库、Docker 容器、已安装应用，一键发现
- ⭐ **GitHub Stars** — 自动抓取仓库 Star 数
- 🟢 **实时状态** — 检测服务运行/停止，脉冲指示器
- ⚡ **一键打开** — 点击直达本地服务（localhost:xxxx）或网页
- 📊 **系统状态** — 主机名、运行时间、内存、磁盘一目了然
- 🏷️ **分类浏览** — Git仓库 / Docker / 桌面应用 / 已收藏
- 🔄 **实时刷新** — 点击"刷新扫描"重新发现项目
- 🌍 **跨平台** — 同一套代码，macOS 和 Windows 都能跑

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Git（自动扫描 Git 仓库）
- Docker（可选，自动扫描 Docker 容器）

### macOS

```bash
git clone https://github.com/WWEIHAOMUSIC/project-launcher.git
cd project-launcher
python3 server.py
# 浏览器自动打开 http://localhost:9876
```

### Windows

**方式一：双击运行**
1. 克隆或下载项目
2. 双击 `start.bat` 或右键 `start.ps1` → **使用 PowerShell 运行**
3. 浏览器自动打开 http://localhost:9876

**方式二：命令行**
```powershell
cd project-launcher
python server.py
# 浏览器打开 http://localhost:9876
```

> 💡 **首次运行提示**：Windows 可能会弹出防火墙提示，点击"允许访问"即可。

## 📁 项目结构

```
project-launcher/
├── index.html          # 面板前端（纯 HTML/CSS/JS）
├── scan.py             # 扫描脚本（跨平台，自动检测 macOS/Win）
├── server.py           # 轻量本地服务器（跨平台）
├── start.bat           # Windows 快捷启动脚本
├── start.ps1           # Windows PowerShell 启动脚本
├── bookmarks.json      # 收藏项目配置
├── com.project-launcher.plist  # macOS 开机自启配置（仅 macOS）
└── README.md
```

## ⚙️ 配置

### 跳过目录

在 `scan.py` 中修改 `skip_dirs` 列表，添加你不想显示的目录：

```python
skip_dirs = [".qclaw", ".openclaw", ".nvm", ".hermes", "AppData", ...]
```

### GitHub API 限流

Stars 查询使用 GitHub API，未认证每小时限 60 次。设置 Token 可提升至 5000 次：

```bash
# macOS
export GITHUB_TOKEN="ghp_your_token_here"

# Windows PowerShell
$env:GITHUB_TOKEN="ghp_your_token_here"

# 然后运行扫描
python scan.py
```

### 自定义端口

```bash
python server.py --no-open   # 不自动打开浏览器
# 默认端口 9876，可直接修改 server.py 中的 PORT 变量
```

## 🔧 跨平台说明

| 功能 | macOS | Windows |
|------|-------|---------|
| Git 仓库扫描 | ✅ | ✅ |
| Docker 容器 | ✅ | ✅ |
| 应用发现 | Homebrew Cask | 开始菜单应用 |
| 端口检测 | lsof | netstat |
| 系统信息 | vm_stat / sysctl | wmic |
| 开机自启 | LaunchAgent 配置 | 任务计划程序 |

## 🛠️ 技术栈

- **前端**：纯 HTML + CSS + Vanilla JS（零依赖）
- **后端**：Python 3 标准库 `http.server`
- **扫描**：Python 3（Git/Docker/系统 CLI）

## 📄 License

MIT License — 自由使用、修改、分发。

---

⭐ 如果觉得有用，给个 Star 吧！
