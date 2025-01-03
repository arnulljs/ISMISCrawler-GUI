from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import getpass
import os

# Configurations
options = Options()
options.headless = False  # Enables Chromium browser to run without being visible
options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Disables DevTools logs on terminal
ser = Service(r"C:\\Users\\Chrys Sean Sevilla\\Documents\\ISMISCrawler\\chromedriver.exe")
browser = webdriver.Chrome(service=ser, options=options)
clear = lambda: os.system('clear')  # Clears the terminal
loginStatus = False  # Login status initially declared False to initialize next loop of gathering credentials

# Functions
def getUserInput(prompt, maximumNumber=None):
    if prompt == "What is your username?":
        if maximumNumber is not None:
            while True:
                userInput = input(prompt + "\n")
                if len(userInput) < maximumNumber:
                    return userInput
                print("Invalid Input. Username is over 10 characters")
    elif prompt == "What is your password?":
        return getpass.getpass(prompt)  # Censors password entry

def loginAttempt(username, password):
    browser.get("https://ismis.usc.edu.ph")
    username_field = browser.find_element(By.ID, "Username")
    password_field = browser.find_element(By.ID, "Password")
    loginButton = browser.find_element(By.CSS_SELECTOR, "button.btn")
    print("Entering username...")
    username_field.send_keys(username)
    time.sleep(1)
    print("Entering password...")
    password_field.send_keys(password)
    time.sleep(1)
    print(f"Attempting login for {username}...")
    loginButton.click()

def checkValidLogin(element):
    try:
        browser.find_element(By.CSS_SELECTOR, element)
    except NoSuchElementException:
        return True
    print("Wrong username/password. Please try again.")
    return False

def checkSiteCrash(element):
    try:
        browser.find_element(By.ID, element)
    except NoSuchElementException:
        return True
    return False

# Main
clear()

print("Welcome to blurridge's ISMIS Crawler!\n")
print("Delivering your grades without the hassle.")
time.sleep(1)
print("Loading...")

time.sleep(2)
clear()

while loginStatus == False:  # Upon failed login, program resets and asks for user input once again
    usernameInput = getUserInput("What is your username?", 10)
    clear()
    passwordInput = getUserInput("What is your password?", None)
    clear()
    loginAttempt(usernameInput, passwordInput)
    loginStatus = checkValidLogin("div.validation-summary-errors")

print("Entering home page...")
time.sleep(5)

# Ensure the homepage is fully loaded before proceeding
homepageCrash = checkSiteCrash("header_profile_pic")
while homepageCrash:
    print("Home page did not load correctly. Refreshing...")
    browser.refresh()
    time.sleep(5)
    homepageCrash = checkSiteCrash("header_profile_pic")

print("Home page successfully loaded.")

# Open 5 tabs
for i in range(5):
    browser.execute_script("window.open('');")  # Opens a new tab
    time.sleep(1)
    browser.switch_to.window(browser.window_handles[i])  # Switches to the new tab
    browser.get("https://ismis.usc.edu.ph/advisedcourse")  # Navigate to advised courses page
    time.sleep(3)

print("Cycling through tabs to ensure all are loaded...")

try:
    while True:  # Infinite loop to keep refreshing tabs
        for tab in range(len(browser.window_handles)):
            browser.switch_to.window(browser.window_handles[tab])
            homepageCrash = checkSiteCrash("header_profile_pic")
            while homepageCrash:
                print(f"Tab {tab + 1}: Site crashed. Refreshing...")
                browser.refresh()
                time.sleep(1)  # Shorter delay for faster retries
                homepageCrash = checkSiteCrash("header_profile_pic")
            print(f"Tab {tab + 1}: Successfully loaded.")
        time.sleep(1)  # Delay before switching tabs
except KeyboardInterrupt:
    print("\nProcess interrupted by user. Closing browser...")
    browser.quit()
