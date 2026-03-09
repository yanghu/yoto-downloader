# 🎵 Yoto Downloader

A self-hosted, highly automated tool for downloading and preparing audio for [Yoto Player](https://us.yotoplay.com/) "Make Your Own" cards. 🚀

[📖 中文文档](README_cn.md)

## 🌟 Why This Exists? (The Pain Point)

Every parent knows the scene: your child hears a song they love and immediately asks, **"Can I have this on my Yoto?"** Currently, the process is full of friction:

1. **The "Pending List"**: You send a link to yourself or your spouse to remember it later.
2. **Manual Labor**: Once you're at your computer, you have to manually run `yt-dlp` or similar tools.
3. **The Image Struggle**: You have to find, download, and manually crop a cover photo into a perfect square.
4. **The Delay**: By the time you've finished, the "magic moment" has passed.

**Yoto Downloader** turns this multi-step chore into a 5-second action on your phone. Send the link via your Share Sheet, and let your NAS handle the rest. 👶🎶

## 🧱 System Components

To get this workflow running, you'll need the following parts:

1. **A Server (NAS or PC)**: An always-on machine running Docker to host the Web API.
2. **File Access (SMB/Shared Folder)**: A shared folder on your NAS where the audio and images are stored. This allows your iPhone to "see" the files via the Files app.
3. **iPhone with Shortcuts App**: The bridge that connects your YouTube app to your server.

## ✨ Features

* **⚡ FastAPI Backend**: Provides immediate HTTP 200 responses with video metadata to prevent iOS Shortcut timeouts.
* **🎧 Optimized Audio Extraction**: Extracts the best available audio stream (saved as `.m4a`) without unnecessary re-encoding.
* **🖼️ Auto Square Crop**: Automatically detects the thumbnail and uses `Pillow` to crop it to a perfect 1:1 ratio (`_square.jpg`).
* **🤖 JS Challenge Support**: Includes `Deno` to handle YouTube's latest signature and JavaScript challenges.
* **📂 Date-based Organization**: Archives downloads into `/audio/YYYY-MM/` and `/covers/YYYY-MM/` directories.
* **📦 One-click Archive**: Move all processed songs to a flat `/archive/` directory after adding them to Yoto cards.
* **🔔 Discord Notifications**: Sends a webhook notification once the processing is complete. ✅
* **🛡️ NAS Friendly**: Supports `PUID` and `PGID` for seamless SMB permission management.
* **🖥️ Web UI**: Built-in song management dashboard for browsing, searching, and deleting downloads.

## 🖥️ Web UI — Song Manager

Access the built-in management dashboard at `http://<YOUR_NAS_IP>:8000/`.

<img src="docs/ui-demo.webp" alt="Song Manager Demo" width="800">

**Capabilities:**

- **Unified View**: Browse all downloaded songs and covers across every date in one place
- **Duplicate Detection**: Songs with the same title on different dates are flagged with a "重复" badge
- **Search & Filter**: Instantly filter songs by title with live stats updates
- **Multi-Select**: Click cards or use the "Select All" checkbox, then bulk-delete with a confirmation dialog
- **Cover Art**: Displays the auto-cropped square cover art for each song

## 🚀 Getting Started

### 1. Setup Environment

Clone the repository and create an `.env` file:

```bash
cp .env_example .env

```

Edit the `.env` file (refer to `.env_example` for details). Ensure `PUID` and `PGID` match your NAS user to avoid permission issues via SMB.

### 2. Run with Docker Compose

```bash
docker-compose up -d

```

## 🛠️ Development & CI/CD

### Local Development

All common tasks are driven by `make`. Run `make help` to see available targets.

```bash
make dev        # Build and start the dev stack with hot-reload (http://localhost:8000)
make dev-logs   # Tail logs from the dev stack
make dev-down   # Stop and remove the dev stack
```

The dev stack uses `docker-compose.dev.yml`, which mounts the `./app` source directory
into the container so code changes are picked up without a full rebuild.

### Testing

Two test layers are provided:

| Command | What it does | Requires |
|---|---|---|
| `make test` | Unit tests — fast, no Docker needed | Python + `requirements-test.txt` |
| `make smoke` | End-to-end smoke tests against a live server | `make dev` running first |

**Setup for unit tests:**

```bash
pip install -r requirements-test.txt
make test
```

Unit tests live in `tests/` and use `pytest`. Tests marked `smoke` are excluded by default
(see `pytest.ini`). The `conftest.py` mocks `yt_dlp`, `requests`, and `ensure_dirs` so tests
run without Docker or file system access to `/downloads`.

**Smoke tests** (end-to-end):

```bash
make dev     # start the stack
make smoke   # POST a real URL and verify the response
```

### Manual Docker Build & Push

```bash
make build              # Build the image locally
make push               # Build + push to Docker Hub (yang517/yoto-downloader:latest)
make push TAG=v1.2.3    # Push with a specific tag
```

### NAS Deployment

After pushing an image, you can deploy it to your NAS in one command:

```bash
make deploy-nas
```

This will:
1. Warn if `.env` is missing on the NAS (it's never overwritten)
2. Copy `docker-compose.yml` to the NAS
3. Pull the latest image and restart the service via SSH

Configure the target in your `.env` (see `.env_example`):

```env
NAS_USER=admin
NAS_IP=192.168.1.100
NAS_DIR=/volume1/docker/yoto-downloader
NAS_COMPOSE_CMD=sudo /usr/local/bin/docker-compose  # adjust for your system
```

Or override on the command line: `make deploy-nas NAS_IP=192.168.1.100`

### GitHub Actions CI/CD

The workflow at `.github/workflows/ci-cd.yml` runs automatically on every push and pull request.

```
Every push / PR
    └─ [test]  python -m pytest tests/ -m "not smoke" -v
                    │
                    │  only on push to main, and only if tests pass
                    ▼
             [publish]  docker build + push to Docker Hub
                        → yang517/yoto-downloader:latest
                        → yang517/yoto-downloader:<short-sha>
```

**Required GitHub repository secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|---|---|
| `DOCKERHUB_USERNAME` | Your Docker Hub username |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Account Settings → Security → New Access Token) |

Once set, every merge to `main` will automatically run tests and publish a fresh image.
PRs only run tests — no image is published.

## 📱 iOS Shortcut Setup

1. Enable **Show in Share Sheet** (Accepts: *URLs* and *Articles/Text*).
2. Add action: **Get URLs from Input**. (Crucial for extracting clean links from YouTube's shared text).
3. Add action: **Get contents of URL**.
4. Configure:
* URL: `http://<YOUR_NAS_IP>:8000/download`
* Method: `POST`
* Request Body: `JSON`
* Key: `url` (Text) -> Value: *Output from "Get URLs from Input"*.



## 📁 Folder Structure

```text
/downloads
  ├── audio/
  │   └── 2026-03/
  │       └── The Wheels on the Bus.m4a
  ├── covers/
  │   └── 2026-03/
  │       ├── The Wheels on the Bus.webp         # Original
  │       └── The Wheels on the Bus_square.jpg   # Ready for Yoto!
  └── archive/                                   # After one-click archive
      ├── audio/
      │   └── The Wheels on the Bus.m4a
      └── covers/
          └── The Wheels on the Bus_square.jpg
```
