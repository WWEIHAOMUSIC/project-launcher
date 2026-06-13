#!/usr/bin/env python3
"""Auto-scan installed projects — Cross-platform (macOS + Windows)."""
import os, json, subprocess, glob, re, time, platform, sys, shutil

HOME = os.path.expanduser("~")
IS_WIN = platform.system() == "Windows"
IS_MAC = platform.system() == "Darwin"
PROJECTS = []

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
    """Check if a port is in use (cross-platform)."""
    if IS_WIN:
        # Windows: netstat
        out = run(f'netstat -ano | findstr ":{port}"')
        return bool(out.strip())
    else:
        # macOS / Linux: lsof
        return bool(run(f"lsof -ti:{port} 2>/dev/null"))

def get_hostname():
    if IS_WIN:
        return os.environ.get("COMPUTERNAME", "Windows PC")
    elif IS_MAC:
        return run("scutil --get ComputerName 2>/dev/null") or "Mac"
    return platform.node()

def get_disk():
    if IS_WIN:
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
        return {"total": "?", "used": "?", "free": "?", "percent": "?"}
    else:
        df = run("df -h /")
        parts = df.strip().split('\n')
        if len(parts) >= 2:
            cols = parts[-1].split()
            return {"used": cols[2], "free": cols[3], "total": cols[1], "percent": cols[4]}
    return {}

def get_memory():
    if IS_WIN:
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
        return {"total": "?", "used": "?", "free": "?", "percent": "?"}
    elif IS_MAC:
        total = int(run("sysctl -n hw.memsize"))
        vm = run("vm_stat")
        used_pages = 0
        for line in vm.split('\n'):
            if 'Pages active' in line: used_pages += int(line.split(':')[1].strip().replace('.',''))
            elif 'Pages wired' in line: used_pages += int(line.split(':')[1].strip().replace('.',''))
            elif 'Pages speculative' in line: used_pages += int(line.split(':')[1].strip().replace('.',''))
            elif 'Pages occupied by compressor' in line:
                used_pages += int(line.split(':')[1].strip().replace('.',''))
        used_gb = used_pages * 4096 / (1024**3)
        total_gb = total / (1024**3)
        return {"total": f"{total_gb:.0f}G", "used": f"{used_gb:.1f}G",
                "free": f"{total_gb - used_gb:.1f}G", "percent": f"{used_gb/total_gb*100:.0f}"}
    return {"total": "?", "used": "?", "free": "?", "percent": "?"}

def get_uptime():
    if IS_WIN:
        out = run("wmic os get LastBootUpTime")
        import datetime
        for line in out.split('\n')[1:]:
            line = line.strip()
            if line and len(line) >= 14:
                try:
                    boot = datetime.datetime.strptime(line[:14], "%Y%m%d%H%M%S")
                    delta = datetime.datetime.now() - boot
                    days = delta.days
                    hours = delta.seconds // 3600
                    mins = (delta.seconds % 3600) // 60
                    return f"{days}d {hours}h {mins}m"
                except:
                    pass
        return ""
    else:
        up = run("uptime")
        m = re.search(r'up\s+(.+?),', up)
        return m.group(1).strip() if m else ""

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
    # Try to get from local scan first via curl on all platforms
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

# ──────────────────────────────────────────────────
# 1. Scan Git repos in user's home
# ──────────────────────────────────────────────────
# Exclude workspace/agent directories
skip_dirs = [".qclaw", ".openclaw", ".nvm", ".hermes",
             "AppData", "Application Support"]

# On Windows, repos are under USERPROFILE; on macOS, under HOME
scan_roots = [HOME]
if IS_WIN:
    scan_roots.append(os.path.join(HOME, "Documents"))
    scan_roots.append(os.path.join(HOME, "Desktop"))

scanned = set()
# Only scan common locations, not deep recursive
scan_globs = [os.path.join(HOME, "*/.git")]  # top-level
if not IS_WIN:
    scan_globs.append(os.path.join(HOME, "Projects/*/.git"))
    scan_globs.append(os.path.join(HOME, "dev/*/.git"))
    scan_globs.append(os.path.join(HOME, "code/*/.git"))
    scan_globs.append(os.path.join(HOME, "Documents/*/.git"))
if IS_WIN:
    scan_globs.append(os.path.join(HOME, "source/*/.git"))
    scan_globs.append(os.path.join(HOME, "Desktop/*/.git"))

# Also scan common project directories
for extra in ["Documents", "Desktop", "Downloads", "Projects", "dev", "code", "source"]:
    p = os.path.join(HOME, extra)
    if os.path.isdir(p):
        for item in os.listdir(p):
            gitdir = os.path.join(p, item, ".git")
            if os.path.isdir(gitdir):
                scan_globs.append(gitdir)

# Add the known project directories from our config
known_repos = [
    os.path.join(HOME, "ai-goofish-monitor"),
]
for r in known_repos:
    g = os.path.join(r, ".git")
    if os.path.isdir(g):
        scan_globs.append(g)

for gitdir in set(scan_globs):
    if not os.path.isdir(gitdir):
        continue
    repo = os.path.dirname(gitdir)
    name = os.path.basename(repo)
    parts = repo.replace("\\", "/").split("/")
    if any(s in parts for s in skip_dirs):
        continue
    if repo in scanned:
        continue
    scanned.add(repo)

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
    if os.path.isfile(os.path.join(repo, "Cargo.toml")): stack.append("Rust")

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

# ──────────────────────────────────────────────────
# 2. Docker containers
# ──────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────
# 3. System-specific app scanning
# ──────────────────────────────────────────────────
if IS_WIN:
    # Scan Start Menu shortcuts as an indicator of installed apps
    start_menu = os.path.join(os.environ.get("APPDATA", ""),
                              "Microsoft", "Windows", "Start Menu", "Programs")
    if os.path.isdir(start_menu):
        count = 0
        for root, dirs, files in os.walk(start_menu):
            if count >= 20: break
            for f in files:
                if f.endswith((".lnk", ".url")):
                    name = os.path.splitext(f)[0]
                    if any(kw in name.lower() for kw in ["uninstall", "help", "readme"]):
                        continue
                    add(name, "📦", "installed", "Windows 应用", "Native",
                        os.path.join(root, f), category="app")
                    count += 1
elif IS_MAC:
    # Homebrew casks
    casks = run("brew list --cask 2>/dev/null")
    for cask in casks.split('\n'):
        if not cask.strip(): continue
        app_path = os.path.join("/Applications", f"{cask}.app")
        if not os.path.isdir(app_path):
            matches = glob.glob(f"/Applications/*{cask}*")
            app_path = matches[0] if matches else ""
        add(cask, "📦", "installed", "Homebrew 安装的应用", "Native", app_path,
            category="app")

# ──────────────────────────────────────────────────
# 4. Special known projects (from config or user bookmarks)
# ──────────────────────────────────────────────────
# These are loaded from the static projects.json to preserve
# web bookmarks and manual entries

# ──────────────────────────────────────────────────
# System info
# ──────────────────────────────────────────────────
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
