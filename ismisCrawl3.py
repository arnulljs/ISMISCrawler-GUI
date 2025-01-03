from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time
import os

# Configurations
options = Options()
options.headless = False  # Runs Chromium browser without being visible
options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Disables DevTools logs on terminal
ser = Service(r"C:\\Users\\Chrys Sean Sevilla\\Documents\\ISMISCrawler\\chromedriver.exe")
browser = webdriver.Chrome(service=ser, options=options)

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')  # Clears terminal

# Functions
def load_credentials(filename="credentials.txt"):
    """Loads username and password from a file."""
    try:
        with open(filename, "r") as file:
            credentials = {}
            for line in file:
                key, value = line.strip().split("=")
                credentials[key.strip()] = value.strip()
            return credentials.get("username"), credentials.get("password")
    except FileNotFoundError:
        print(f"Error: {filename} not found. Please create the file and add your credentials.")
        exit()
    except ValueError:
        print(f"Error: Invalid format in {filename}. Ensure it follows 'key=value' format.")
        exit()

def wait_for_element(by, identifier, timeout=10):
    """Waits for an element to be present and returns it."""
    while True:
        try:
            return WebDriverWait(browser, timeout).until(EC.presence_of_element_located((by, identifier)))
        except TimeoutException:
            print(f"Timed out waiting for element: {identifier}. Retrying...")
            browser.refresh()
            time.sleep(5)

def login_attempt(username_input, password_input):
    """Attempts to log into the ISMIS website."""
    browser.get("https://ismis.usc.edu.ph")
    try:
        username = wait_for_element(By.ID, "Username")
        password = wait_for_element(By.ID, "Password")
        login_button = wait_for_element(By.CSS_SELECTOR, "button.btn")

        print("Entering username...")
        username.send_keys(username_input)
        time.sleep(1)
        print("Entering password...")
        password.send_keys(password_input)
        time.sleep(1)
        print(f"Attempting login for {username_input}...")
        login_button.click()

    except WebDriverException as e:
        print(f"Error during login attempt: {e}")
        return False
    return True

def check_valid_login():
    """Checks if the login is successful."""
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.validation-summary-errors"))
        )
        print("Wrong username/password. Please try again.")
        return False
    except TimeoutException:
        return True

def check_site_crash():
    """Checks if the ISMIS homepage has crashed."""
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "header_profile_pic"))
        )
    except TimeoutException:
        return True
    return False

def fetch_grades():
    """Fetches and prints the grade data."""
    try:
        browser.get("https://ismis.usc.edu.ph/ViewGrades")
        body = wait_for_element(By.TAG_NAME, "body", timeout=60)
        tables = body.find_elements(By.CLASS_NAME, "table")

        print("{:20s} {:60s} {:7s} {:4s} {:4s}".format("Course Code", "Course Name", "Units", "MG", "FG"))

        for table_index in range(len(tables)):
            course_code = tables[table_index].find_elements(By.CLASS_NAME, "col-lg-3")
            course_name = tables[table_index].find_elements(By.CLASS_NAME, "col-lg-6")
            unit_num = tables[table_index].find_elements(By.CSS_SELECTOR, "td.hidden-xs")
            grade_value = tables[table_index].find_elements(By.CSS_SELECTOR, "td.col-lg-1:not(.hidden-xs)")

            grade_index = 0
            for index in range(len(course_code)):
                print("{:20s} {:60s} {:7s} {:4s} {:4s}".format(
                    course_code[index].text, course_name[index].text, unit_num[index].text,
                    grade_value[grade_index].text, grade_value[grade_index + 1].text
                ))
                grade_index += 2
            print("\n\n")
    except TimeoutException:
        print("Error fetching grades. Please try again later.")

def main():
    """Main function to control the flow of the program."""
    clear()

    print("Welcome to blurridge's ISMIS Crawler!\n")
    print("Delivering your grades without the hassle.")
    time.sleep(1)
    print("Loading...")

    username_input, password_input = load_credentials()

    login_status = False
    homepage_crash = False

    while not login_status:
        login_status = login_attempt(username_input, password_input)
        if login_status:
            login_status = check_valid_login()

    print("Entering homepage...")
    time.sleep(5)
    homepage_crash = check_site_crash()

    while homepage_crash:
        print("Site crashed. Refreshing...")
        browser.refresh()
        time.sleep(5)
        homepage_crash = check_site_crash()

    fetch_grades()

    print("DONE!")
    browser.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        browser.quit()
