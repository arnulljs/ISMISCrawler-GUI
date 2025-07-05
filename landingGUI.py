import kivy
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

class LoginScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

class ISMISCrawler(MDApp):
    def build(self):
        Window.size = (614, 768)
        Window.minimum_width = 614 
        Window.minimum_height = 768
        Window.maximum_width = 614
        Window.maximum_height = 768
        Window.resizable = False 
        Window.set_title("ISMIS Crawler")
        self.theme_cls.primary_palette = "Green"
        self.theme_cls.primary_hue = "700"
        self.theme_cls.theme_style = "Dark"
        Builder.load_file('kv/home.kv')
        return HomeScreen()

ISMISCrawler().run()