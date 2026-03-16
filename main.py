"""
DocAssist - Mobile RAG Document Assistant
Main entry point for Kivy application
"""

import os
os.environ["KIVY_NO_ENV_CONFIG"] = "1"

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.utils import platform

# Set window size for desktop testing
if platform not in ("android", "ios"):
    Window.size = (400, 800)

from ui.main_screen import MainScreen
from kivy.uix.screenmanager import ScreenManager

KV = """
ScreenManager:
    MainScreen:
        name: 'main'
"""


class DocAssistApp(App):
    title = "DocAssist"

    def build(self):
        self.theme_cls = None
        return Builder.load_string(KV)

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == "__main__":
    DocAssistApp().run()
