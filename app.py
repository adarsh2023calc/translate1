from flask import Flask, render_template, request, redirect, url_for, flash
from transformers import pipeline
from deep_translator import GoogleTranslator
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip
import subprocess
import webvtt
import os
import uuid
import torch
import pymysql
from flask_sqlalchemy import SQLAlchemy
import shutil
from google.cloud import texttospeech
from dotenv import load_dotenv
import time

load_dotenv()


print("CWD:", os.getcwd())



from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

YTDLP_PATH = r"C:\Users\adars\anaconda3\envs\tf\Scripts\yt-dlp.exe"
FFMPEG_PATH = r"C:\Users\adars\anaconda3\envs\tf\Library\bin\ffmpeg.exe"
print("ffmpeg exists:", os.path.exists(FFMPEG_PATH), FFMPEG_PATH)
print("yt-dlp exists:", os.path.exists(YTDLP_PATH), YTDLP_PATH)

print("ffmpeg shutil:", shutil.which("ffmpeg"))
print("yt-dlp shutil:", shutil.which("yt-dlp"))

os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH
os.environ["FFMPEG_BINARY"] = FFMPEG_PATH
os.environ["PATH"] = os.path.dirname(FFMPEG_PATH) + ";" + os.environ["PATH"]

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/youtube_processor?charset=utf8mb4'  # Update with your MySQL credentials
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -------------------- SUMMARIZER --------------------
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn",
    device=-1
)

# -------------------- DATABASE MODELS --------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    address = db.Column(db.Text, nullable=False)
    records = db.relationship('Record', backref='user', lazy=True)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    youtube_url = db.Column(db.Text, nullable=False)
    transcript = db.Column(db.Text)
    summary = db.Column(db.Text)
    translated_text = db.Column(db.Text)
    audio_path = db.Column(db.String(255))
    video_path = db.Column(db.String(255))
    language = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- SUBTITLE EXTRACTION --------------------
def extract_subtitles_yt_dlp(youtube_url):
    for f in os.listdir():
        if f.endswith(".vtt"):
            os.remove(f)

    subprocess.run([
        YTDLP_PATH,
        "--write-auto-sub",
        "--sub-lang", "en",
        "--skip-download",
        youtube_url
    ], check=True)

    vtt_files = [f for f in os.listdir() if f.endswith(".vtt")]
    if not vtt_files:
        raise Exception("No subtitles found")

    text = ""
    for caption in webvtt.read(vtt_files[0]):
        text += " " + caption.text

    return text




from google.cloud import texttospeech
import uuid
import os

def synthesize_text_google(translated_text, target_lang,audio_name):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(
        text=translated_text
    )

    # Language mapping (extend if needed)
    language_map = {
        "en": "en-US",
        "hi": "hi-IN",
        "ml": "ml-IN",
        "ta": "ta-IN",
        "te": "te-IN",
    }


    language_code = language_map.get(target_lang, "en-US")


    if language_code == "en-US":
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Chirp3-HD-Charon",  # best English voice
        )
    else:
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code  # auto-select native voice
        )

    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    
    with open(audio_name, "wb") as out:
        out.write(response.audio_content)

    return audio_name


# -------------------- SUMMARIZATION --------------------
def summarize_text(text):
    summaries = []
    for i in range(0, len(text), 900):
        chunk = text[i:i + 900]
        out = summarizer(chunk, max_length=150, min_length=60, do_sample=False)
        summaries.append(out[0]["summary_text"])
    return " ".join(summaries)


# -------------------- TRANSLATION (CHUNKED) --------------------
def translate_text_chunked(text, target_lang):
    translator = GoogleTranslator(source="en", target=target_lang)
    translated_chunks = []

    for i in range(0, len(text), 4500):
        translated_chunks.append(translator.translate(text[i:i + 4500]))

    return " ".join(translated_chunks)


# -------------------- SAFE VIDEO DOWNLOAD (403 PROOF) --------------------
def download_video_safe(url, output_path):
    try:
        # Try progressive MP4 (NO HLS)
        subprocess.run([
            YTDLP_PATH,
            "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
            "--merge-output-format", "mp4",
            "--user-agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "--referer", "https://www.youtube.com/",
            "--no-playlist",
            "-o", output_path,
            url
        ], check=True)

    except:
        try:
            # Retry with cookies if available
            subprocess.run([
                YTDLP_PATH,
                "--cookies", "cookies.txt",
                "-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
                "--merge-output-format", "mp4",
                "-o", output_path,
                url
            ], check=True)

        except:
            # FINAL fallback (always works)
            subprocess.run([
                YTDLP_PATH,
                "-f", "18",  # 360p MP4
                "-o", output_path,
                url
            ], check=True)


# -------------------- AUTH ROUTES --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username, phone=phone, email=email, password=password, address=address)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.')

    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():
    records = Record.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', records=records)

# -------------------- HOME ROUTE --------------------
@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('home.html')

# -------------------- PROCESS ROUTE --------------------
@app.route("/process", methods=["GET", "POST"])
@login_required
def index():
    
    transcript_text = ""
    translated_text = ""
    summary = ""
    audio_file = ""
    video_out = ""
    error = ""

    if request.method == "POST":
        pipeline_startup_time = time.time()
        try:
            url = request.form["url"]
            target_lang = request.form["language"]

            # 1️⃣ Extract subtitles
            transcript_text = extract_subtitles_yt_dlp(url)

            # 2️⃣ Summarize
            summary = summarize_text(transcript_text)
            #summary="eeeeeeeeeeeeeeeeeeeeeeeee"
            
            # 3️⃣ Translate
            translated_text = translate_text_chunked(summary, target_lang)

            # 4️⃣ Text → Speech
            audio_name = f"static/audio/{uuid.uuid4()}.mp3"
            
            start = time.time()
            synthesize_text_google(translated_text,target_lang,audio_name)
            end = time.time()
            latency = end- start

           

            print(f"Latency: {latency:.4f} seconds")
            # 5️⃣ Download video (403-safe)
            video_path = f"static/video/{uuid.uuid4()}.mp4"
            download_video_safe(url, video_path)

            # 6️⃣ REMOVE ORIGINAL AUDIO & ADD TRANSLATED AUDIO
            final_video = f"static/video/final_{uuid.uuid4()}.mp4"


            video_clip = VideoFileClip(video_path).without_audio()
            audio_clip = AudioFileClip(audio_name)

            audio_clip = audio_clip.subclip(0, min(audio_clip.duration, video_clip.duration))
            final_clip = video_clip.set_audio(audio_clip)

            sync_ratio=audio_clip.duration/video_clip.duration

            print("Sync Ratio:", sync_ratio)


            final_clip.write_videofile(
                final_video,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile="temp-audio.m4a",
                remove_temp=True
            )

            video_out = final_video

            # Store in database
            new_record = Record(
                user_id=current_user.id,
                youtube_url=url,
                transcript=transcript_text,
                summary=summary,
                translated_text=translated_text,
                audio_path=audio_name,
                video_path=video_out,
                language=target_lang
            )
            db.session.add(new_record)
            db.session.commit()
            pipeline_end_time = time.time()
            print("End-To-End Pipeline time: ", pipeline_end_time-pipeline_startup_time)

        except Exception as e:
            error = str(e)
    
    

    return render_template(
        "index.html",
        transcript=transcript_text,
        translated=translated_text,
        summary=summary,
        audio=audio_name,
        video=video_out,
        error=error
    )



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
