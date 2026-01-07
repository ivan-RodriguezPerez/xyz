from flask import Flask, request
import sounddevice as sd
import scipy.io.wavfile as wavfile
from faster_whisper import WhisperModel
import os


AUDIO_DST_FOLDER = os.path.join(os.getcwd(), "audios")
AUDIO_FILE = "audio.wav"
audio_dst = os.path.join(AUDIO_DST_FOLDER, AUDIO_FILE)

print(audio_dst)
if not os.path.exists(AUDIO_DST_FOLDER):
    os.mkdir(AUDIO_DST_FOLDER)

AUDIO_DURATION = 5  # [s]
FS = 44100 # Sample rate
DEVICE_INDEX = 1  # Microphone index


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


def transcribe_audio(file_path: str, model_size: str = "tiny") -> str:
    """
    Transcribe audio using the FasterWhisper package.

    Args:
        file_path (str): Path to the input file (or a file-like object), or the audio waveform.
        model_size (str): Size of the model to use (tiny, tiny.en, base, base.en,
            small, small.en, distil-small.en, medium, medium.en, distil-medium.en, large-v1,
            large-v2, large-v3, large, distil-large-v2 or distil-large-v3), a path to a
            converted model directory, or a CTranslate2-converted Whisper model ID from the HF Hub.
            When a size or a model ID is configured, the converted model is downloaded
            from the Hugging Face Hub.

    Returns:
        transcription (str): transcribed audio in string format for the provided input audio or video. 
    """

    # Initalize WhisperModel
    model = WhisperModel(
        model_size_or_path=model_size,
        device='auto',
        compute_type="float32"
    )

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

@app.route('/listen', methods=['POST'])
def listen():

    text = request.get_json()['text']
    print(text)
    if text == "record_command":
        try:
            record_OK = record_audio()
            
            if record_OK:
                transcription = transcribe_audio(file_path=audio_dst)

            return transcription
            
        except Exception as e:
            return f'ERROR: {e}'

    else:
        return "Empty action"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
