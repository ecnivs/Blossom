from settings import *
import webbrowser

class ActionHandler:
    def __init__(self, core):
        self.core = core

    def run_cmd(self, command, shell=True, capture_output=True, text=True, check=True):
        try:
            result = subprocess.run(command, shell=shell, capture_output=capture_output, text=text, check=check)
            logging.info(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            logging.error(f"Error: {e}")

    def toggle_camera(self, state):
        self.core.handler.llm.cam = state

    def toggle_screenshots(self, state):
        self.core.handler.llm.ss = state

    def open_site(self, url, new=0, autoraise=True):
        webbrowser.open(url, new=new, autoraise=autoraise)

    def take_picture(self):
        response_text = self.core.handler.llm.get_response("", cam = True)
        self.core.handler.process_response(response_text)

    def take_screenshot(self):
        response_text = self.core.handler.llm.get_response("", ss = True)
        self.core.handler.process_response(response_text)
