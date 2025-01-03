# /*============================================================================================================
# FILENAME        :ismisCrawl.py
# DESCRIPTION     :This script will enable us to scrape our grades without opening the ISMIS website.
# AUTHOR          :Zach Riane I. Machacon
# CREATED ON      :20 January 2022
# ============================================================================================================*/

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
ser = Service(r"C:\Users\Chrys Sean Sevilla\Documents\ISMISCrawler\chromedriver.exe")
browser = webdriver.Chrome(service=ser, options=options)
clear = lambda: os.system('clear')  # Clears the terminal
loginStatus = False  # Login status initially declared False to initialize next loop of gathering credentials
homepageCrash = False

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
    username = browser.find_element(By.ID, "Username")
    password = browser.find_element(By.ID, "Password")
    loginButton = browser.find_element(By.CSS_SELECTOR, "button.btn")
    print("Entering username...")
    username.send_keys(usernameInput)
    time.sleep(1)
    print("Entering password...")
    password.send_keys(passwordInput)
    time.sleep(1)
    print(f"Attempting login for {usernameInput}...")
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

print("Entering home page...")  # Enters homepage once loginStatus is set to True
time.sleep(5)
homepageCrash = checkSiteCrash("header_profile_pic")  # Program then checks for site crash using ISMIS Profile picture as an anchor
while homepageCrash == True:
    print("Site crashed. Refreshing...")
    browser.refresh()
    time.sleep(5)
    homepageCrash = checkSiteCrash("header_profile_pic")

time.sleep(5)
print("Opening multiple tabs and navigating to the grades page...")
browser.get("https://ismis.usc.edu.ph/advisedcourse")
homepageCrash = checkSiteCrash("header_profile_pic")  # Program then checks for site crash using ISMIS Profile picture as an anchor
while homepageCrash == True:
    print("Site crashed. Refreshing...")
    browser.refresh()
    time.sleep(5)
    homepageCrash = checkSiteCrash("header_profile_pic")

print("All tabs are loaded successfully.")

# Keep the browser open after navigation
# The browser will stay open until you manually close it
input("Press Enter to exit and close the browser.")
browser.quit()
