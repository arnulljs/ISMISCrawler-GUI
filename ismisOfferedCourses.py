from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
import time
import getpass
import os

# Configurations
options = Options()
options.headless = False  # Runs Chromium browser visibly
options.add_experimental_option("excludeSwitches", ["enable-logging"])  # Disables DevTools logs
ser = Service("./chromedriver.exe")
browser = webdriver.Chrome(service=ser, options=options)

clear = lambda: os.system('cls' if os.name == 'nt' else 'clear')  # Clears terminal

# Functions
def load_credentials(file_path="credentials.txt"):
    """Loads credentials from a file."""
    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
            username = lines[0].strip()
            password = lines[1].strip()
            return username, password
    except FileNotFoundError:
        print("Credentials file not found. Creating a new one...")
        username = input("Enter your username: ")
        password = getpass.getpass("Enter your password: ")
        with open(file_path, "w") as file:
            file.write(f"{username}\n{password}")
        return username, password

def wait_for_element(by, identifier, timeout=5, max_retries=10):
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

def check_site_crash_login_page():
    """Checks if the login page is fully loaded by looking for the login button."""
    try:
        WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn")))
        return False  # No crash, button found
    except TimeoutException:
        print("Login page not loaded properly. Refreshing...")
        return True  # Crash detected

def check_site_crash_homepage():
    """Checks if the homepage is properly loaded by looking for the header profile picture."""
    try:
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "header_profile_pic"))
        )
        return False  # No crash, profile picture found
    except TimeoutException:
        print("Homepage not loaded properly. Refreshing...")
        return True  # Crash detected

def login_attempt(username_input, password_input, max_retries=5):
    """Attempts to log into the ISMIS website with retries."""
    retries = 0
    while retries < max_retries:
        try:
            browser.get("https://ismis.usc.edu.ph")

            # Ensure the login page is loaded properly
            while check_site_crash_login_page():
                browser.refresh()
                time.sleep(5)

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

def navigate_to_courses():
    """Navigate to the course schedule page and interact with the course filter."""
    try:
        browser.get("https://ismis.usc.edu.ph/courseSchedule/CourseScheduleOfferedIndex")

        # Wait for the filter button and click it
        filter_button = wait_for_element(By.CSS_SELECTOR, "a.rs-ajax.green")
        filter_button.click()

        # Wait for the filter modal to appear
        wait_for_element(By.ID, "OfferedCourseFilter")

        # Fill the course code, academic period, and academic year fields
        course_input = wait_for_element(By.ID, "Courses")
        academic_period_select = wait_for_element(By.ID, "AcademicPeriod")
        academic_year_select = wait_for_element(By.ID, "AcademicYear")

        # Fill in values (you can replace these with dynamic input or defaults)
        course_input.send_keys("GE-FEL")  # Example course code
        academic_period_select.send_keys("2ND SEMESTER")
        academic_year_select.send_keys("2024")

        # Find the submit button and click it
        submit_button = wait_for_element(By.CSS_SELECTOR, "div.form-actions button[type='submit']")
        submit_button.click()

    except Exception as e:
        print(f"Error interacting with course filter: {e}")

def print_course_data():
    """Extract and print course details including the header in the desired format."""
    try:
        # Print the table header
        print("""
<thead>
    <tr>
        <th>CourseCode</th>
        <th>Course Description</th>
        <th>Course Status</th>
        <th>Teacher/s</th>
        <th>Schedule</th>
        <th>Department Reserved</th>
        <th>Enrolled Students</th>
    </tr>
</thead>
        """)

        # Wait for the course rows to load
        rows = WebDriverWait(browser, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr"))
        )
        
        for row in rows:
            try:
                # Extract course details
                course_name = row.find_element(By.XPATH, ".//td[1]").text.strip()
                course_title = row.find_element(By.XPATH, ".//td[2]").text.strip()
                section = row.find_element(By.XPATH, ".//td[3]").text.strip()
                schedule = row.find_element(By.XPATH, ".//td[5]").text.strip()
                department = row.find_element(By.XPATH, ".//td[6]").text.strip()
                enrolled = row.find_element(By.XPATH, ".//td[7]").text.strip()

                # Print the course details in the desired format
                print(f"""
<tr class=" " title="created by: [ID] last [DATE], updated by: [ID] last [DATE]">
    <td>{course_name}</td>
    <td>{course_title}</td>
    <td>{section}</td>
    <td></td>
    <td>
        <span>{schedule}</span><br>
    </td>
    <td>
        {department}<span>&nbsp;</span> <span>(40)</span> <br>
    </td>
    <td>{enrolled}</td>
</tr>
                """)
            except NoSuchElementException:
                # If any course data is missing, we skip it
                continue
    except Exception as e:
        print(f"Error extracting or printing course data: {e}")

def main():
    """Main function to control the flow of the program."""
    clear()

    print("Welcome to blurridge's ISMIS Crawler!\n")
    print("Accessing course schedule data...")
    time.sleep(1)
    print("Loading...")

    login_status = False

    # Load credentials from a file
    username_input, password_input = load_credentials()

    # Login process
    while not login_status:
        clear()
        login_status = login_attempt(username_input, password_input)
        if login_status:
            login_status = check_valid_login()

    print("Entering homepage...")

    # Handle homepage crashes
    while check_site_crash_homepage():
        print("Site crashed. Refreshing homepage...")
        browser.refresh()
        time.sleep(5)

    navigate_to_courses()

    # Extract and print course data
    print_course_data()

    print("DONE!")
    browser.quit()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        browser.quit()
