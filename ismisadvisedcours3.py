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
USERNAME = "21101819"  # Replace with your ISMIS username
PASSWORD = "seansevilla15"  # Replace with your ISMIS password

options = Options()
options.headless = False  # Enables Chromium browser to run without being visible
options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Disables DevTools logs on terminal
ser = Service(r"C:\Users\Chrys Sean Sevilla\Documents\ISMISCrawler\chromedriver.exe")
browser = webdriver.Chrome(service=ser, options=options)
clear = lambda: os.system('clear')  # Clears the terminal
loginStatus = False  # Login status initially declared False to initialize next loop of gathering credentials
homepageCrash = False

# Functions

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
    print("Wrong username/password. Please check your credentials.")
    return False

def checkSiteCrash(element):
    try:
        browser.find_element(By.ID, element)
    except NoSuchElementException:
        return True
    return False

def isLoginExpired():
    """Check if the session has expired by detecting the login elements."""
    try:
        browser.find_element(By.ID, "Username")
        browser.find_element(By.ID, "Password")
        browser.find_element(By.CSS_SELECTOR, "button.btn")
        return True
    except NoSuchElementException:
        return False

# Main

clear()

print("Welcome to blurridge's ISMIS Crawler!\n")
print("Delivering your grades without the hassle.")
time.sleep(1)
print("Loading...")

time.sleep(2)
clear()

while loginStatus == False:  # Initial login attempt
    loginAttempt(USERNAME, PASSWORD)
    loginStatus = checkValidLogin("div.validation-summary-errors")

print("Entering home page...")  # Enters homepage once loginStatus is set to True
time.sleep(5)
homepageCrash = checkSiteCrash("header_profile_pic")  # Program checks for site crash using ISMIS Profile picture as an anchor
while homepageCrash == True:
    print("Site crashed. Refreshing...")
    browser.refresh()
    time.sleep(5)
    homepageCrash = checkSiteCrash("header_profile_pic")

time.sleep(5)
print("Opening multiple tabs and navigating to the grades page...")
browser.get("https://ismis.usc.edu.ph/advisedcourse")

while True:
    homepageCrash = checkSiteCrash("header_profile_pic")
    if homepageCrash:
        print("Site crashed. Refreshing...")
        browser.refresh()
        time.sleep(5)
        continue

    if isLoginExpired():  # Check if login session has expired
        print("Session expired. Logging in again...")
        
        # Try to log in again
        while loginStatus == False:  # Reattempt login
            loginAttempt(USERNAME, PASSWORD)
            loginStatus = checkValidLogin("div.validation-summary-errors")
        
        print("Re-logged in successfully.")
        browser.get("https://ismis.usc.edu.ph/advisedcourse")

        # After login, check if the site has crashed
        homepageCrash = checkSiteCrash("header_profile_pic")
        if homepageCrash:
            print("Site crashed after re-login. Refreshing...")
            browser.refresh()
            time.sleep(5)
            continue

    print("Session active. Monitoring...")
    time.sleep(30)  # Adjust the delay to check periodically
    
    # If everything is okay (no crash, session active), break the loop
    print("Website is stable and session is active. Exiting monitoring loop.")
    break  # Exit the loop if the site is not crashing and the session is active

# Keep the browser open after navigation
input("Press Enter to exit and close the browser.")
browser.quit()

