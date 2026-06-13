#!/usr/bin/env python3
"""
Project Launcher Scanner — Windows.

Scans: Git repos, Docker containers, installed apps, and user bookmarks.
Outputs JSON for the web panel.

Usage:
  python scan_windows.py              # Scan and output JSON
  python scan_windows.py > projects.json  # Save to file
"""

import os, json, subprocess, glob, re, time, platform, sys

HOME = os.path.expanduser("~")
PROJECTS = []

# Directories to skip
SKIP_DIRS = ["AppData", "Application Support", ".nvm", ".cache", "node_modules"]

def run(cmd, shell=True):
    try:
        r = subprocess.run(cmd, shell=shell, text=True,
                           capture_output=True, timeout=15)
        return r.stdout.strip()
    except:
        return ""

def add(name, icon, status, desc, stack="", path="", github="", port="",
        running=False, webUrl="", category="local", stars="", mtime=""):
    PROJECTS.append({
        "name": name, "icon": icon, "status": status,
        "desc": desc, "stack": stack, "path": path,
        "github": github, "port": port, "running": running,
        "webUrl": webUrl, "category": category,
        "stars": stars, "mtime": mtime
    })

def check_port(port):
    out = run(f'netstat -ano | findstr ":{port}"')
    return bool(out.strip())

def get_hostname():
    return os.environ.get("COMPUTERNAME", "Windows PC")

def get_disk():
    out = run("wmic logicaldisk where DriveType=3 get DeviceID,Size,FreeSpace")
    for line in out.split('\n')[1:]:
        parts = line.strip().split()
        if len(parts) >= 3:
            drive, free_str, total_str = parts[0], parts[1], parts[2]
            try:
                total_gb = int(total_str) / (1024**3)
                free_gb = int(free_str) / (1024**3)
                percent = f"{(1 - int(free_str)/int(total_str))*100:.0f}%"
                return {"total": f"{total_gb:.0f}G", "used": f"{total_gb - free_gb:.0f}G",
                        "free": f"{free_gb:.0f}G", "percent": percent}
            except:
                continue
    return {}

def get_memory():
    out = run("wmic os get TotalVisibleMemorySize,FreePhysicalMemory")
    for line in out.split('\n')[1:]:
        parts = line.strip().split()
        if len(parts) >= 2:
            try:
                total_kb, free_kb = int(parts[0]), int(parts[1])
                total_gb = total_kb / (1024 * 1024)
                free_gb = free_kb / (1024 * 1024)
                return {"total": f"{total_gb:.0f}G", "used": f"{total_gb - free_gb:.1f}G",
                        "free": f"{free_gb:.1f}G", "percent": f"{(1 - free_kb/total_kb)*100:.0f}"}
            except:
                continue
    return {}

def get_uptime():
    out = run("wmic os get LastBootUpTime")
    for line in out.split('\n')[1:]:
        line = line.strip()
        if line and len(line) >= 14:
            try:
                boot = time.strptime(line[:14], "%Y%m%d%H%M%S")
                boot_dt = time.mktime(boot)
                delta = time.time() - boot_dt
                days = int(delta // 86400)
                hours = int((delta % 86400) // 3600)
                mins = int((delta % 3600) // 60)
                return f"{days}d {hours}h {mins}m"
            except:
                pass
    return ""

def get_readme_desc(repo_path):
    for name in ("README.md", "readme.md", "Readme.md"):
        readme = os.path.join(repo_path, name)
        if os.path.isfile(readme):
            try:
                with open(readme, 'r', errors='ignore') as f:
                    for _ in range(50):
                        line = f.readline().strip()
                        if line and not line.startswith(('#','!','>','*','-','<','|','[','{','```','---','<!--')):
                            return line[:150]
            except:
                pass
    return ""

def get_github_stars(github_url):
    if not github_url:
        return ""
    gh_api = github_url.replace("https://github.com/", "https://api.github.com/repos/")
    token = os.environ.get("GITHUB_TOKEN", "")
    cmd = f'curl -s -H "Accept: application/vnd.github.v3+json"'
    if token:
        cmd += f' -H "Authorization: token {token}"'
    cmd += f' "{gh_api}"'
    result = run(cmd)
    try:
        info = json.loads(result)
        return str(info.get("stargazers_count", ""))
    except:
        return ""

# ==========================================
# 1. Scan Git repos
# ==========================================
scan_dirs = [
    HOME,
    os.path.join(HOME, "Documents"),
    os.path.join(HOME, "Desktop"),
    os.path.join(HOME, "source"),
    os.path.join(HOME, "Projects"),
    os.path.join(HOME, "code"),
]

scanned = set()
for root in scan_dirs:
    if not os.path.isdir(root):
        continue
    try:
        for item in os.listdir(root):
            gitdir = os.path.join(root, item, ".git")
            if os.path.isdir(gitdir):
                repo = os.path.dirname(gitdir)
                parts = repo.replace("\\", "/").split("/")
                if any(s in parts for s in SKIP_DIRS):
                    continue
                if repo in scanned:
                    continue
                scanned.add(repo)

                name = os.path.basename(repo)
                remote = run(f'git -C "{repo}" remote get-url origin 2>/dev/null')

                github_url = ""
                if "github.com" in remote:
                    if remote.startswith("https://"):
                        github_url = remote.replace(".git", "")
                    elif remote.startswith("git@"):
                        github_url = "https://github.com/" + remote.split(":")[1].replace(".git", "")

                desc = get_readme_desc(repo)

                stack = []
                if os.path.isfile(os.path.join(repo, "package.json")): stack.append("Node.js")
                if os.path.isfile(os.path.join(repo, "requirements.txt")) or os.path.isfile(os.path.join(repo, "pyproject.toml")):
                    stack.append("Python")
                if os.path.isfile(os.path.join(repo, "docker-compose.yml")) or os.path.isfile(os.path.join(repo, "docker-compose.yaml")):
                    stack.append("Docker")
                if os.path.isfile(os.path.join(repo, "go.mod")): stack.append("Go")

                port = ""
                for env_file in glob.glob(os.path.join(repo, ".env*")):
                    try:
                        with open(env_file, 'r') as f:
                            for line in f:
                                m = re.match(r'SERVER_PORT\s*=\s*(\d+)', line)
                                if m: port = m.group(1)
                    except:
                        pass

                running = bool(port and check_port(port))
                stars = get_github_stars(github_url)

                try:
                    stat = os.stat(repo)
                    mtime = time.strftime("%Y-%m-%d", time.localtime(stat.st_mtime))
                except:
                    mtime = ""

                add(name, "📂", "installed", desc or "本地 Git 仓库",
                    " + ".join(stack) if stack else "", repo, github_url, port, running,
                    category="git", stars=stars, mtime=mtime)
    except PermissionError:
        continue

# ==========================================
# 2. Docker containers
# ==========================================
docker_info = run("docker info 2>/dev/null")
if docker_info:
    containers = run('docker ps -a --format "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}" 2>/dev/null')
    for line in containers.split('\n'):
        if not line.strip(): continue
        parts = line.split('|')
        if len(parts) < 4: continue
        name, image, status, ports = parts[0], parts[1], parts[2], parts[3]
        is_running = "up" in status.lower()
        port_match = re.search(r'0\.0\.0\.0:(\d+)', ports)
        port = port_match.group(1) if port_match else ""
        add(name, "🐳", "running" if is_running else "stopped",
            f"容器: {image}", "Docker", "", "", port, is_running, category="docker")

# ==========================================
# 3. Windows installed apps (Start Menu)
# ==========================================
start_menu = os.path.join(os.environ.get("APPDATA", ""),
                          "Microsoft", "Windows", "Start Menu", "Programs")
if os.path.isdir(start_menu):
    count = 0
    for root, dirs, files in os.walk(start_menu):
        if count >= 30:
            break
        for f in files:
            if f.endswith((".lnk", ".url")):
                name = os.path.splitext(f)[0]
                if any(kw in name.lower() for kw in ["uninstall", "help", "readme", "manual"]):
                    continue
                add(name, "📦", "installed", "Windows 应用", "Native",
                    os.path.join(root, f), category="app")
                count += 1
                if count >= 30:
                    break

# ==========================================
# 4. Bookmarks (loaded from static JSON)
# ==========================================
# (bookmarks are merged from projects.json by the web panel)

# ==========================================
# System info
# ==========================================
result = {
    "projects": PROJECTS,
    "system": {
        "hostname": get_hostname(),
        "uptime": get_uptime(),
        "disk": get_disk(),
        "memory": get_memory(),
        "docker": bool(docker_info),
    },
    "generated": time.strftime("%Y-%m-%d %H:%M:%S")
}

print(json.dumps(result, ensure_ascii=False, indent=2))
