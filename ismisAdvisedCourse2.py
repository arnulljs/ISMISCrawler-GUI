from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import getpass
import os

# Configurations
options = Options()
options.headless = False  # Runs browser visibly
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


def wait_for_element(by, identifier, timeout=5):
    """Waits for an element to be present."""
    return WebDriverWait(browser, timeout).until(EC.presence_of_element_located((by, identifier)))


def check_site_crash_login_page():
    """Checks if the login page is fully loaded by looking for the login button."""
    try:
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn")))
        return False  # No crash, button found
    except TimeoutException:
        print("Login page not loaded properly. Refreshing...")
        return True  # Crash detected


def check_site_crash_after_login():
    """Checks if the homepage is properly loaded by looking for the profile picture."""
    try:
        WebDriverWait(browser, 5).until(EC.presence_of_element_located((By.ID, "header_profile_pic")))
        return False  # No crash, profile picture found
    except TimeoutException:
        print("Homepage not loaded properly. Refreshing...")
        return True  # Crash detected


def login_attempt(username_input, password_input):
    """Attempts to log into the ISMIS website with retry logic for connection timeouts."""
    while True:
        try:
            print("Attempting to load ISMIS website...")
            browser.get("https://ismis.usc.edu.ph")

            # Wait for the login button to appear
            while check_site_crash_login_page():
                print("Page load failed or incomplete. Refreshing...")
                browser.refresh()
                time.sleep(5)

            # Locate username, password fields, and login button
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
            break  # Exit loop if login attempt proceeds

        except WebDriverException as e:
            if "ERR_CONNECTION_TIMED_OUT" in str(e):
                print("Connection timed out. Retrying...")
            else:
                print(f"An unexpected WebDriver error occurred: {e}")
            time.sleep(5)  # Wait briefly before retrying

def navigate_to_page_with_retry(url, element_selector):
    """Navigates to a given URL with retry logic for connection timeouts and missing elements."""
    while True:
        try:
            print(f"Navigating to {url}...")
            browser.get(url)

            # Wait for the specified element to appear on the page
            WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, element_selector)))
            print("Page loaded successfully.")
            break

        except TimeoutException:
            print("Page load timeout or element not found. Retrying...")
            time.sleep(5)

        except WebDriverException as e:
            if "ERR_CONNECTION_TIMED_OUT" in str(e):
                print("Connection timed out. Retrying...")
            else:
                print(f"An unexpected WebDriver error occurred: {e}")
            time.sleep(5)

def check_valid_login():
    """Checks if the login is successful."""
    try:
        WebDriverWait(browser, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.validation-summary-errors"))
        )
        print("Wrong username/password. Please try again.")
        return False
    except TimeoutException:
        return True


def press_block_advising():
    """Presses the Block Advising button, handles modal issues for 'undefined' or stuck states, and retries indefinitely."""
    while True:
        try:
            # Click the Block Advising button
            block_advising_button = wait_for_element(By.CSS_SELECTOR, "a.btn.btn-sm.green.rs-modal[title='Click to see block section list']")
            block_advising_button.click()
            print("Block Advising button clicked successfully.")

            # Wait for the Block Section List to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "BlockSectionBody"))
            )
            print("Block Section List loaded successfully.")

            # Fetch block titles and href attributes
            block_sections = browser.find_elements(By.CSS_SELECTOR, "#BlockSectionBody h4")
            for block_section in block_sections:
                # Extract block title and link
                title = block_section.text.strip()
                link_element = block_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                link = link_element.get_attribute("href")
                
                print(f"Block Title: {title}")
                print(f"Link: {link}")

            # Break the loop after successful execution
            break

        except TimeoutException:
            print("Error: Block Section List did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")

        time.sleep(2)  # Brief delay before retrying


def press_view_lacking():
    """Presses the View Lacking button."""
    try:
        view_lacking_button = wait_for_element(By.CSS_SELECTOR, "a.btn.btn-sm.green.rs-modal[title='Click To Show Lacking Courses.']")
        view_lacking_button.click()
        print("View Lacking button clicked successfully.")
        
        # Wait for the View Lacking List to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.portlet-title > h3"))
            )
        print("View Lacking List loaded successfully.")
    except TimeoutException:
        print("Error: View Lacking button not found.")


def press_advised_course():
    """Presses the Advised Course button, handles modal issues for 'undefined' or stuck states, and retries indefinitely."""
    while True:
        try:
            # Click the Advised Course button
            advised_course_button = wait_for_element(By.CSS_SELECTOR, "a.btn.btn-sm.green.rs-modal[title='Click To Show Courses']")
            advised_course_button.click()
            print("Advised Course button clicked successfully.")

            # Wait for the page or content to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "ChooseToAdviseBody")) 
            )
            print("Advised Course content loaded successfully.")

            # Break the loop after successful execution
            break

        except TimeoutException:
            print("Error: Advised Course content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")

        time.sleep(2)  # Brief delay before retrying
        
def press_GE_FEL2():
    """Presses the GE_FEL2 button, handles modal issues for 'undefined' or stuck states, and retries indefinitely."""
    while True:
        try:
            # Click the GE_FEL 2 button
            GE_FEL2_course_button = wait_for_element(By.CSS_SELECTOR, "a.green.rs-modal[title*='GE-FREELEC 2']")
            GE_FEL2_course_button.click()
            print("GE FEL2 Course button clicked successfully.")

            # Wait for the page or content to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "ToBeAdviseBody")) 
            )
            print("GE-FEL 2 Course content loaded successfully.")

            # Break the loop after successful execution
            break

        except TimeoutException:
            print("Error: GE-FEL 2 Course content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")

        time.sleep(2)  # Brief delay before retrying        

def press_GE_FEL3():
    """Presses the GE_FEL3 button, handles modal issues for 'undefined' or stuck states, and retries indefinitely."""
    while True:
        try:
            # Click the GE_FEL 3 button
            GE_FEL3_course_button = wait_for_element(By.CSS_SELECTOR, "a.green.rs-modal[title*='GE-FREELEC 3']")
            GE_FEL3_course_button.click()
            print("GE FEL3 Course button clicked successfully.")

            # Wait for the page or content to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "ToBeAdviseBody")) 
            )
            print("GE-FEL 3 Course content loaded successfully.")

            # Break the loop after successful execution
            break

        except TimeoutException:
            print("Error: GE-FEL 3 Course content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")

        time.sleep(2)  # Brief delay before retrying     

def advise_ge_fel_course(timeout=10):
    """
    Continuously tries to press a GE-FEL button until the modal with "Successfully advised course" appears.
    Handles:
      - Success
      - Already advised
      - Schedule not available
      - Maximum units reached
    Stops asking after a successful advise, already advised, or max units reached.
    """

    ge_fel_courses = [
        ("ESUR", "EUREKA! STIR YOUR IMAGINATION"),
        ("TPDD", "THANATOLOGY (PHILOSOPHY OF DYING AND DEATH)"),
        ("US", "URBAN SKETCHING"),
        ("ITCCD", "INDIGENOUS TRADITIONAL CREATIVE CRAFTS AND DESIGN"),
        ("EL", "EDIBLE LANDSCAPING"),
        ("OMDL", "OPERATIONS MANAGEMENT IN DAILY LIFE"),
        ("ISE", "INTRODUCTION TO SOCIAL ENTREPRENEURSHIP"),
        ("LSC", "LIVING SUSTAINABILITY IN CEBU"),
        ("CCC", "COPING WITH CLIMATE CHANGE"),
        ("EO", "EXPLORING THE OCEANS"),
        ("HLT", "HEALTHY LIVING IN THE TROPICS"),
    ]

    while True:
        print("Select the GE-FEL course to advise:")
        for idx, (code, title) in enumerate(ge_fel_courses, start=1):
            print(f"{idx}. GE-FEL {code} - {title}")

        try:
            choice = int(input("Enter the number corresponding to the GE-FEL course: "))
            if choice < 1 or choice > len(ge_fel_courses):
                raise ValueError("Invalid selection.")
            selected_course, course_title = ge_fel_courses[choice - 1]
        except ValueError as e:
            print(f"Error: {e}. Please restart and choose a valid option.")
            return

        button_selector = f"a.green.rs-modal[title*='Click to advise course GE-FEL {selected_course}']"

        while True:
            try:
                button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
                button.click()
                print(f"Attempting to advise course: GE-FEL {selected_course} - {course_title}...")

                success_modal = wait_for_element(By.CSS_SELECTOR, "#modal2Body", timeout)
                modal_text = success_modal.text
                if "Successfully advised course" in modal_text:
                    print(f"Successfully advised course: GE-FEL {selected_course} - {course_title}.")
                    try:
                        modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                    except Exception:
                        pass
                    return
                if "Course already been advised!" in modal_text:
                    print(f"Course already been advised!")
                    try:
                        modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                    except Exception:
                        pass
                    return
                if "Student has reached the maximum number of units allowed for the term." in modal_text:
                    print("Maximum units reached for the term. Ending advise for GE-FEL course.")
                    try:
                        modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                    except Exception:
                        pass
                    return
                if "Cannot advise course equivalent due to course schedule not available" in modal_text:
                    print("Cannot advise course: schedule not available. Please select another GE-FEL course.")
                    try:
                        modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                    except Exception:
                        pass
                    break  # Break inner loop, re-prompt user
            except TimeoutException:
                try:
                    modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                    if modal.is_displayed():
                        modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                        if "Successfully advised course" in modal_body:
                            print(f"Successfully advised course: GE-FEL {selected_course} - {course_title}. (Timeout branch)")
                            try:
                                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                                close_btn.click()
                            except Exception:
                                pass
                            return
                        if "Course already been advised!" in modal_body:
                            print(f"Course already been advised! (Timeout branch)")
                            try:
                                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                                close_btn.click()
                            except Exception:
                                pass
                            return
                        if "Student has reached the maximum number of units allowed for the term." in modal_body:
                            print("Maximum units reached for the term. (Timeout branch)")
                            try:
                                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                                close_btn.click()
                            except Exception:
                                pass
                            return
                        if "Cannot advise course equivalent due to course schedule not available" in modal_body:
                            print("Cannot advise course: schedule not available. Please select another GE-FEL course. (Timeout branch)")
                            try:
                                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                                close_btn.click()
                            except Exception:
                                pass
                            break
                except Exception:
                    pass
                print("Error: Free Elective Course content did not load properly. Retrying...")
            except WebDriverException as e:
                try:
                    modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                    if modal.is_displayed():
                        modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                        if "undefined" in modal_body:
                            print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                            print("Modal closed due to 'undefined'. Retrying immediately...")
                            continue
                        if "... i'm still processing your request :)" in modal_body:
                            print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                            time.sleep(10)
                            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                            print("Modal closed after 10-second wait. Retrying...")
                            continue
                        if "... loading ..." in modal_body:
                            print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                            time.sleep(20)
                            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                            print("Modal closed after 20-second wait. Retrying...")
                            continue
                except Exception as modal_error:
                    print(f"Error while handling modal: {modal_error}")
            time.sleep(2)
        # If we reach here, it means the course could not be advised due to schedule not available, so re-prompt

def schedule_ge_fel_course(timeout=10):
    """
    Prints all available schedule details for a selected GE-FEL course, with robust modal and retry logic.
    Checks if the course is in the advised list before attempting to view schedule.
    """
    ge_fel_courses = [
        ("ESUR", "EUREKA! STIR YOUR IMAGINATION"),
        ("TPDD", "THANATOLOGY (PHILOSOPHY OF DYING AND DEATH)"),
        ("US", "URBAN SKETCHING"),
        ("ITCCD", "INDIGENOUS TRADITIONAL CREATIVE CRAFTS AND DESIGN"),
        ("EL", "EDIBLE LANDSCAPING"),
        ("OMDL", "OPERATIONS MANAGEMENT IN DAILY LIFE"),
        ("ISE", "INTRODUCTION TO SOCIAL ENTREPRENEURSHIP"),
        ("LSC", "LIVING SUSTAINABILITY IN CEBU"),
        ("CCC", "COPING WITH CLIMATE CHANGE"),
        ("EO", "EXPLORING THE OCEANS"),
        ("HLT", "HEALTHY LIVING IN THE TROPICS"),
    ]

    print("Select the GE-FEL course to see Schedule:")
    for idx, (code, title) in enumerate(ge_fel_courses, start=1):
        print(f"{idx}. GE-FEL {code} - {title}")

    try:
        choice = int(input("Enter the number corresponding to the GE-FEL course: "))
        if choice < 1 or choice > len(ge_fel_courses):
            raise ValueError("Invalid selection.")
        selected_course, course_title = ge_fel_courses[choice - 1]
    except ValueError as e:
        print(f"Error: {e}. Please restart and choose a valid option.")
        return

    # Check if the course is in the advised course list
    advised_courses = browser.find_elements(By.CSS_SELECTOR, "#AdvisedCourseList tr")
    found = False
    for row in advised_courses:
        try:
            code = row.find_element(By.CSS_SELECTOR, "td").text.strip()
            if code.endswith(f"GE-FEL {selected_course}"):
                found = True
                break
        except Exception:
            continue
    if not found:
        print(f"GE-FEL {selected_course} is not in the advised course list. Skipping schedule view.")
        return

    button_selector = f"a.green.rs-modal[title*='Click to view schedule  GE-FEL {selected_course}']"
    try:
        button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
    except TimeoutException:
        print(f"No 'Click to view schedule' button found for GE-FEL {selected_course}. Skipping.")
        return
    while True:
        try:
            button.click()
            print(f"Attempting to view schedule: GE-FEL {selected_course} - {course_title}")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody tr")
            if not schedule_sections:
                print(f"No schedule details found for GE-FEL {selected_course}.")
                ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                break
            for schedule_section in schedule_sections:
                try:
                    block_number = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                    course_code = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    schedule_details = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                    course_status = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                    population = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
                    link_element = schedule_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                    link = link_element.get_attribute("href")
                    print(f"Block #: {block_number}")
                    print(f"Course Code: {course_code}")
                    print(f"Schedule: {schedule_details}")
                    print(f"Course Status: {course_status}")
                    print(f"Population: {population}")
                    print(f"Link: {link}")
                    print("-" * 40)
                except Exception:
                    print("A schedule row was missing expected details and was skipped.")
            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
            break
        except TimeoutException:
            print("Error: GE-FEL Schedule content did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def advise_CPE_2301(timeout=10):
    """
    Presses the plus button for CPE 2301 and then presses the 'Click to advise course' button, handling modal errors and retrying as needed.
    Handles 'Course already been advised!' and pre-requisite errors as a success state.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2301']"
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2301']"
    # Step 1: Press the plus button to open the modal
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2301.")
            break
        except TimeoutException:
            print("Error: CPE 2301 show button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)
    # Step 2: Press the 'Click to advise course' button
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            advise_button.click()
            print("Pressed 'Click to advise course' for CPE 2301.")
            # Check for success, already advised, max units, or pre-req error
            success_modal = wait_for_element(By.CSS_SELECTOR, "#modal2Body", timeout)
            modal_text = success_modal.text
            if "Successfully advised course." in modal_text:
                print("Successfully advised course for CPE 2301.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after success
            if "Course already been advised!" in modal_text:
                print("Course already been advised for CPE 2301.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after already advised
            if "Student has reached the maximum number of units allowed for the term." in modal_text:
                print("Maximum units reached for the term. Ending advise for CPE 2301.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after max units
            if "Student has not taken or passed the pre-requisite courses of" in modal_text:
                print("Pre-requisite courses not taken or passed for CPE 2301.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after pre-req error
        except TimeoutException:
            # Check if modal is already showing success, already advised, max units, or pre-req error
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "Successfully advised course." in modal_body:
                        print("Successfully advised course for CPE 2301. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Course already been advised!" in modal_body:
                        print("Course already been advised for CPE 2301. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has reached the maximum number of units allowed for the term." in modal_body:
                        print("Maximum units reached for the term. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has not taken or passed the pre-requisite courses of" in modal_body:
                        print("Pre-requisite courses not taken or passed for CPE 2301. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
            except Exception:
                pass
            print("Error: CPE 2301 advise button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def advise_CPE_2302(timeout=10):
    """
    Presses the plus button for CPE 2302 and then presses the 'Click to advise course' button, handling modal errors and retrying as needed.
    Handles 'Course already been advised!' and pre-requisite errors as a success state.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2302']"
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2302']"
    # Step 1: Press the plus button to open the modal
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2302.")
            break
        except TimeoutException:
            print("Error: CPE 2302 show button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)
    # Step 2: Press the 'Click to advise course' button
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            advise_button.click()
            print("Pressed 'Click to advise course' for CPE 2302.")
            # Check for success, already advised, max units, or pre-req error
            success_modal = wait_for_element(By.CSS_SELECTOR, "#modal2Body", timeout)
            modal_text = success_modal.text
            if "Successfully advised course." in modal_text:
                print("Successfully advised course for CPE 2302.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after success
            if "Course already been advised!" in modal_text:
                print("Course already been advised for CPE 2302.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after already advised
            if "Student has reached the maximum number of units allowed for the term." in modal_text:
                print("Maximum units reached for the term. Ending advise for CPE 2302.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after max units
            if "Student has not taken or passed the pre-requisite courses of" in modal_text:
                print("Pre-requisite courses not taken or passed for CPE 2302.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after pre-req error
        except TimeoutException:
            # Check if modal is already showing success, already advised, max units, or pre-req error
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "Successfully advised course." in modal_body:
                        print("Successfully advised course for CPE 2302. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Course already been advised!" in modal_body:
                        print("Course already been advised for CPE 2302. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has reached the maximum number of units allowed for the term." in modal_body:
                        print("Maximum units reached for the term. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has not taken or passed the pre-requisite courses of" in modal_body:
                        print("Pre-requisite courses not taken or passed for CPE 2302. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
            except Exception:
                pass
            print("Error: CPE 2302 advise button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def advise_CPE_2303L(timeout=10):
    """
    Presses the plus button for CPE 2303L and then presses the 'Click to advise course' button, handling modal errors and retrying as needed.
    Handles 'Course already been advised!' and pre-requisite errors as a success state.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2303L']"
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2303L']"
    # Step 1: Press the plus button to open the modal
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2303L.")
            break
        except TimeoutException:
            print("Error: CPE 2303L show button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)
    # Step 2: Press the 'Click to advise course' button
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            advise_button.click()
            print("Pressed 'Click to advise course' for CPE 2303L.")
            # Check for success, already advised, max units, or pre-req error
            success_modal = wait_for_element(By.CSS_SELECTOR, "#modal2Body", timeout)
            modal_text = success_modal.text
            if "Successfully advised course." in modal_text:
                print("Successfully advised course for CPE 2303L.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after success
            if "Course already been advised!" in modal_text:
                print("Course already been advised for CPE 2303L.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after already advised
            if "Student has reached the maximum number of units allowed for the term." in modal_text:
                print("Maximum units reached for the term. Ending advise for CPE 2303L.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after max units
            if "Student has not taken or passed the pre-requisite courses of" in modal_text:
                print("Pre-requisite courses not taken or passed for CPE 2303L.")
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                close_btn.click()
                return  # Exit the function after pre-req error
        except TimeoutException:
            # Check if modal is already showing success, already advised, max units, or pre-req error
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "Successfully advised course." in modal_body:
                        print("Successfully advised course for CPE 2303L. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Course already been advised!" in modal_body:
                        print("Course already been advised for CPE 2303L. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has reached the maximum number of units allowed for the term." in modal_body:
                        print("Maximum units reached for the term. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
                    if "Student has not taken or passed the pre-requisite courses of" in modal_body:
                        print("Pre-requisite courses not taken or passed for CPE 2303L. (Timeout branch)")
                        close_btn = modal.find_element(By.CSS_SELECTOR, "button.close[data-dismiss='modal']")
                        close_btn.click()
                        return
            except Exception:
                pass
            print("Error: CPE 2303L advise button did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal2")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal2Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def schedule_CPES(timeout=10):
    """
    This is after you have advised the course this is same as schedule_ge_fel_course but this is for individual subjects. It gives the links for the schedules.

    Args:
        timeout: Timeout in seconds for waiting for elements (default: 10 seconds).

    Returns:
        None
    """
    #Click to view schedule  GE-FEL TPDD
    # Construct the CSS selector
    button_selector = f"a.green.rs-modal[title*='Click to view schedule  CPES 2201']" # make this user inputtable soon?

    # Retry logic to click the button and wait for the success message
    while True:
        try:
            # Wait for and click the selected GE-FEL button
            button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
            button.click()
            print(f"Attempting to advise course: CPES 2201")

            # Check if the modal contains the success message
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            
            #Fetch the schedule and href attributes
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody tr")
            for schedule_section in schedule_sections:
                # Extract the block number
                block_number = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
        
                # Extract the course code
                course_code = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
        
                # Extract the schedule details
                schedule_details = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
        
                # Extract the course status
                course_status = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
        
                # Extract the population
                population = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
        
                # Extract the link
                link_element = schedule_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                link = link_element.get_attribute("href")
        
                # Print the details
                print(f"Block #: {block_number}")
                print(f"Course Code: {course_code}")
                print(f"Schedule: {schedule_details}")
                print(f"Course Status: {course_status}")
                print(f"Population: {population}")
                print(f"Link: {link}")
                print("-" * 40)
            break
        except TimeoutException:
            print("Error: CPES Schedule content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")

        time.sleep(2)  # Brief delay before retrying            

def schedule_CPE_2301(timeout=10):
    """
    Prints all available schedule details for CPE 2301, with robust modal and retry logic.
    Checks if the course is in the advised list before attempting to view schedule.
    """
    # First, check if CPE 2301 is in the advised course list
    advised_courses = browser.find_elements(By.CSS_SELECTOR, "#AdvisedCourseList tr")
    found = False
    for row in advised_courses:
        try:
            code = row.find_element(By.CSS_SELECTOR, "td").text.strip()
            if code.endswith("CPE 2301"):
                found = True
                break
        except Exception:
            continue
    if not found:
        print("CPE 2301 is not in the advised course list. Skipping schedule view.")
        return
    button_selector = f"a.green.rs-modal[title*='Click to view schedule  CPE 2301']"
    try:
        button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
    except TimeoutException:
        print("No 'Click to view schedule' button found for CPE 2301. Skipping.")
        return
    while True:
        try:
            button.click()
            print(f"Attempting to view schedule: CPE 2301")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody tr")
            if not schedule_sections:
                print("No schedule details found for CPE 2301.")
                ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                break
            for schedule_section in schedule_sections:
                try:
                    block_number = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                    course_code = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    schedule_details = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                    course_status = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                    population = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
                    link_element = schedule_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                    link = link_element.get_attribute("href")
                    print(f"Block #: {block_number}")
                    print(f"Course Code: {course_code}")
                    print(f"Schedule: {schedule_details}")
                    print(f"Course Status: {course_status}")
                    print(f"Population: {population}")
                    print(f"Link: {link}")
                    print("-" * 40)
                except Exception:
                    print("A schedule row was missing expected details and was skipped.")
            # Escape/close modal after printing all
            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
            break
        except TimeoutException:
            print("Error: CPE 2301 Schedule content did not load properly. Retrying...")
        except WebDriverException as e:
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    if "undefined" in modal_body:
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    if "... i'm still processing your request :)" in modal_body:
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    if "... loading ..." in modal_body:
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def schedule_CPE_2302(timeout=10):
    """
    Prints all available schedule details for CPE 2302, with robust modal and retry logic.
    Checks if the course is in the advised list before attempting to view schedule.
    """
    advised_courses = browser.find_elements(By.CSS_SELECTOR, "#AdvisedCourseList tr")
    found = False
    for row in advised_courses:
        try:
            code = row.find_element(By.CSS_SELECTOR, "td").text.strip()
            if code.endswith("CPE 2302"):
                found = True
                break
        except Exception:
            continue
    if not found:
        print("CPE 2302 is not in the advised course list. Skipping schedule view.")
        return
    button_selector = f"a.green.rs-modal[title*='Click to view schedule  CPE 2302']"
    while True:
        try:
            button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
            button.click()
            print(f"Attempting to view schedule: CPE 2302")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody tr")
            if not schedule_sections:
                print("No schedule details found for CPE 2302.")
                ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                break
            for schedule_section in schedule_sections:
                try:
                    block_number = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                    course_code = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    schedule_details = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                    course_status = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                    population = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
                    link_element = schedule_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                    link = link_element.get_attribute("href")
                    print(f"Block #: {block_number}")
                    print(f"Course Code: {course_code}")
                    print(f"Schedule: {schedule_details}")
                    print(f"Course Status: {course_status}")
                    print(f"Population: {population}")
                    print(f"Link: {link}")
                    print("-" * 40)
                except Exception:
                    print("A schedule row was missing expected details and was skipped.")
            # Escape/close modal after printing all
            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
            break
        except TimeoutException:
            print("Error: CPE 2302 Schedule content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def schedule_CPE_2303L(timeout=10):
    """
    Prints all available schedule details for CPE 2303L, with robust modal and retry logic.
    Checks if the course is in the advised list before attempting to view schedule.
    """
    advised_courses = browser.find_elements(By.CSS_SELECTOR, "#AdvisedCourseList tr")
    found = False
    for row in advised_courses:
        try:
            code = row.find_element(By.CSS_SELECTOR, "td").text.strip()
            if code.endswith("CPE 2303L"):
                found = True
                break
        except Exception:
            continue
    if not found:
        print("CPE 2303L is not in the advised course list. Skipping schedule view.")
        return
    button_selector = f"a.green.rs-modal[title*='Click to view schedule  CPE 2303L']"
    while True:
        try:
            button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
            button.click()
            print(f"Attempting to view schedule: CPE 2303L")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody tr")
            if not schedule_sections:
                print("No schedule details found for CPE 2303L.")
                ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                break
            for schedule_section in schedule_sections:
                try:
                    block_number = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(1)").text.strip()
                    course_code = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(2)").text.strip()
                    schedule_details = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(3) span").text.strip()
                    course_status = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(4)").text.strip()
                    population = schedule_section.find_element(By.CSS_SELECTOR, "td:nth-child(5)").text.strip()
                    link_element = schedule_section.find_element(By.CSS_SELECTOR, "a.green.rs-modal")
                    link = link_element.get_attribute("href")
                    print(f"Block #: {block_number}")
                    print(f"Course Code: {course_code}")
                    print(f"Schedule: {schedule_details}")
                    print(f"Course Status: {course_status}")
                    print(f"Population: {population}")
                    print(f"Link: {link}")
                    print("-" * 40)
                except Exception:
                    print("A schedule row was missing expected details and was skipped.")
            # Escape/close modal after printing all
            ActionChains(browser).send_keys(Keys.ESCAPE).perform()
            break
        except TimeoutException:
            print("Error: CPE 2303L Schedule content did not load properly. Retrying...")

        except WebDriverException as e:
            # Handle potential modal issues
            try:
                modal = browser.find_element(By.CSS_SELECTOR, "#modal1")
                if modal.is_displayed():
                    modal_body = modal.find_element(By.CSS_SELECTOR, "#modal1Body").text.strip()
                    
                    if "undefined" in modal_body:
                        # Close modal immediately for "undefined"
                        print(f"Modal issue detected: {modal_body}. Closing modal and retrying...")
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed due to 'undefined'. Retrying immediately...")
                        continue
                    
                    if "... i'm still processing your request :)" in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is processing: {modal_body}. Waiting 10 seconds before retrying...")
                        time.sleep(10)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 10-second wait. Retrying...")
                        continue
                    
                    if "... loading ..." in modal_body:
                        # Wait 10 seconds before retrying for "still processing"
                        print(f"Modal is loading: {modal_body}. Waiting 20 seconds before retrying...")
                        time.sleep(20)
                        ActionChains(browser).send_keys(Keys.ESCAPE).perform()
                        print("Modal closed after 20-second wait. Retrying...")
                        continue
            except Exception as modal_error:
                print(f"Error while handling modal: {modal_error}")
        time.sleep(2)

def close_remaining_courses_modal(timeout=10):
    """
    Closes the 'Remaining Courses To Be Advised' modal (#modal1) by clicking its close button.
    """
    try:
        # Wait for the modal to be present and visible
        modal = WebDriverWait(browser, timeout).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#modal1"))
        )
        # Find the close button inside the modal header
        close_btn = modal.find_element(By.CSS_SELECTOR, "div.tools > a.remove[data-dismiss='modal']")
        close_btn.click()
        print("Closed 'Remaining Courses To Be Advised' modal.")
    except Exception as e:
        print(f"Could not close 'Remaining Courses To Be Advised' modal: {e}")
        
def navigate_to_block_advising():
    """Navigates to the Block Advising section."""
    browser.get("https://ismis.usc.edu.ph/advisedcourse")

    # Ensure the page is loaded
    while check_site_crash_after_login():
        browser.refresh()
        time.sleep(5)

    # Click the Block Advising button
    press_block_advising()

def navigate_to_view_lacking():
    """Navigates to the View Lacking section."""
    browser.get("https://ismis.usc.edu.ph/advisedcourse")

    # Ensure the page is loaded
    while check_site_crash_after_login():
        browser.refresh()
        time.sleep(5)

    # Click the Block Advising button
    #press_view_lacking()

    
def navigate_to_advise_course():
    """Navigates to the Advised Course section and verifies it has loaded properly."""
    navigate_to_page_with_retry("https://ismis.usc.edu.ph/advisedcourse", "a.btn.btn-sm.green.rs-modal[title='Click To Show Courses']")
    press_advised_course()


def main():
    """Main function to control the flow of the program."""
    clear()
    print("Welcome to ISMIS Crawler!\n")
    print("Delivering your information without the hassle.")
    time.sleep(1)
    print("Loading...")

    # Load credentials from a file
    username_input, password_input = load_credentials()

    # Login process
    login_status = False
    while not login_status:
        #clear()
        login_attempt(username_input, password_input)
        login_status = check_valid_login()

    print("Logged in successfully.")

    # Continuously monitor post-login page for crashes
    while check_site_crash_after_login():
        browser.refresh()
        time.sleep(5)

    # Demonstrate button interactions
    #print("Navigating to Block Advising...")
    #time.sleep(10)
    #navigate_to_block_advising() this is for block enrollment which allows u to get the links to the scheds of the blocks you want.
    #you do still need to get the complete link when u press enroll block section which means either you need to refresh or run this script again whichever is easier.

    #print("Navigating to View Lacking...")
    #navigate_to_view_lacking() this is for view lacking if you want to for some reason.

    #this block of code is for advising courses for non block. you can edit the functions to do the individual courses you want to advise.
    # then print their schedules and href link which leads to faster requests to the server since its what you press instead of clicking add.
    
    # print("Navigating to Advised Course...")
    # navigate_to_advise_course()

    # advise_CPE_2301()
    # time.sleep(2)  # Wait for the modal to load properly
    # advise_CPE_2302()
    # time.sleep(2)  # Wait for the modal to load properly
    # advise_CPE_2303L
    
    # close_remaining_courses_modal()
    
    # schedule_CPE_2301()
    # schedule_CPE_2302()
    # schedule_CPE_2303L()
    
    # this block of code is for enrolling in GE-FEL courses which is not needed for now.
    print("Navigating to Advised Course...")
    navigate_to_advise_course()
    print("Navigating to GE-FEL 2...")
    press_GE_FEL2()
    print("Pressing GE-FEL AYG...")
    advise_ge_fel_course() #the advise ge fel course is a bit broken though due to it not being able to handle success properly yet. will fix soon
    time.sleep(2)  # Wait for the modal to load properly
    close_remaining_courses_modal()
    schedule_ge_fel_course() 
    
    #schedule_CPES() initial test to see schedule of a certain course. hte schedule cpe is much better i think
    
    
    
    print("DONE!")
    # Keep the browser open after navigation
    input("Press Enter to exit and close the browser.")
    browser.quit()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        browser.quit()

