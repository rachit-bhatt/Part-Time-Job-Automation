import configparser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants
WAIT_TIME = 30  # Common wait time

# Load configuration
config = configparser.ConfigParser()
config.read('config.ini')

# Path to msedge driver
driver_path = config['webdriver']['driver_path']

# Create a new Edge session
driver = webdriver.Edge(executable_path=driver_path)

# Open login page
driver.get(config['walmart']['login_url'])

# Retrieve login credentials from the configuration file
email = config['credentials']['email']
password = config['credentials']['password']

# Log in
try:
    email_field = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="email"]'))
    )
    password_field = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="password"]'))
    )

    email_field.send_keys(email)
    password_field.send_keys(password)

    # Use the Tab key to move focus to the Sign In button and then press Space to click it
    password_field.send_keys(Keys.TAB)
    WebDriverWait(driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="signInSubmitButton"]'))
    ).send_keys(Keys.SPACE)

    print("Login successful")

    # Open the job search page after login
    driver.get(config['walmart']['jobs_url'])

    # Step 1: Click on the Filter button
    filter_button = WebDriverWait(driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="distanceLocation"]'))
    )
    driver.execute_script("arguments[0].click();", filter_button)

    # Step 2: Simulate keyboard actions to select the Distance radio button
    filter_container = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation-id="filterMenu"]'))
    )
    
    # Scroll filter container into view if necessary
    driver.execute_script("arguments[0].scrollIntoView(true);", filter_container)
    
    # Focus moves to the first radio button using Tab
    filter_container.send_keys(Keys.TAB)
    
    # Focus moves to the second radio button using Tab again
    filter_container.send_keys(Keys.TAB)
    
    # Select the radio button by pressing Space
    filter_container.send_keys(Keys.SPACE)

    # Step 3: Enter postal code in the search input
    postal_code_field = WebDriverWait(driver, WAIT_TIME).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="searchInput"]'))
    )
    postal_code_field.send_keys('M2J 1S5')  # Replace with your postal code

    # Step 4: Click on the View Jobs button
    view_jobs_button = WebDriverWait(driver, WAIT_TIME).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="viewAllJobsButton"]'))
    )
    driver.execute_script("arguments[0].click();", view_jobs_button)

    print("Filtered jobs by location")

except Exception as e:
    print(f"Error: {e}")

finally:
    driver.quit()