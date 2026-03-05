# 🎵 Yoto Downloader

A self-hosted, highly automated tool for downloading and preparing audio for [Yoto Player](https://us.yotoplay.com/) "Make Your Own" cards. 🚀

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
* **📂 Date-based Organization**: Archives downloads into `/audio/YYYY-MM/DD/` and `/covers/YYYY-MM/DD/` directories.
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
  │       └── 04/
  │           └── The Wheels on the Bus.m4a
  └── covers/
      └── 2026-03/
          └── 04/
              ├── The Wheels on the Bus.webp         # Original
              └── The Wheels on the Bus_square.jpg   # Ready for Yoto!

```
