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
                
                #a.green.rs-modal[title*='GE-FREELEC 2']
                #title="Click to show course to be advisedGE-FREELEC 2"
                #title="Click to show course to be advisedGE-FREELEC 3"
                
                
                #ToBeAdviseBody for free elecs?
                
                #"a.green.rs-modal[title*='GE-FEL EW-AYG']") #for GE-FEL EW-AYG
                #"a.green.rs-modal[title*='GE-FEL TPDD']") #for GE-FEL TPDD
                #title="Click to advise course GE-FEL EW-AYG"
                #title="Click to advise course GE-FEL TPDD"
                
                
                #Course already been advised!
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
                
                #a.green.rs-modal[title*='GE-FREELEC 2']
                #title="Click to show course to be advisedGE-FREELEC 2"
                #title="Click to show course to be advisedGE-FREELEC 3"
                
                
                #ToBeAdviseBody for free elecs?
                
                #"a.green.rs-modal[title*='GE-FEL EW-AYG']") #for GE-FEL EW-AYG
                #"a.green.rs-modal[title*='GE-FEL TPDD']") #for GE-FEL TPDD
                #title="Click to advise course GE-FEL EW-AYG"
                #title="Click to advise course GE-FEL TPDD"
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
                
                #a.green.rs-modal[title*='GE-FREELEC 2']
                #title="Click to show course to be advisedGE-FREELEC 2"
                #title="Click to show course to be advisedGE-FREELEC 3"
                
                
                #ToBeAdviseBody for free elecs?
                
                #"a.green.rs-modal[title*='GE-FEL EW-AYG']") #for GE-FEL EW-AYG
                #"a.green.rs-modal[title*='GE-FEL TPDD']") #for GE-FEL TPDD
                #title="Click to advise course GE-FEL EW-AYG"
                #title="Click to advise course GE-FEL TPDD"
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

    Args:
        timeout: Timeout in seconds for waiting for elements (default: 10 seconds).

    Returns:
        None
    """

    # Pre-defined list of GE-FEL courses with full titles
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

    # Display the courses for the user to select
    print("Select the GE-FEL course to advise:")
    for idx, (code, title) in enumerate(ge_fel_courses, start=1):
        print(f"{idx}. GE-FEL {code} - {title}")

    # Prompt user for selection
    try:
        choice = int(input("Enter the number corresponding to the GE-FEL course: "))
        if choice < 1 or choice > len(ge_fel_courses):
            raise ValueError("Invalid selection.")
        selected_course, course_title = ge_fel_courses[choice - 1]
    except ValueError as e:
        print(f"Error: {e}. Please restart and choose a valid option.")
        return

    # Construct the CSS selector
    button_selector = f"a.green.rs-modal[title*='Click to advise course GE-FEL {selected_course}']"

    # Retry logic to click the button and wait for the success message
    while True:
        try:
            # Wait for and click the selected GE-FEL button
            button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
            button.click()
            print(f"Attempting to advise course: GE-FEL {selected_course} - {course_title}...")

            # Check if the modal contains the success message
            success_modal = wait_for_element(By.CSS_SELECTOR, "#modal2Body", timeout)
            if "Successfully advised course" in success_modal.text:
                print(f"Successfully advised course: GE-FEL {selected_course} - {course_title}.")
                break
            if "Course already been advised!" in success_modal.text:
                print(f"Course already been advised!")
                break
        except TimeoutException:
            print("Error: Free Elective Course content did not load properly. Retrying...")

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

def press_CPE_2301_show(timeout=10):
    """
    Presses the 'Click to show course to be advisedCPE 2301' button and waits for the modal to open.
    Retries on modal errors.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2301']"
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2301.")
            return True
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

def get_CPE_2301_advise_link(timeout=10):
    """
    Gets the 'Click to advise course CPE 2301' link from the modal.
    Retries on modal errors.
    """
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2301']"
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            link = advise_button.get_attribute("href")
            print(f"CPE 2301 advise link: {link}")
            return link
        except TimeoutException:
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

def press_CPE_2302_show(timeout=10):
    """
    Presses the 'Click to show course to be advisedCPE 2302' button and waits for the modal to open.
    Retries on modal errors.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2302']"
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2302.")
            return True
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

def get_CPE_2302_advise_link(timeout=10):
    """
    Gets the 'Click to advise course CPE 2302' link from the modal.
    Retries on modal errors.
    """
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2302']"
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            link = advise_button.get_attribute("href")
            print(f"CPE 2302 advise link: {link}")
            return link
        except TimeoutException:
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

def press_CPE_2303L_show(timeout=10):
    """
    Presses the 'Click to show course to be advisedCPE 2303L' button and waits for the modal to open.
    Retries on modal errors.
    """
    show_button_selector = "a.green.rs-modal[title*='Click to show course to be advisedCPE 2303L']"
    while True:
        try:
            show_button = wait_for_element(By.CSS_SELECTOR, show_button_selector, timeout)
            show_button.click()
            print("Opened modal for CPE 2303L.")
            return True
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

def get_CPE_2303L_advise_link(timeout=10):
    """
    Gets the 'Click to advise course CPE 2303L' link from the modal.
    Retries on modal errors.
    """
    advise_button_selector = "a.green.rs-modal[title*='Click to advise course CPE 2303L']"
    while True:
        try:
            advise_button = wait_for_element(By.CSS_SELECTOR, advise_button_selector, timeout)
            link = advise_button.get_attribute("href")
            print(f"CPE 2303L advise link: {link}")
            return link
        except TimeoutException:
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

def schedule_ge_fel_course(timeout=10):
    """
    Continuously tries to press a GE-FEL button until the modal with "Schedule" appears.

    Args:
        timeout: Timeout in seconds for waiting for elements (default: 10 seconds).

    Returns:
        None
    """

    # Pre-defined list of GE-FEL courses with full titles
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

    # Display the courses for the user to select
    print("Select the GE-FEL course to see Schedule:")
    for idx, (code, title) in enumerate(ge_fel_courses, start=1):
        print(f"{idx}. GE-FEL {code} - {title}")

    # Prompt user for selection
    try:
        choice = int(input("Enter the number corresponding to the GE-FEL course: "))
        if choice < 1 or choice > len(ge_fel_courses):
            raise ValueError("Invalid selection.")
        selected_course, course_title = ge_fel_courses[choice - 1]
    except ValueError as e:
        print(f"Error: {e}. Please restart and choose a valid option.")
        return

    # Construct the CSS selector
    button_selector = f"a.green.rs-modal[title*='Click to view schedule  GE-FEL {selected_course}']"

    # Retry logic to click the button and wait for the success message
    while True:
        try:
            # Wait for and click the selected GE-FEL button
            button = wait_for_element(By.CSS_SELECTOR, button_selector, timeout)
            button.click()
            print(f"Attempting to advise course: GE-FEL {selected_course} - {course_title}...")

            # Check if the modal contains the success message
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "EnrollBody"))
            )
            print("Schedule loaded successfully.")
            
            #Fetch the schedule and href attributes
            schedule_sections = browser.find_elements(By.CSS_SELECTOR, "#EnrollBody")
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
            print("Error: GE-FEL Schedule content did not load properly. Retrying...")

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
    #navigate_to_block_advising()

    #print("Navigating to View Lacking...")
    #navigate_to_view_lacking()

    print("Navigating to Advised Course...")
    navigate_to_advise_course()

    print("Navigating to CPES 2301...")
    press_CPE_2301_show()
    link = get_CPE_2301_advise_link()
    print(f"CPE 2301 advise link: {link}")
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    print("Navigating to CPES 2302...")
    press_CPE_2302_show()
    link = get_CPE_2302_advise_link()
    print(f"CPE 2302 advise link: {link}")
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    print("Navigating to CPES 2303L...")
    press_CPE_2303L_show()
    link = get_CPE_2303L_advise_link()
    print(f"CPE 2303L advise link: {link}")
    ActionChains(browser).send_keys(Keys.ESCAPE).perform()

    #print("Navigating to GE-FEL 2...")
    #press_GE_FEL2()
    
    #print("Pressing GE-FEL AYG...")
    #advise_ge_fel_course()
    
    #schedule_ge_fel_course()
    
    #schedule_CPES()
    
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


