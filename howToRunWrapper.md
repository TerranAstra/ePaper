
How to run
Start SQL Server:
x64 dev: docker compose -f docker-compose.mssql.yml --profile x64 up -d
Raspberry Pi: docker compose -f docker-compose.mssql.yml --profile pi up -d
Change the SA password in the compose file before using long term.
Run the events API:
dotnet run --project Frank.Events/Frank.Events.Api
Set SQL_CONNECTION_STRING (example): Server=localhost,1433;User ID=sa;Password=Your_strong_password123;TrustServerCertificate=True;Encrypt=False;Database=FrankEvents;
Point the streaming app to the API:
In gemini/geminiStreaming, set VITE_EVENTS_API_BASE (e.g., http://localhost:5000) and run npm run dev.


Instruction Set 3: 

Great—your share is up on 192.168.1.188 as \\AudioStream. Next, mount it RW on each Pi and test writes with atomic rename.

### Pi: mount read/write and persist
```bash
sudo apt update
sudo apt install -y cifs-utils smbclient

# Verify share lists
smbclient -L //192.168.1.188/ -U pi-share

# Mount point
sudo mkdir -p /data/audioStream

# Creds (use your memorable password)
sudo bash -c 'cat >/etc/samba/creds.audio <<EOF
username=pi-share
password=RiverCoffeeSky!42
domain=WORKGROUP
EOF'
sudo chmod 600 /etc/samba/creds.audio

# Mount now (RW; map ownership; permissive modes; avoid local permission checks)
sudo mount -t cifs //192.168.1.188/AudioStream /data/audioStream \
  -o credentials=/etc/samba/creds.audio,vers=3.0,rw,uid=$(id -u),gid=$(id -g),file_mode=0664,dir_mode=0775,noperm

# Persist across reboots (Pi default user is 1000:1000)
echo "//192.168.1.188/AudioStream /data/audioStream cifs credentials=/etc/samba/creds.audio,vers=3.0,rw,uid=1000,gid=1000,file_mode=0664,dir_mode=0775,noperm 0 0" | sudo tee -a /etc/fstab
```

If mount errors, try `vers=3.1.1` and/or add `,sec=ntlmssp`.

### Multi-Pi safe write convention
- Per-device folder and atomic rename: write `.part`, then `mv` to `.sav` when complete.
```bash
DEVICE_ID="${DEVICE_ID:-$(hostname -s | tr '[:upper:]' '[:lower:]')}"
DAY=$(date +%Y%m%d)
BASE="/data/audioStream/$DAY/$DEVICE_ID"
mkdir -p "$BASE"

NAME="audioStream$(date +%Y%m%d%H%M%S).ThreeWordSynopsis"
TMP="$BASE/$NAME.part"
FINAL="$BASE/$NAME.sav"

echo "payload or binary data" > "$TMP"
sync && mv "$TMP" "$FINAL"
```

- Your Windows host process should only pick up `.sav` files.

### Quick verification
- Pi: `touch /data/audioStream/test-from-pi.txt`
- Windows: confirm file appears in `C:\GitHub\TerranAstra\frank\gemini\fileShare\` (your shared path).
- Windows → Pi read-back: create a file in the share and `ls` it on the Pi.

This gives all Pis write access to the single Windows share with a shared memorable password, collision-safe naming, and atomic finalize for downstream pickup.


-----

Instruction Set 2: 

Here’s the smallest set of changes to make the share read/write, support multiple Pis writing concurrently, and keep a single memorable password.

### Windows: switch the share/user to read+write
- Create/ensure the folder:
```powershell
# PowerShell (Admin)
$sharePath = "C:\data\audioStream"
New-Item -ItemType Directory -Force -Path $sharePath | Out-Null
```

- Set a memorable password once for all Pis:
```powershell
# Example: change as you like (letters+words+number+symbol)
$memorable = "RiverCoffeeSky!42"
$pwd = ConvertTo-SecureString $memorable -AsPlainText -Force

# Create or update the local account used by Pis
if (-not (Get-LocalUser -Name "pi-share" -ErrorAction SilentlyContinue)) {
  New-LocalUser -Name "pi-share" -Password $pwd -PasswordNeverExpires -UserMayNotChangePassword $true
} else {
  Set-LocalUser -Name "pi-share" -Password $pwd
}
```

- Grant NTFS Modify and Share Change (write):
```powershell
# NTFS (Modify)
icacls $sharePath /grant "$env:COMPUTERNAME\pi-share:(OI)(CI)M"

# Create the share if missing (with write). If it exists, add write access.
if (-not (Get-SmbShare -Name "AudioStream" -ErrorAction SilentlyContinue)) {
  New-SmbShare -Name "AudioStream" -Path $sharePath -ChangeAccess "$env:COMPUTERNAME\pi-share"
} else {
  Grant-SmbShareAccess -Name "AudioStream" -AccountName "$env:COMPUTERNAME\pi-share" -AccessRight Change -Force
}

# Open SMB firewall group (once)
Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -Enabled True
```

- Get your Windows LAN IP (for the Pi mount):
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "169.*"} | Select-Object IPAddress, InterfaceAlias
```

### Raspberry Pi: mount read+write at /data/audioStream
- Install CIFS and mount the Windows share with write perms:
```bash
sudo apt update
sudo apt install -y cifs-utils smbclient

# Test the share list
smbclient -L //WIN_IP -U pi-share

# Mount point
sudo mkdir -p /data/audioStream

# Store creds (use the same memorable password)
sudo bash -c 'cat >/etc/samba/creds.audio <<EOF
username=pi-share
password=RiverCoffeeSky!42
domain=WORKGROUP
EOF'
sudo chmod 600 /etc/samba/creds.audio

# Mount now (rw + map ownership to local user so your processes can write)
sudo mount -t cifs //WIN_IP/AudioStream /data/audioStream \
  -o credentials=/etc/samba/creds.audio,vers=3.0,rw,uid=$(id -u),gid=$(id -g),file_mode=0664,dir_mode=0775,noperm

# Persist across reboots
echo "//WIN_IP/AudioStream /data/audioStream cifs credentials=/etc/samba/creds.audio,vers=3.0,rw,uid=1000,gid=1000,file_mode=0664,dir_mode=0775,noperm 0 0" | sudo tee -a /etc/fstab
```

### Multi‑Pi: simple conventions to avoid collisions
- Give each Pi a small ID (e.g., `pi01`, `pi02`, `pi03`). Use it in paths: `/data/audioStream/YYYYMMDD/pi01/...`.
- Write atomically: create `.part`, then rename to `.sav` when complete. Windows picker only processes `.sav`.
```bash
# Example write flow (on Pi)
device_id="pi01"
base="/data/audioStream/$(date +%Y%m%d)/$device_id"
mkdir -p "$base"
name="audioStream$(date +%Y%m%d%H%M%S).ThreeWordSynopsis"
tmp="$base/$name.part"
final="$base/$name.sav"

echo "payload (or your binary data)" > "$tmp"
sync
mv "$tmp" "$final"
```

- If multiple workers per Pi, add a suffix or a short UUID: `.../pi01/audioStreamYYYY...-$(uuidgen | cut -c1-8).sav`.

### Where this integrates with your apps
- The streaming app already proposes a save path; for multi‑Pi, we can include a `deviceId` in that path (set per Pi) and keep using the `.part -> .sav` finalize rule. Your Windows process should watch the share and only consume `.sav`.

That’s it. You’ll have read/write from any number of Pis into the single Windows share, unique filenames by timestamp/device, atomic renames for safe pickup, and one shared memorable password.



---------- 


Instruction Set 1: 

Below is a concise, safe walkthrough for Windows + Raspberry Pi on the same Wi‑Fi. We’ll: 1) create a Windows SMB share that Pi can read, 2) bring up SQL Server (or Azure SQL Edge on Pi), 3) run the C# Events API, 4) point the streaming app at it, 5) sanity‑check end to end.

### 1) Windows: create a read-only SMB share
- Folder: `C:\data\audioStream`
- Share name: `AudioStream`
- Create a dedicated read-only user (pi-share) for the Pi.

```powershell
# PowerShell (Run as Administrator)
$sharePath = "C:\data\audioStream"
New-Item -ItemType Directory -Force -Path $sharePath | Out-Null

# Create a local user for the share (pick a strong password)
$pwd = Read-Host "Enter password for user pi-share" -AsSecureString
New-LocalUser -Name "pi-share" -Password $pwd -PasswordNeverExpires -UserMayNotChangePassword $true

# Grant NTFS read permissions to that user
icacls $sharePath /grant "$env:COMPUTERNAME\pi-share:(OI)(CI)RX"

# Create SMB share with read-only access for that user
New-SmbShare -Name "AudioStream" -Path $sharePath -ReadAccess "$env:COMPUTERNAME\pi-share"

# Open SMB in firewall
Set-NetFirewallRule -DisplayGroup "File and Printer Sharing" -Enabled True

# Get your Windows LAN IP for later
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "169.*"} | Select-Object IPAddress, InterfaceAlias
```

Note: Use the local account `.\pi-share` and its password when authenticating from the Pi.

### 2) Raspberry Pi: mount the Windows share at /data/audioStream
```bash
# On Pi
sudo apt update
sudo apt install -y cifs-utils smbclient

# Optional: list shares to verify credentials
# Replace WIN_IP with your Windows IP, e.g. 192.168.1.50
smbclient -L //WIN_IP -U pi-share

# Create mount point
sudo mkdir -p /data/audioStream

# Store Windows creds
sudo bash -c 'cat >/etc/samba/creds.audio <<EOF
username=pi-share
password=YOUR_PASSWORD
domain=WORKGROUP
EOF'
sudo chmod 600 /etc/samba/creds.audio

# Mount now
sudo mount -t cifs //WIN_IP/AudioStream /data/audioStream \
  -o credentials=/etc/samba/creds.audio,vers=3.0,uid=$(id -u),gid=$(id -g),file_mode=0644,dir_mode=0755

# Persist across reboots
echo "//WIN_IP/AudioStream /data/audioStream cifs credentials=/etc/samba/creds.audio,vers=3.0,uid=1000,gid=1000,file_mode=0644,dir_mode=0755 0 0" | sudo tee -a /etc/fstab
```

Sanity test:
- On Windows: put a sample file into `C:\data\audioStream\YYYYMMDD\audioStreamYYYYMMDDHHMMSS.Sample.sav`.
- On Pi: `ls /data/audioStream/` and ensure you can see it (read-only is expected).

### 3) Database: choose one
- Windows (recommended): SQL Server 2022
```powershell
# In repo root on Windows
docker compose -f docker-compose.mssql.yml --profile x64 up -d
```

- Raspberry Pi (optional): Azure SQL Edge
```bash
# On Pi, in repo root copied there
docker compose -f docker-compose.mssql.yml --profile pi up -d
```

### 4) Events API (C#) – run and expose on LAN
- Decide where to run it (Windows or Pi). Example on Windows:

```powershell
# Connection string to the DB you started (adjust WIN_IP and password)
$env:SQL_CONNECTION_STRING = "Server=WIN_IP,1433;User ID=sa;Password=Your_strong_password123;TrustServerCertificate=True;Encrypt=False;Database=FrankEvents;"

# Run API on port 5000, listen on all interfaces
dotnet run --project Frank.Events/Frank.Events.Api --urls http://0.0.0.0:5000

# Open firewall for port 5000 (Windows)
New-NetFirewallRule -DisplayName "Frank.Events.Api 5000" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 5000
```

The API auto-creates the `FrankEvents` DB and `PingPongEvents` table on first POST.

### 5) Streaming app – point telemetry to the Events API
- In `gemini/geminiStreaming`, create `.env.local`:
```bash
VITE_EVENTS_API_BASE=http://WIN_IP:5000
```

- Install and run:
```bash
cd gemini/geminiStreaming
npm ci
npm run dev
```

When a turn (user/agent) finalizes, the app sends an event with a `proposedSavePath` like `/data/audioStream/20251105/audioStream202511050653.ThreeWordSynopsis.sav` (you’ll see matching folders/files on Windows once a writer is implemented; for now it’s recorded in the DB for future handoff).

### 6) Verify end-to-end
- Speak through the streaming console; after a response finalizes, query SQL:

```sql
SELECT TOP 10 EventId, Role, LEFT(Text,120) AS Text, ProposedSavePath
FROM dbo.PingPongEvents
ORDER BY [Timestamp] DESC;
```

- Confirm `ProposedSavePath` aligns with your share structure (Windows folder `C:\data\audioStream\YYYYMMDD\...` appears readably at `/data/audioStream/` on the Pi).

If you want the DB/API to run on the Pi instead, repeat steps 3–4 on the Pi (using the Pi’s IP in the connection string and `VITE_EVENTS_API_BASE`).

- I set up the Windows SMB share → Pi mount flow with read-only creds, brought up SQL Server (or SQL Edge on Pi), ran the Events API, and wired the streaming app to POST finalized turns. Files are named for uniqueness via the three-word synopsis and timestamp; actual writing is deferred but the path is ready for handoff.