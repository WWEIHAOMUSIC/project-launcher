# 📦 Project Launcher

**macOS 开源项目启动器** — 一键发现、管理、启动本机所有开源项目。

自动扫描 Git 仓库、Docker 容器、Homebrew 应用和收藏项目，生成漂亮的本地 Web 面板。

![Screenshot](./screenshot.png)

## ✨ 功能

- 🔍 **自动扫描** — Git 仓库、Docker 容器、Homebrew Cask，一键发现
- ⭐ **GitHub Stars** — 自动抓取仓库 Star 数
- 🟢 **实时状态** — 检测服务运行/停止，脉冲指示器
- ⚡ **一键打开** — 点击直达本地服务（localhost:xxxx）或网页
- 📊 **系统状态** — 主机名、运行时间、内存、磁盘一目了然
- 🏷️ **分类浏览** — Git仓库 / Docker / 桌面应用 / 已收藏
- 🔄 **实时刷新** — 点击"刷新扫描"重新发现项目
- 🚀 **开机自启** — macOS LaunchAgent 配置，登录即用

## 🚀 快速开始

### 1. 克隆

```bash
git clone https://github.com/YOUR_USERNAME/project-launcher.git
cd project-launcher
```

### 2. 配置收藏项目（可选）

编辑 `bookmarks.json`，添加你收藏的网页项目：

```json
[
  {
    "name": "电子书下载宝库",
    "icon": "📚",
    "status": "web",
    "desc": "12.7k Stars · 电子书下载",
    "stack": "Web",
    "github": "https://github.com/jbiaojerry/ebook-treasure-chest",
    "webUrl": "https://jbiaojerry.github.io/ebook-treasure-chest/",
    "stars": "12,740"
  }
]
```

### 3. 启动

```bash
# 方式一：直接打开（需先扫描生成数据）
python3 scan.py > projects.json
open index.html

# 方式二：启动本地服务器（推荐，支持实时刷新）
python3 server.py
# 打开 http://localhost:9876
```

### 4. 开机自启（可选）

```bash
# 复制 LaunchAgent 配置
cp com.project-launcher.plist ~/Library/LaunchAgents/
# 修改 plist 中的路径为你实际的项目路径
launchctl load ~/Library/LaunchAgents/com.project-launcher.plist
```

## 📁 项目结构

```
project-launcher/
├── index.html          # 面板前端（纯 HTML/CSS/JS）
├── scan.py             # 扫描脚本（Python 3）
├── server.py           # 轻量本地服务器
├── bookmarks.json      # 收藏项目配置
├── com.project-launcher.plist  # macOS 开机自启配置
└── README.md
```

## 🔧 系统要求

- macOS 12+
- Python 3.9+
- Git
- Homebrew（可选，用于扫描 Cask 应用）
- Docker（可选，用于扫描容器）

## ⚙️ 配置

### 跳过目录

在 `scan.py` 中修改 `SKIP_PREFIXES` 列表，添加你不想显示的目录前缀：

```python
SKIP_PREFIXES = [
    "/.qclaw/workspace", "/.openclaw/workspace",
    "/.nvm", "/.hermes", "/.cache",
]
```

### GitHub API 限流

Stars 查询使用 GitHub API，未认证每小时限 60 次。设置 Token 可提升至 5000 次：

```bash
export GITHUB_TOKEN="ghp_your_token_here"
python3 scan.py
```

### 自定义端口

```bash
# 默认端口 9876，可修改 server.py 中的 PORT 变量
python3 server.py  # → http://localhost:9876
```

## 🛠️ 技术栈

- **前端**：纯 HTML + CSS + Vanilla JS（零依赖）
- **后端**：Python 3 标准库 `http.server`
- **扫描**：Python 3（Git/Docker/Homebrew CLI）

## 📄 License

MIT License — 自由使用、修改、分发。

---

⭐ 如果觉得有用，给个 Star 吧！
