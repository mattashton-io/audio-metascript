import os
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from transcribe_logic import transcribe_and_translate

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# As per your request, the GCS bucket name is hardcoded here.
# For a production app, this would likely come from an environment variable.
BUCKET_NAME = "pytutoring-dev-bucket"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/transcribe', methods=['POST'])
def transcribe_route():
    print("beginning of transcribe_route function call... line 19")
    if 'audio_file' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio_file']
    source_language = request.form.get('source_lang')
    target_language = request.form.get('target_lang')

    if not audio_file.filename:
        return jsonify({'error': 'File is missing a name.'}), 400

    if not all([audio_file, source_language, target_language]):
        return jsonify({'error': 'Missing required parameters (audio_file, source_lang, target_lang)'}), 400

    print("before try reading audio_file... line 33")
    try:
        audio_content = audio_file.read()
        print("audio_file read ... line 36")
        transcript, translated_text = transcribe_and_translate(
            audio_file_content=audio_content,
            file_name=audio_file.filename,
            source_language_code=source_language,
            target_language_code=target_language,
            bucket_name=BUCKET_NAME
        )
        print("before json transcription... line 44")
        return jsonify({
            'transcription': transcript,
            'translation': translated_text
        })
    except Exception as e:
        # It's good practice to log the exception
        app.logger.error(f"An error occurred: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again later.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
