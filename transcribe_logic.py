# First, you'll need to install the required Google Cloud libraries:
# pip install google-cloud-speech
# pip install google-cloud-translate
# pip install google-cloud-storage

# You'll also need to set up authentication.
# See: https://cloud.google.com/docs/authentication/getting-started

from google.cloud import speech
from google.cloud import translate_v2 as translate
from google.cloud import storage
import os

def transcribe_and_translate(audio_file_content, file_name, source_language_code, target_language_code, bucket_name):
    """
    Handles long audio transcription using GCS and translates the result.

    Args:
        audio_file_content (bytes): The raw content of the audio file.
        file_name (str): The original name of the audio file.
        source_language_code (str): The language for Speech-to-Text (e.g., 'en-US').
        target_language_code (str): The language for Translation (e.g., 'en').
        bucket_name (str): The GCS bucket to use for temporary storage.

    Returns:
        A tuple containing:
            - The original transcript (str).
            - The translated text (str).
    """
    print("beginning of transcribe_logic.py call... line 30 of transcribe_logic")
    # Initialize clients
    speech_client = speech.SpeechClient()
    translate_client = translate.Client()
    storage_client = storage.Client()

    # 1. Upload the audio file to GCS
    bucket = storage_client.bucket(bucket_name)
    blob_name = f"temp_audio/{file_name}"
    blob = bucket.blob(blob_name)
    
    blob.upload_from_string(audio_file_content)

    # 2. Get the gs:// URI for the file
    gcs_uri = f"gs://{bucket_name}/{blob_name}"

    # 3. Call the long_running_recognize method
    audio = speech.RecognitionAudio(uri=gcs_uri)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16, # Adjust if needed
        sample_rate_hertz=16000, # Adjust if needed
        language_code=source_language_code,
        enable_automatic_punctuation=True,
    )

    operation = speech_client.long_running_recognize(config=config, audio=audio)

    # 4. Wait for the operation to complete
    print("Waiting for transcription to complete...")
    response = operation.result(timeout=900) # Timeout in seconds

    # 5. Get the final transcript text
    transcript_builder = []
    for result in response.results:
        transcript_builder.append(result.alternatives[0].transcript)
    
    transcript = "\n".join(transcript_builder)

    # 6. Cleanup: Delete the temporary file from GCS
    try:
        blob.delete()
    except Exception as e:
        print(f"Warning: Failed to delete temporary file {gcs_uri}. Error: {e}")

    # 7. Translate the resulting text
    if not transcript:
        return "", ""

    translation_result = translate_client.translate(
        transcript, target_language=target_language_code
    )
    translated_text = translation_result["translatedText"]

    return transcript, translated_text
