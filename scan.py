#!/usr/bin/env python3
"""
Project Launcher Scanner — Auto-discover installed open-source projects on macOS.

Scans: Git repos, Docker containers, Homebrew casks, and user bookmarks.
Outputs JSON for the web panel.

Usage:
  python3 scan.py                    # Scan and output JSON
  python3 scan.py > projects.json    # Save to file
"""

import os, json, subprocess, glob, re, time

HOME = os.path.expanduser("~")
PROJECTS = []

# --- Config ---
# Directories to skip when scanning Git repos
SKIP_PREFIXES = [
    "/.qclaw/workspace", "/.openclaw/workspace",
    "/.nvm", "/.hermes", "/.cache", "/.local",
]

# User bookmarks file (JSON array of bookmark objects)
BOOKMARKS_FILE = os.path.join(os.path.dirname(__file__), "bookmarks.json")

# Max depth for Git repo scanning
SCAN_DEPTH = 3


def run(cmd):
    """Run shell command and return stdout."""
    try:
        return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
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


def get_disk():
    df = run("df -h /")
    parts = df.strip().split('\n')
    if len(parts) >= 2:
        cols = parts[-1].split()
        return {"used": cols[2], "free": cols[3], "total": cols[1], "percent": cols[4]}
    return {}


def get_memory():
    try:
        total = int(run("sysctl -n hw.memsize"))
    except ValueError:
        return {}
    vm = run("vm_stat")
    used_pages = 0
    for line in vm.split('\n'):
        if 'Pages active' in line:
            used_pages += int(line.split(':')[1].strip().replace('.', ''))
        elif 'Pages wired' in line:
            used_pages += int(line.split(':')[1].strip().replace('.', ''))
        elif 'Pages speculative' in line:
            used_pages += int(line.split(':')[1].strip().replace('.', ''))
        elif 'Pages occupied by compressor' in line:
            used_pages += int(line.split(':')[1].strip().replace('.', ''))
    used_gb = used_pages * 4096 / (1024**3)
    total_gb = total / (1024**3)
    return {
        "total": f"{total_gb:.0f}G",
        "used": f"{used_gb:.1f}G",
        "free": f"{total_gb - used_gb:.1f}G",
        "percent": f"{used_gb/total_gb*100:.0f}"
    }


def get_uptime():
    up = run("uptime")
    m = re.search(r'up\s+(.+?),', up)
    return m.group(1).strip() if m else "unknown"


def get_github_stars(github_url):
    """Fetch star count from GitHub API."""
    if not github_url or "/github.com/" not in github_url:
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
    except Exception:
        return ""


# ============================================================
# 1. Scan Git repositories
# ============================================================
patterns = []
for depth in range(1, SCAN_DEPTH + 1):
    patterns.append(f"{HOME}/" + "*/" * depth + ".git")

for gitdir in sorted(set(
    p for pattern in patterns
    for p in glob.glob(pattern)
)):
    repo = os.path.dirname(gitdir)
    name = os.path.basename(repo)

    # Skip internal/tool directories
    if any(s in repo for s in SKIP_PREFIXES):
        continue

    # Remote URL
    remote = run(f"git -C '{repo}' remote get-url origin 2>/dev/null")
    github_url = ""
    if remote.startswith("https://github.com/"):
        github_url = remote.replace(".git", "")
    elif remote.startswith("git@github.com:"):
        github_url = "https://github.com/" + remote.split(":")[1].replace(".git", "")

    # Description from README
    desc = ""
    readme_path = os.path.join(repo, "README.md")
    if os.path.isfile(readme_path):
        with open(readme_path, 'r', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(('#', '!', '>', '*', '-', '<', '|', '[', '{', '```', '---', '<!--')):
                    desc = line[:150]
                    break

    # Detect tech stack
    stack = []
    if os.path.isfile(os.path.join(repo, "package.json")):
        stack.append("Node.js")
    if os.path.isfile(os.path.join(repo, "requirements.txt")) or os.path.isfile(os.path.join(repo, "pyproject.toml")):
        stack.append("Python")
    if os.path.isfile(os.path.join(repo, "docker-compose.yml")) or os.path.isfile(os.path.join(repo, "docker-compose.yaml")):
        stack.append("Docker")
    if os.path.isfile(os.path.join(repo, "go.mod")):
        stack.append("Go")
    if os.path.isfile(os.path.join(repo, "Cargo.toml")):
        stack.append("Rust")
    if os.path.isfile(os.path.join(repo, "pom.xml")):
        stack.append("Java")

    # Detect port from .env files
    port = ""
    for env_file in glob.glob(os.path.join(repo, ".env*")):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    m = re.match(r'(?:SERVER_PORT|PORT|APP_PORT)\s*=\s*(\d+)', line)
                    if m:
                        port = m.group(1)
                        break
        except Exception:
            pass

    running = bool(port and run(f"lsof -ti:{port}"))
    stars = get_github_stars(github_url)

    try:
        stat = os.stat(repo)
        mtime = time.strftime("%Y-%m-%d", time.localtime(stat.st_mtime))
    except Exception:
        mtime = ""

    add(name, "📂", "installed", desc or "Local Git repository",
        " + ".join(stack) if stack else "", repo, github_url, port, running,
        category="git", stars=stars, mtime=mtime)


# ============================================================
# 2. Docker containers
# ============================================================
docker_info = run("docker info 2>/dev/null")
if docker_info:
    containers = run("docker ps -a --format '{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}' 2>/dev/null")
    for line in containers.split('\n'):
        if not line.strip():
            continue
        parts = line.split('|')
        if len(parts) < 4:
            continue
        name, image, status, ports = parts[0], parts[1], parts[2], parts[3]
        is_running = "up" in status.lower()
        port_match = re.search(r'0\.0\.0\.0:(\d+)', ports)
        port = port_match.group(1) if port_match else ""
        add(name, "🐳", "running" if is_running else "stopped",
            f"Container: {image}", "Docker", "", "", port, is_running,
            category="docker")


# ============================================================
# 3. Homebrew Casks (GUI applications)
# ============================================================
casks = run("brew list --cask 2>/dev/null")
for cask in casks.split('\n'):
    if not cask.strip():
        continue
    app_path = os.path.join("/Applications", f"{cask}.app")
    if not os.path.isdir(app_path):
        matches = glob.glob(f"/Applications/*{cask}*")
        app_path = matches[0] if matches else ""
    add(cask, "📦", "installed", "Homebrew Cask", "Native", app_path,
        category="app")


# ============================================================
# 4. User bookmarks (from bookmarks.json)
# ============================================================
if os.path.isfile(BOOKMARKS_FILE):
    try:
        with open(BOOKMARKS_FILE, 'r') as f:
            bookmarks = json.load(f)
        for bm in bookmarks:
            add(
                bm.get("name", ""),
                bm.get("icon", "🌐"),
                bm.get("status", "web"),
                bm.get("desc", ""),
                bm.get("stack", ""),
                "",
                bm.get("github", ""),
                "",
                bm.get("status") == "web",
                webUrl=bm.get("webUrl", ""),
                category="web",
                stars=bm.get("stars", "")
            )
    except Exception:
        pass


# ============================================================
# Output
# ============================================================
result = {
    "projects": PROJECTS,
    "system": {
        "hostname": run("scutil --get ComputerName 2>/dev/null") or "Mac",
        "uptime": get_uptime(),
        "disk": get_disk(),
        "memory": get_memory(),
        "docker": bool(docker_info),
    },
    "generated": time.strftime("%Y-%m-%d %H:%M:%S")
}

print(json.dumps(result, ensure_ascii=False, indent=2))
