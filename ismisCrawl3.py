from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time
import os

# Configuration
options = Options()
options.headless = False  # Runs browser visibly; change to True to run headless
options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Disables DevTools logs
service = Service("./chromedriver.exe")
browser = webdriver.Chrome(service=service, options=options)

# Clear terminal function
clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')

# Functions
def wait_for_element(by, identifier, timeout=10, max_retries=5):
    """Waits for an element to be present and retries on connection or timeout errors."""
    retries = 0
    while retries < max_retries:
        try:
            return WebDriverWait(browser, timeout).until(EC.presence_of_element_located((by, identifier)))
        except TimeoutException:
            print(f"Timed out waiting for element: {identifier}. Retrying ({retries + 1}/{max_retries})...")
            retries += 1
            browser.refresh()
            time.sleep(5)
        except WebDriverException as e:
            if "ERR_CONNECTION_RESET" in str(e) or "ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Connection issue detected ({str(e)}). Retrying ({retries + 1}/{max_retries})...")
                retries += 1
                browser.refresh()
                time.sleep(5)
            else:
                raise e
    raise TimeoutException(f"Failed to find element {identifier} after {max_retries} retries.")


def get_credentials():
    """Reads credentials from a file or prompts the user if unavailable."""
    try:
        with open("credentials.txt", "r") as file:
            lines = file.readlines()
            username = lines[0].strip()
            password = lines[1].strip()
            return username, password
    except FileNotFoundError:
        print("Credentials file not found. Please create a 'credentials.txt' file with username on the first line and password on the second line.")
        exit()

def login_attempt(username_input, password_input, max_retries=5):
    """Attempts to log into the ISMIS website with retries."""
    retries = 0
    while retries < max_retries:
        try:
            browser.get("https://ismis.usc.edu.ph")
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

            return True
        except WebDriverException as e:
            if "ERR_CONNECTION_RESET" in str(e) or "ERR_CONNECTION_TIMED_OUT" in str(e):
                print(f"Connection issue detected ({str(e)}). Retrying login ({retries + 1}/{max_retries})...")
                retries += 1
                time.sleep(5)
            else:
                raise e
    raise Exception("Failed to log in after multiple retries.")

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

def fetch_grades(max_retries=5):
    """Fetches and prints the grade data with retries."""
    retries = 0
    while retries < max_retries:
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
            return
        except WebDriverException as e:
            if "ERR_CONNECTION_RESET" in str(e):
                print(f"Connection reset detected. Retrying fetch grades ({retries + 1}/{max_retries})...")
                retries += 1
                time.sleep(5)
            else:
                raise e
    raise Exception("Failed to fetch grades after multiple retries.")

def main():
    """Main function to control the flow of the program."""
    clear()

    print("Welcome to ISMIS Crawler!")
    print("Delivering your grades without the hassle.")
    time.sleep(1)
    print("Loading...")

    login_status = False
    homepage_crash = False

    while not login_status:
        username_input, password_input = get_credentials()
        clear()

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
