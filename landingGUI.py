import kivy
import os
from kivymd.app import MDApp
from kivy.lang import Builder
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle
from kivy.config import Config
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.dialog import (
    MDDialogHeadlineText,
    MDDialogSupportingText,
    MDDialogButtonContainer,
)
from kivymd.uix.button import MDButton, MDButtonText
from kivy.clock import Clock


class LoginScreen(Screen):
    pass

class HomeScreen(Screen):
    pass

class ISMISCrawler(MDApp):
    dialog = None
    
    def runISMIS(app):
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        import time

        def show(msg):
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: app.show_dialog("Logging in...", msg, auto_dismiss=False), 0)

        show("Launching browser...")
        options = Options()
        options.headless = False
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        service = Service("./chromedriver.exe")
        browser = webdriver.Chrome(service=service, options=options)

        show("Reading credentials...")
        with open("credentials.txt", "r") as f:
            username, password = [line.strip() for line in f.readlines()]

        show("Opening ISMIS...")
        browser.get("https://ismis.usc.edu.ph")

        while True:
            try:
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn"))
                )
                break
            except:
                show("Retrying ISMIS page...")
                browser.refresh()
                time.sleep(3)

        show("Filling in credentials...")
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "Username"))).send_keys(username)
        browser.find_element(By.ID, "Password").send_keys(password)
        browser.find_element(By.CSS_SELECTOR, "button.btn").click()

        show("Login successful! Launching dashboard...")
        time.sleep(2)  # simulate wait or dashboard load
            
    def _run_ismis_and_continue(self):
        try:
            self.runISMIS()
        except Exception as e:
            # Show error and exit early
            Clock.schedule_once(lambda dt: self.show_dialog("Login Failed", str(e), auto_dismiss=True), 0)
            return

        # Dismiss the loading dialog
        Clock.schedule_once(lambda dt: self.dialog.dismiss() if self.dialog else None, 0.1)

        # Go to home screen
        Clock.schedule_once(lambda dt: self.goto_home(), 0.5)

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
        Builder.load_file('kv/login.kv')
        
        self.sm = ScreenManager()
        self.login_screen = LoginScreen(name="login")
        self.home_screen = HomeScreen(name="home")

        self.sm.add_widget(self.login_screen)
        self.sm.add_widget(self.home_screen)
            
        self.check_credentials()

        return self.sm
    
    def check_credentials(self):
        if os.path.exists("credentials.txt"):
            with open("credentials.txt", "r") as file:
                lines = file.readlines()
                if len(lines) == 2:
                    username = lines[0].strip()
                    password = lines[1].strip()

                    # Show loading dialog
                    self.show_dialog("Auto Login", "Logging you in automatically...", auto_dismiss=False)

                    # Start selenium in background thread
                    import threading
                    threading.Thread(target=self._run_ismis_and_continue).start()
                    return

        self.sm.current = "login"

            
    def on_login(self):
        username = self.login_screen.ids.username.text.strip()
        password = self.login_screen.ids.password.text.strip()
        
        if username and password:
            self.login(username, password, save=True)
        else:
            self.show_dialog("Username or password cannot be empty.")
            
    def login(self, username, password, save=False):
        if save:
            try:
                with open("credentials.txt", "w") as file:
                    file.write(f"{username}\n{password}")
            except Exception as e:
                self.show_dialog("Error", f"Failed to save credentials:\n{str(e)}")
                return

        self.show_dialog("Logging in...", "Please wait while we log you into ISMIS.", auto_dismiss=False)

        import threading
        threading.Thread(target=self._run_ismis_and_continue).start()

    def goto_home(self, *args):
        self.sm.current = "home"

    def show_dialog(self, title, text, on_dismiss=None, auto_dismiss=False):
        if self.dialog:
            self.dialog.dismiss()

        self.dialog = MDDialog(
        MDDialogHeadlineText(text=title),
        MDDialogSupportingText(text=text),
        auto_dismiss=auto_dismiss,
        )

        if on_dismiss:
            self.dialog.bind(on_dismiss=lambda x: on_dismiss())

        self.dialog.open()

        if auto_dismiss and on_dismiss:
            Clock.schedule_once(lambda dt: self.dialog.dismiss(), 1)  # delay 1s
            Clock.schedule_once(lambda dt: on_dismiss(), 1.1) 
        
    def on_logout(self):
        if self.dialog:
            self.dialog.dismiss()
            self.dialog = None

        self.sm.current = "login"

ISMISCrawler().run()