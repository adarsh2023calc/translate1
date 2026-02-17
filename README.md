# 🎬 YouTube AI Processing Platform

An AI-powered web application that:

-   Extracts YouTube subtitles\
-   Summarizes using BART\
-   Translates to Indian languages\
-   Converts text to speech (SarvamAI)\
-   Replaces original audio with translated speech\
-   Stores records in MySQL

------------------------------------------------------------------------

# 🏗️ Tech Stack

-   Backend: Flask\
-   Database: MySQL\
-   NLP: HuggingFace Transformers (facebook/bart-large-cnn)\
-   Translation: Google Cloud Translation API\
-   TTS: SarvamAI\
-   Video Processing: MoviePy + FFmpeg\
-   Subtitle Extraction: yt-dlp

------------------------------------------------------------------------

# 🧪 1️⃣ Anaconda Environment Setup

## Step 1: Install Anaconda

Download and install:\
https://www.anaconda.com/products/distribution

## Step 2: Create Virtual Environment

conda create -n youtube_ai python=3.10\
conda activate youtube_ai

## Step 3: Install Dependencies

pip install flask flask-login flask-sqlalchemy pymysql\
pip install transformers torch\
pip install deep-translator\
pip install moviepy webvtt-py\
pip install sarvamai pyttsx3 yt-dlp\
pip install python-dotenv

------------------------------------------------------------------------

# 🎥 2️⃣ Install FFmpeg

Download from:\
https://www.gyan.dev/ffmpeg/builds/

After extraction, update path in your code:

FFMPEG_PATH = r"PATH_TO_FFMPEG`\ffmpeg`{=tex}.exe"

------------------------------------------------------------------------

# ⬇️ 3️⃣ Install yt-dlp

pip install yt-dlp

Or download binary from:\
https://github.com/yt-dlp/yt-dlp/releases

Update path in your code:

YTDLP_PATH = r"PATH_TO_YTDLP`\yt`{=tex}-dlp.exe"

------------------------------------------------------------------------

# 🗄️ 4️⃣ MySQL Database Setup

## Install MySQL

https://dev.mysql.com/downloads/mysql/

## Create Database

CREATE DATABASE youtube_processor CHARACTER SET utf8mb4;

## Update Flask Config

app.config\['SQLALCHEMY_DATABASE_URI'\] =\
'mysql+pymysql://root:YOUR_PASSWORD@localhost/youtube_processor?charset=utf8mb4'

------------------------------------------------------------------------

# 🔑 5️⃣ Google Cloud API Setup (Translation)

## Step 1: Create Google Cloud Project

https://console.cloud.google.com/

-   Create new project\
-   Enable **Cloud Translation API**

## Step 2: Create Service Account

-   IAM & Admin → Service Accounts\
-   Create service account\
-   Generate JSON key\
-   Download the JSON file

## Step 3: Set Environment Variable

Windows:

set GOOGLE_APPLICATION_CREDENTIALS=path`\to`{=tex}`\your`{=tex}-key.json

Mac/Linux:

export GOOGLE_APPLICATION_CREDENTIALS="path/to/your-key.json"

------------------------------------------------------------------------

# 🔊 6️⃣ SarvamAI API Setup

## Step 1: Get API Key

https://www.sarvam.ai/

Generate your API subscription key.

## Step 2: Set Environment Variable

Windows:

set sarvam_api=YOUR_SARVAM_API_KEY

Mac/Linux:

export sarvam_api="YOUR_SARVAM_API_KEY"

------------------------------------------------------------------------

# 📂 Required Folder Structure

project/\
│\
├── static/\
│ ├── audio/\
│ └── video/\
│\
├── templates/\
├── app.py\
└── README.md

------------------------------------------------------------------------

# ▶️ Run the Application

conda activate youtube_ai\
python app.py

Open browser:

http://127.0.0.1:5000

------------------------------------------------------------------------

# 🔐 Security Recommendations

-   Use password hashing (werkzeug.security)\
-   Store keys in .env file\
-   Do not commit API keys\
-   Add file cleanup mechanism\
-   Add rate limiting for production

------------------------------------------------------------------------

# 🚀 End-to-End Pipeline

YouTube URL\
↓\
Subtitle Extraction\
↓\
Summarization (BART)\
↓\
Translation\
↓\
Text-to-Speech\
↓\
Video Re-render\
↓\
Database Storage
