

Here are **copy/paste-ready** terminal commands for the Pi to **pull files from your NAS share** (`\\192.168.1.137\AiModels`) down to a default local folder (`~/AiModels`).

## Option A (recommended): mount SMB share, then copy/rsync

### 1) Install SMB mount support + make folders

```bash
cd ~
sudo apt update
sudo apt install -y cifs-utils rsync

mkdir -p ~/nas/AiModels
mkdir -p ~/AiModels
```

### 2) Mount the NAS share (try guest first)

```bash
sudo mount -t cifs //192.168.1.137/AiModels ~/nas/AiModels -o guest,uid=$(id -u),gid=$(id -g),iocharset=utf8,vers=3.0
```

If guest **fails** and you need credentials, use this instead (edit USER/PASS):

```bash
sudo mount -t cifs //192.168.1.137/AiModels ~/nas/AiModels -o username=NAS_USER,password=NAS_PASS,uid=$(id -u),gid=$(id -g),iocharset=utf8,vers=3.0
```

### 3) Copy everything down (safe, resumable)

```bash
cd ~
rsync -avh --progress ~/nas/AiModels/ ~/AiModels/
```

### 4) Unmount when done

```bash
sudo umount ~/nas/AiModels
```

---

## Option B (no mounting): use smbclient to download recursively

This is nice if you don’t want to mount anything.

### Install + download

```bash
cd ~
sudo apt update
sudo apt install -y smbclient

mkdir -p ~/AiModels
cd ~/AiModels

# guest mode
smbclient //192.168.1.137/AiModels -N -c 'recurse ON; prompt OFF; mget *'
```

If credentials required:

```bash
cd ~
mkdir -p ~/AiModels
cd ~/AiModels
smbclient //192.168.1.137/AiModels -U NAS_USER -c 'recurse ON; prompt OFF; mget *'
```

---

If you tell me whether your NAS share allows **guest** access (no username/password) and roughly how big it is, I can pick the safest default flags (e.g., `--partial`, `--inplace`, exclude patterns, etc.).



ls -la ~/.ollama
ls -la /usr/share/ollama/.ollama 2>/dev/null
ls -la /var/lib/ollama/.ollama 2>/dev/null
systemctl status ollama --no-pager 2>/dev/null | head -n 40

---


cd ~
set -e

# =========================
# NAS SETTINGS (EDIT THESE)
# =========================
NAS_IP="192.168.1.137"
NAS_SHARE="AiModels"
NAS_USER="jeff"
NAS_PASS="CHANGE ME"   # <-- put your real NAS password here

# =========================
# INSTALL DEPENDENCIES
# =========================
sudo apt update
sudo apt install -y cifs-utils rsync

# =========================
# DETECT OLLAMA MODELS DIR
# =========================
CANDIDATES=(
  "$HOME/.ollama/models"
  "/usr/share/ollama/.ollama/models"
  "/var/lib/ollama/.ollama/models"
)

# If ollama service sets OLLAMA_MODELS, prefer that
if systemctl is-active --quiet ollama 2>/dev/null; then
  OLLAMA_MODELS_FROM_SERVICE="$(systemctl show ollama --property=Environment 2>/dev/null \
    | tr ' ' '\n' \
    | sed -n 's/^Environment=//p' \
    | grep -E '^OLLAMA_MODELS=' \
    | head -n1 \
    | cut -d= -f2- || true)"
  if [ -n "$OLLAMA_MODELS_FROM_SERVICE" ]; then
    CANDIDATES=("$OLLAMA_MODELS_FROM_SERVICE" "${CANDIDATES[@]}")
  fi
fi

OLLAMADIR=""
for d in "${CANDIDATES[@]}"; do
  if [ -d "$d" ]; then
    OLLAMADIR="$d"
    break
  fi
done

# If none exist, create the usual default
if [ -z "$OLLAMADIR" ]; then
  OLLAMADIR="$HOME/.ollama/models"
  mkdir -p "$OLLAMADIR"
fi

echo "Using OLLAMADIR: $OLLAMADIR"
mkdir -p "$OLLAMADIR/blobs" "$OLLAMADIR/manifests"

# =========================
# MOUNT NAS
# =========================
sudo mkdir -p /mnt/nas_aimodels

# Clear prior mount if any (ignore errors)
sudo umount /mnt/nas_aimodels 2>/dev/null || true

sudo mount -t cifs "//$NAS_IP/$NAS_SHARE" /mnt/nas_aimodels \
  -o "username=$NAS_USER,password=$NAS_PASS,uid=$(id -u),gid=$(id -g),iocharset=utf8,vers=3.0,nofail"

# =========================
# COPY WITH RESUME SUPPORT
# =========================
# --partial keeps partially transferred files
# --append-verify resumes big files and verifies appended data
rsync -avh --progress --partial --append-verify /mnt/nas_aimodels/ "$OLLAMADIR/"

# =========================
# UNMOUNT
# =========================
sudo umount /mnt/nas_aimodels

echo "Done."
echo "Models copied into: $OLLAMADIR"
