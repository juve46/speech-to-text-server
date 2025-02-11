from flask import Flask, request, jsonify
import subprocess
import os
from google.cloud import speech
import io

app = Flask(__name__)

# תיקייה לשמירת קבצים זמניים
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# הגדרת Google Speech API
client = speech.SpeechClient()

def convert_audio(input_path, output_path):
    """ ממיר קובץ שמע (Opus/M4A) ל-WAV באמצעות FFmpeg """
    command = ["ffmpeg", "-i", input_path, "-ac", "1", "-ar", "16000", output_path, "-y"]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def transcribe_audio(file_path):
    """ מבצע המרת דיבור לטקסט עם Google Speech-to-Text """
    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="he-IL",
    )

    response = client.recognize(config=config, audio=audio)

    # החזרת הטקסט המזוהה
    return " ".join([result.alternatives[0].transcript for result in response.results])

@app.route("/upload", methods=["POST"])
def upload_file():
    """ API להעלאת קובץ שמע והמרתו לטקסט """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["opus", "m4a", "mp3", "wav"]:
        return jsonify({"error": "Unsupported file format"}), 400

    # שמירת הקובץ
    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    output_path = os.path.join(UPLOAD_FOLDER, "converted.wav")
    file.save(input_path)

    # המרת קובץ ל-WAV
    convert_audio(input_path, output_path)

    # המרת דיבור לטקסט
    text_result = transcribe_audio(output_path)

    # מחיקת קבצים זמניים
    os.remove(input_path)
    os.remove(output_path)

    return jsonify({"text": text_result})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
