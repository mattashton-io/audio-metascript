import os
import uuid
import threading
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from transcribe_logic import transcribe_and_translate

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# --- In-memory Job Store ---
# In a production app, you'd use a more robust solution like Redis or a database.
JOBS = {}

# As per your request, the GCS bucket name is hardcoded here.
# For a production app, this would likely come from an environment variable.
BUCKET_NAME = "pytutoring-dev-bucket"

@app.route('/')
def index():
    return render_template('index.html')

def run_transcription_job(job_id, audio_content, file_name, source_lang, target_lang):
    """The background task that runs the transcription and updates the job status."""
    try:
        transcript, translated_text = transcribe_and_translate(
            audio_file_content=audio_content,
            file_name=file_name,
            source_language_code=source_lang,
            target_language_code=target_lang,
            bucket_name=BUCKET_NAME
        )
        JOBS[job_id] = {
            "status": "COMPLETE",
            "transcription": transcript,
            "translation": translated_text
        }
    except Exception as e:
        app.logger.error(f"Job {job_id} failed: {e}")
        JOBS[job_id] = {"status": "FAILED", "error": str(e)}

@app.route('/api/transcribe', methods=['POST'])
def transcribe_route():
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio_file']
    source_language = request.form.get('source_lang')
    target_language = request.form.get('target_lang')

    if not audio_file.filename:
        return jsonify({'error': 'File is missing a name.'}), 400

    if not all([audio_file, source_language, target_language]):
        return jsonify({'error': 'Missing required parameters'}), 400

    job_id = str(uuid.uuid4())
    audio_content = audio_file.read()

    # Store job with PENDING status
    JOBS[job_id] = {"status": "PENDING"}

    # Start the background thread
    thread = threading.Thread(
        target=run_transcription_job,
        args=(job_id, audio_content, audio_file.filename, source_language, target_language)
    )
    thread.start()

    return jsonify({'job_id': job_id})

@app.route('/api/status/<job_id>')
def status_route(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
