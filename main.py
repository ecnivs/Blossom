# Blossom
from res_handler import ResponseHandler
from settings import *
import pyaudio
from vosk import Model, KaldiRecognizer
import time
from TTS.api import TTS
import torch
import wave
import queue
import uuid
import glob

class Core:
    """Core class responsible for managing speech recognition and text-to-speech and user queries."""
    def __init__(self):
        self.name = NAME
        self.model = VOSK_MODEL
        self.query = None
        self.called = False
        self.is_playing = False
        self.outstream = None

        self.on_init()

    def on_init(self):
        """Initializes the necessary components for the class instance."""
        self.lock = threading.Lock()
        self.condition = threading.Condition()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tts = TTS(model_name=TTS_MODEL).to(self.device)
        self.shutdown_flag = threading.Event()
        self.audio = pyaudio.PyAudio()
        self.model = self.load_vosk_model()
        self.recognizer = KaldiRecognizer(self.model, SAMPLING_RATE)
        self.handler = ResponseHandler(self)
        self.speech_queue = queue.Queue()
        self.audio_queue = queue.Queue()
        self.instream = self.audio.open(format=pyaudio.paInt16,
                channels = 1,
                rate = RATE,
                input = True,
                frames_per_buffer = FRAMES_PER_BUFFER)

    def load_vosk_model(self):
        """Loads the Vosk speech recognition model."""
        if not os.path.exists(self.model):
            logging.info(f'Model not found at {self.model}, please check the path.')
            exit(1)
        try:
            return Model(self.model)
        except ValueError as e:
            logging.error(f'Error loading Vosk model: {e}')
            exit(1)

    def speak(self, text):
        """Generate speech audio from text using TTS and queue it for playback."""
        try:
            output_wav = f"{uuid.uuid4().hex}_temp.wav"
            self.tts.tts_to_file(text, file_path = output_wav, speaker_wav = SPEAKER_WAV, language = "en")
            self.audio_queue.put(output_wav)
        except Exception as e:
            logging.error(f"TTS error: {e}")

    def play_audio(self, filename):
        """Play the generated or pre-recorded audio file."""
        def audio_thread():
            with self.lock:
                self.outstream = None
                try:
                    with wave.open(filename, 'rb') as wf:
                        chunk_size = min(CHUNK_SIZE, wf.getnframes())
                        self.outstream = self.audio.open(
                            format=self.audio.get_format_from_width(wf.getsampwidth()),
                            channels=wf.getnchannels(),
                            rate=wf.getframerate(),
                            output=True,
                            frames_per_buffer=chunk_size)

                        data = wf.readframes(wf.getnframes())
                        self.outstream.write(data)
                        time.sleep(0.1)
                        self.outstream.stop_stream()

                    if "_temp" in filename:
                        os.remove(filename)

                except Exception as e:
                    logging.error(f'Error during playback of {filename}: {e}')
                finally:
                    if self.outstream is not None:
                        if self.outstream.is_active():
                            self.outstream.stop_stream()
                        self.outstream.close()

        threading.Thread(target=audio_thread, daemon=True).start()

    def recognize_speech(self):
        """Capture and process speech input."""
        self.instream.start_stream()

        # load model into memory
        self.speech_queue.put("".join(self.handler.llm.get_response(f"Hey {self.name}")))

        logging.info("Listening...")

        try:
            while not self.shutdown_flag.is_set():
                data = self.instream.read(FRAMES_PER_BUFFER,
                                          exception_on_overflow=EXCEPTION_ON_OVERFLOW)

                if self.recognizer.AcceptWaveform(data):
                    result = json.loads(self.recognizer.Result())
                    if 'text' in result and result['text'].strip() != "":
                        with self.lock:
                            self.query = result['text'].strip()
                        logging.info(f'Recognized: {self.query}')

                with self.lock:
                    if not self.query:
                        continue

                    # lowercase and split
                    query_lower = self.query.lower().strip()
                    query_words = query_lower.split()
                    name_lower = self.name.lower()

                    # hotword detection
                    if any(word in query_lower for word in CALL_WORDS):
                        for word in CALL_WORDS:
                            if f'{word} {name_lower}' in query_lower:
                                self.called = True
                                logging.info("call detected!")
                                _, query = query_lower.split(f'{word} {name_lower}', 1)
                                if query.strip() == "" or len(query.strip().split()) < 2:
                                    self.query = None
                                    self.play_audio(START_WAV)
                                else:
                                    self.query = query.strip()
                                break

                    if self.called is not True:
                        if query_words[0] == name_lower and len(query_words) > 2:
                            self.called = True
                            logging.info("call detected!")
                            self.query = " ".join(query_words[1:])

        except IOError as e:
            logging.error(f'IOError in audio stream: {e}')
        except Exception as e:
            logging.error(f'Unexpected error in audio stream: {e}')
        finally:
            self.instream.stop_stream()
            self.instream.close()
            self.audio.terminate()
            logging.info("Audio stream terminated.")

    def process_queue(self):
        """ Process speech and audio playback queues."""
        if not self.speech_queue.empty():
            self.speak(self.speech_queue.get())
        if not self.audio_queue.empty():
            if not self.is_playing:
                self.play_audio(self.audio_queue.get())

    def run(self):
        """Main loop for processing user queries."""
        self.speech_thread = threading.Thread(target=self.recognize_speech, daemon=True)
        self.speech_thread.start()

        try:
            while True:
                self.process_queue()
                if self.called:
                    with self.lock:
                        if self.query:
                            logging.info("processing...")
                            self.play_audio(END_WAV)
                            self.called = False
                            self.handler.handle(self.query)
                        self.query = None
                time.sleep(0.1)

        except KeyboardInterrupt:
            logging.info("Shutting down...")
            self.shutdown_flag.set()
            self.handler.save_cache()
            self.handler.llm.session.close()
            self.handler.llm.unload_model()

            files = glob.glob("*_temp.wav")
            for file in files:
                os.remove(file)

            if self.speech_thread:
                self.speech_thread.join()
            logging.info("All threads terminated.")

if __name__ == '__main__':
    core = Core()
    core.run()
