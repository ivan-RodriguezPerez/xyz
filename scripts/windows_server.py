from flask import Flask, request
import sounddevice as sd
import scipy.io.wavfile as wavfile
from faster_whisper import WhisperModel
import subprocess
import os
import time



AUDIO_DST_FOLDER = os.path.join(os.getcwd(), "audios")
AUDIO_FILE = "audio.wav"
audio_dst = os.path.join(AUDIO_DST_FOLDER, AUDIO_FILE)

if not os.path.exists(AUDIO_DST_FOLDER):
    os.mkdir(AUDIO_DST_FOLDER)

AUDIO_DURATION = 5  # [s]
FS = 44100 # Sample rate
DEVICE_INDEX = 1  # Microphone index

MODEL_SIZE = "large"
WHISPER_MODEL_PATH = "./whisper_model_large"

if not os.path.exists(WHISPER_MODEL_PATH):
    os.mkdir(WHISPER_MODEL_PATH)

# Initalize WhisperModel
t0 = time.time()
model = WhisperModel(
    model_size_or_path=MODEL_SIZE,
    device='auto',
    compute_type="int8",
    local_files_only=True,
    download_root=WHISPER_MODEL_PATH
)
t1 = time.time()
loading_time = round(t1 - t0, 2)
print(f"WhisperModel loaded successfully.\nLoading time: {loading_time} s.")


def record_audio():    
    
    try:
        print("Recording...")
        audio = sd.rec(
            int(AUDIO_DURATION * FS),
            samplerate=FS,
            channels=1,
            dtype='int16',
            device=DEVICE_INDEX
        )

        # Wait until record finished
        sd.wait()
        print("Record completed")

        # Save in WAV
        wavfile.write(audio_dst, FS, audio)

        return True

    except:
        return False


def transcribe_audio(file_path: str) -> str:
    """
    Transcribe audio using the FasterWhisper package.

    Args:
        file_path (str): Path to the input file (or a file-like object), or the audio waveform.

    Returns:
        transcription (str): transcribed audio in string format for the provided input audio or video. 

    """

    # Perform the transcription 
    segments, _ = model.transcribe(file_path)

    # Define object to return transcription
    transcription = ''

    # Merge all segments composing the transcription
    for i, segment in enumerate(segments):
        
        text = segment.text

        # Eliminate spaces at the beggining of the text in the first segment
        if i == 0 and segment.text[0] == ' ':
            while text[0] == ' ':
                text = text[1:]
        else:
            text = segment.text

        transcription += text

    # Format text setting the first letter as capital
    transcription = transcription.capitalize()

    return transcription


app = Flask(__name__)

@app.route('/')
def index():
    return 'Hello world!'

@app.route('/speak', methods=['POST'])
def speak():

    try:
        text = request.get_json()

        subprocess.run(["espeak-ng", text])

        return 'OK'
    
    except Exception as e:
        return f'ERROR: {e}'

@app.route('/listen', methods=['POST'])
def listen():

    text = request.get_json()['text']
    print(text)
    if text == "record_command":
        try:
            record_OK = record_audio()
            
            if record_OK:
                t0 = time.time()
                transcription = transcribe_audio(file_path=audio_dst)
                t1 = time.time()
                
                print(f"Transcription time: {t1 - t0}")

            return transcription
            
        except Exception as e:
            return f'ERROR: {e}'

    else:
        return "Empty action"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
