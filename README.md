# 🎬 YouTube Automator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.14-blue.svg)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg)
![FFmpeg](https://img.shields.io/badge/Rendering-FFmpeg-orange.svg)
![YouTube API](https://img.shields.io/badge/YouTube-API%20v3-red.svg)

**Automate YouTube video uploads with smart scheduling and batch processing**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Architecture](#-architecture) • [License](#-license)

</div>

---

## 📋 Description

YouTube Automator is a powerful tool for automating the creation and upload of music videos to YouTube. The application allows you to convert MP3 files into videos with cover images and automatically upload them to your channel on a schedule.

### ✨ Features

- 🎵 **Batch Processing** - process multiple MP3 files simultaneously
- 🖼️ **Automatic Video Creation** - convert audio + image to video via FFmpeg
- 📅 **Smart Scheduling** - automatic uploads on schedule
- 🎨 **Beautiful GUI** - modern interface built with CustomTkinter
- 📝 **Metadata Templates** - saved presets for titles, descriptions and tags
- 🔄 **Pattern Mode** - automatically apply different presets to files by patterns
- ☁️ **YouTube API Integration** - direct upload with OAuth 2.0 support
- 📊 **Queue Database** - SQLite for tracking job status
- 🛡️ **Error Handling** - protection against YouTube API quota exceeded
- 🧵 **Multi-threading** - background worker for async processing

---

## 🏗️ Architecture

The project is built following **Clean Architecture** principles with clear separation of concerns:

```
src/
├── domain/              # Business logic (entities, ports)
├── application/         # Use cases (scheduler, worker, DTOs)
├── infrastructure/      # External services
│   ├── db/             # SQLite repository
│   ├── ffmpeg/         # Video rendering
│   ├── youtube/        # YouTube API uploader
│   └── ioc_container.py # Dependency Injection
└── presentation/        # GUI (CustomTkinter)
```

### Core Components

- **Domain Layer**: Entities (Job) and interfaces (Ports)
- **Application Layer**: Scheduler, Worker, Presets, DTOs
- **Infrastructure Layer**: Port implementations (Repository, Renderer, Uploader)
- **Presentation Layer**: GUI and controllers

---

## 🚀 Installation

### Requirements

- Python 3.14+
- FFmpeg (included in `src/bin/`)
- YouTube API credentials

### Step 1: Clone the repository

```bash
git clone https://github.com/your-username/yt_automator.git
cd yt_automator
```

### Step 2: Install dependencies

Create `requirements.txt`:

```txt
customtkinter>=5.2.0
google-auth>=2.16.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.80.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 3: Configure YouTube API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop app)
5. Download the JSON file and save it as `src/client_secrets.json`

### Step 4: Run the application

```bash
python src/main.py
```

On first launch, a browser will open for YouTube authorization. After successful authorization, the token will be saved in `src/token.json`.

---

## 💻 Usage

### 1️⃣ Select Files

- **Select MP3 Folder** - choose a folder with audio files
- **Select Fallback Cover** - choose a cover image (1920x1080)

### 2️⃣ Configure Schedule

- **Start Date** - date of first publication (format: YYYY-MM-DD)
- **Interval** - interval between publications (in days)

### 3️⃣ Metadata

#### Single Preset Mode
Use one preset for all videos:
- **Title Template**: `{filename} - Music Video`
- **Description**: Video description
- **Tags**: `music, audio, relaxation` (comma-separated)

#### Pattern Mode
Apply different presets to different files:
```
Pattern: *meditation* → Preset: Meditation
Pattern: *sleep* → Preset: Sleep Music
Pattern: * → Preset: Default (fallback)
```

### 4️⃣ Generate and Run

1. Click **⚡ GENERATE BATCH** - creates jobs in the queue
2. Click **🚀 START UPLOADING** - starts the worker
3. Monitor progress in the **📊 Jobs** tab

---

## 📝 Configuration

File `src/config.py`:

```python
VIDEO_WIDTH = 1920          # Video width
VIDEO_HEIGHT = 1080         # Video height
FFMPEG_PRESET = "ultrafast" # FFmpeg preset (ultrafast/fast/medium)
YOUTUBE_CATEGORY_ID = "10"  # YouTube category (10 = Music)
```

---

## 📊 Database Structure

SQLite database (`src/data/queue.db`):

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    audio_path TEXT NOT NULL,
    image_path TEXT NOT NULL,
    title TEXT,
    description TEXT,
    tags TEXT,
    publish_at TEXT,
    status TEXT,  -- PENDING, PROCESSING, COMPLETED, FAILED
    video_id TEXT,
    error_message TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

---

## 🔧 Extensions

### Adding a New Renderer

1. Implement the `RendererPort` interface in `domain/ports.py`
2. Create a class in `infrastructure/`
3. Register it in `ioc_container.py`

### Adding a New Platform

The architecture allows easy integration with other platforms (Vimeo, Dailymotion, etc.) by implementing new ports.

---

## ⚠️ Limitations

- **YouTube API Quota**: Default 10,000 units/day
- **Upload cost**: ~1,600 units per video
- **Max videos/day**: ~6 uploads with free quota

---

## 🐛 Known Issues

- FFmpeg required in `src/bin/` (Windows)
- OAuth token refreshes automatically
- Worker stops automatically when quota is exceeded

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---


<div align="center">

**⭐ If you found this project helpful, please give it a star! ⭐**

Made with ❤️ by holydxvi

</div>

