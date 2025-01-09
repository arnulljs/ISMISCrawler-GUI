from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to your ChromeDriver
service = Service('./chromedriver.exe')
options = webdriver.ChromeOptions()
# options.add_argument("--headless")  # Optional: Run in headless mode

# Start WebDriver
driver = webdriver.Chrome(service=service, options=options)

try:
    # Open the target URL
    driver.get("https://ismis.usc.edu.ph/Paymaya")

    # Wait for the form to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "__RequestVerificationToken")))

    # Fill out the form fields
    driver.find_element(By.NAME, "Student.Firstname").send_keys("")
    driver.find_element(By.NAME, "Student.Middlename").send_keys("")
    driver.find_element(By.NAME, "Student.Lastname").send_keys("")
    driver.find_element(By.NAME, "Student.IDNumber").send_keys("")
    driver.find_element(By.NAME, "Student.EmailAddress").send_keys("")
    driver.find_element(By.NAME, "Student.MobileNumber").send_keys("")
    driver.find_element(By.NAME, "Student.CardCode").send_keys("PM") #PM for paymaya,VC for visa card, MC for mastercard, JCB for jcb card
    # for some reason should you choose paymaya lets say 3000 the service fee is 15. but if you choose visa card/mastercard/jcb the service fee is 37.50
    driver.find_element(By.NAME, "Telleritem[0].Amount").send_keys("")

    # Submit the form
    driver.find_element(By.CSS_SELECTOR, "button.btn").click()

    # Wait for the next page to load
    time.sleep(5)  # Adjust based on network speed

    # Extract the href URL if available
    try:
        href_link = driver.find_element(By.CSS_SELECTOR, "a[href*='payments.maya.ph']").get_attribute("href")
    except:
        href_link = "No href link found."

    # Extract the meta refresh URL if available
    try:
        meta_redirect = driver.find_element(By.CSS_SELECTOR, "meta[http-equiv='refresh']").get_attribute("content")
        meta_url = meta_redirect.split("URL=")[1].strip() if "URL=" in meta_redirect else "No meta redirect URL."
    except:
        meta_url = "No meta redirect found."

    # Wait for the final redirection and capture the redirected URL
    WebDriverWait(driver, 10).until(lambda d: "payments.maya.ph" in d.current_url)
    final_redirected_url = driver.current_url

    # Print the URLs
    print("Href link (if present):", href_link)
    print("Meta redirect URL (if present):", meta_url)
    print("Final redirected URL:", final_redirected_url)

    # Save the links to a file
    with open("redirect_links.txt", "w") as file:
        file.write(f"Href link: {href_link}\n")
        file.write(f"Meta Redirect URL: {meta_url}\n")
        file.write(f"Final Redirected URL: {final_redirected_url}\n")

except Exception as e:
    print("An error occurred:", str(e))
finally:
    # Close the browser
    driver.quit()
