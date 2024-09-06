# Blossom
import os
from dflow import Dflow
import subprocess
import pyaudio
import json
import threading
from vosk import Model, KaldiRecognizer

class Core:
    def __init__(self, name):
        self.name = name
        self.agent = Dflow(self)
        self.model_path = 'vosk-model-small-en-us-0.15'
        self.model = self.load_vosk_model()
        self.recognizer = KaldiRecognizer(self.model, 16000)
        self.query = None # shared variable to store recognized speech.
        self.speech_thread = None

    def load_vosk_model(self):
        if not os.path.exists(self.model_path):
            print(f'Model not found at {self.model_path}, please check the path.')
            exit(1)
        return Model(self.model_path)

    def speak(self, text):
        subprocess.run(['espeak', '-ven+f3', '-s 150', '-p 50', text])
        print(text)

    def recognize_speech(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=4096)
        stream.start_stream()

        print("Listening...")

        while True:
            data = stream.read(4096, exception_on_overflow=False)
            if self.recognizer.AcceptWaveform(data):
                result = json.loads(self.recognizer.Result())
                if 'text' in result and result['text'].strip() != "":
                    self.query = result['text'].strip() # update shared variable.
                    print(f'Recognized: {self.query}')

    def start_sr_thread(self):
        # start speech recognition in a seperate thread.
        self.speech_thread = threading.Thread(target=self.recognize_speech)
        self.speech_thread.daemon = True # ensures thread stops when main program exits.
        self.speech_thread.start()

    def run(self):
        self.start_sr_thread() # start recognizing speech in background.

        while True:
            if self.query: # check if new query is available.
                self.speak(self.agent.get_response(self.query.lower()))

                # for testing
                print(f'{self.agent.response.query_result.intent_detection_confidence} {self.agent.response.query_result.intent.display_name}')

                # reset the query so it doesn't get processed multiple times.
                self.query = None

if __name__ == '__main__':
    core = Core('Blossom')
    core.run()
