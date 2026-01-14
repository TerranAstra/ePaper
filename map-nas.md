

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



