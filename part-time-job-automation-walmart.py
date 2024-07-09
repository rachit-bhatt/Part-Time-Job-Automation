import os
import re
import json
import configparser
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants
WAIT_TIME = 30  # Common wait time.
SLEEP_TIME = 5  # Common sleep time.
SHORT_SLEEP_TIME = 2  # Common short sleep time.

class WalmartJobApplication:
    def __init__(self, config_file = 'config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        self.driver_path = self.config['webdriver']['driver_path']
        self.login_url = self.config['walmart']['login_url']
        self.jobs_url = self.config['walmart']['jobs_url']
        self.email = self.config['credentials']['email']
        self.password = self.config['credentials']['password']

        self.location = 'CA/M2J 1S5/North York'  # Default location for job search
        self.log_path = 'Resume/Resume Log.txt'
        self.resume_folder = 'Resume'

        self.json_path = self.config['json']['json_path']

    def login(self):
        driver = webdriver.Edge(executable_path = self.driver_path)

        driver.get(self.login_url)

        # Wait for email input field to be visible
        WebDriverWait(driver, WAIT_TIME).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="email"]')))

        # Login
        email_field = driver.find_element(By.CSS_SELECTOR, 'input[data-automation-id="email"]')
        email_field.send_keys(self.email)

        password_field = driver.find_element(By.CSS_SELECTOR, 'input[data-automation-id="password"]')
        password_field.send_keys(self.password)

        # Pressing the Sign-In button manually because can't find it's source using HTML code.
        password_field.send_keys(Keys.TAB)

        # Waiting a little to let the system know that it is a user-input and not a machine doing DOS attack.
        # sleep(SLEEP_TIME)

        sign_in_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-automation-id="click_filter"]'))
        )

        # Clicking the button thrice as on pressing it once sometimes doesn't work.
        sign_in_button.click()
        sign_in_button.send_keys(Keys.SPACE)
        sleep(SHORT_SLEEP_TIME) # Waiting for a natural delay.
        sign_in_button.send_keys(Keys.SPACE)

        # Wait for login to complete
        WebDriverWait(driver, WAIT_TIME).until(EC.url_contains('userHome')) # Scrum NOTE: Remove in future or place it outside this function and find better way to determine whether the user has been successfully logged in.

        sleep(SLEEP_TIME) # Waiting a little for letting the system login

        return driver

    def search_jobs(self, driver):
        driver.get(self.jobs_url)

        # Step 1: Click on the Filter button
        filter_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="distanceLocation"]'))
        )
        driver.execute_script("arguments[0].click();", filter_button)

        # Step 2: Select the Distance radio button directly
        distance_radio_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-uxi-element-id="radio_distance"]'))
        )
        driver.execute_script("arguments[0].click();", distance_radio_button)

        # Step 3: Enter full string in the search input
        postal_code_field = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="searchInput"]'))
        )
        postal_code_field.send_keys('CA/M2J 1S5/North York')  # Enter the full string

        # Step 4: Wait for a few seconds to allow suggestions to load
        sleep(SLEEP_TIME)

        # Step 5: Press Down arrow key and Enter to select the suggestion
        postal_code_field.send_keys(Keys.DOWN)
        postal_code_field.send_keys(Keys.ENTER)

        # Step 6: Click on the View Jobs button
        view_jobs_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="viewAllJobsButton"]'))
        )
        driver.execute_script("arguments[0].click();", view_jobs_button)

        print("Filtered jobs by location")

        # Waiting for a few seconds to allow the searched data to load.
        sleep(SLEEP_TIME)

        return driver

    def open_job_in_new_tab(self, driver, job_title, job_link):
        # Open job link in a new tab
        current_window = driver.current_window_handle
        driver.execute_script("window.open();")

        sleep(SLEEP_TIME)  # Wait to allow the new tab to open.

        new_window = [window for window in driver.window_handles if window != current_window][0]

        driver.switch_to.window(new_window)
        driver.get(job_link)

        # Match job title with available resumes
        matching_resume = self.find_resume(job_title)

        if matching_resume:
            # Proceed with application process using matching_resume
            print(f"Applying to { job_title } using { matching_resume }")

            # Implement application process (form filling, submission, etc.)
            self.apply_job(driver)

        driver.close()
        driver.switch_to.window(current_window)

    def find_resume(self, job_title):
        # Normalize job title for comparison
        normalized_job_title = re.sub(r'\(.*?\)\s*', '', job_title, flags = re.IGNORECASE).strip().lower()

        # Find matching resume
        resume_found = False
        self.resume_file = str()

        # List all resumes in the Resume folder
        for resume_file in os.listdir(self.resume_folder):
            if resume_file.endswith('.pdf'):
                normalized_resume_name = re.sub(r'\.pdf$', '', resume_file, flags = re.IGNORECASE).strip().lower()
                if normalized_job_title == normalized_resume_name:
                    resume_found = True
                    self.resume_file = resume_file
                    break

        # Steps on finding the resume
        if resume_found:
            return resume_found
        else:
            # Log missing resume
            log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Resume not found for job title: { job_title }\n"
            with open(self.log_path, 'a') as log_file:
                log_file.write(log_message)

            return None

    def apply_job(self, driver):
        # Click the "Apply" button
        WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-automation-id="adventureButton"]'))).click()

        # Click the "Autofill with Resume" button
        WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a[data-automation-id="autofillWithResume"]'))).click()

        # Validator.
        if self.resume_file:
            self.uploading_resume(driver)
            self.choose_personal_details(driver)
        else:
            log_message = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Resume file not found before uploading!\n"
            with open(self.log_path, 'a') as log_file:
                log_file.write(log_message)

    def uploading_resume(self, driver):
        try:
            # Upload the resume file
            upload_element = WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="file-upload-input-ref"]')))
            upload_element.send_keys(os.path.join(os.getcwd(), self.resume_folder, self.resume_file))

            # Wait until the resume is uploaded
            WebDriverWait(driver, WAIT_TIME).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation-id="file-upload-item"]')))

            # Click the "Continue" button
            continue_button = WebDriverWait(driver, WAIT_TIME).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="bottom-navigation-next-button"]')))
            continue_button.click()

        except TimeoutException:
            # Skipping the step to upload the resume.
            pass

    def choose_personal_details(self, driver):
        #region Referral Option Selection

        #region Reaching to Search Bar

        # Waiting till the body of the page renders.
        WebDriverWait(driver, WAIT_TIME).until(
            EC.url_contains('job')
        )

        try:
            # Waiting for the back button to render.
            WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="bottom-navigation-back-button"]'))
            )
        except TimeoutException:
            pass # Possible that sometimes we don't have `Back` button on this page so we pass this step.

        # Focusing on the `Back to Job Posting` option for reliable focus tabbing.
        back_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[class="css-dsowhc"]'))
        )

        # Tabbing to gain focus of the search bar.
        back_button.send_keys(Keys.TAB)

        # Use JavaScript to get the currently focused element and simulate pressing the Enter key
        script = """
        var focusedElement = document.activeElement;
        focusedElement.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter'}));
        focusedElement.dispatchEvent(new KeyboardEvent('keypress', {key: 'Enter'}));
        focusedElement.dispatchEvent(new KeyboardEvent('keyup', {key: 'Enter'}));
        return focusedElement;
        """
        focused_element = driver.execute_script(script)

        # Pressing ENTER key to open the menu.
        focused_element.send_keys(Keys.ENTER)

        #endregion

        # Select the Referral option
        referral_option = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-automation-label="Referral"]'))
        )
        referral_option.click()

        # Select the first radio button ("I know someone who works here")
        first_radio_button = WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-automation-id="promptOption"]'))
        )
        first_radio_button.click()

        # Wait for the dialog to disappear after selection (if applicable)
        WebDriverWait(driver, WAIT_TIME).until_not(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-automation-label="Referral"]'))
        )

        #endregion

        #region Referral Email

        # Wait for the text box to appear
        referral_text_box = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="referral"]'))
        )

        # Get the referral value from the config file
        referral_value = self.config.get('walmart', 'referral_email')

        # Input the referral value into the text box
        referral_text_box.send_keys(referral_value)

        #endregion

        #region Other Personal Details from Resume

        json_data = self.load_json(self.json_path)
        self.fill_form(driver, json_data['personal_information'])

        #endregion

    def fill_experiences_and_languages(self, driver):
        
        # Waiting for the page to load the content.
        sleep(SLEEP_TIME)

        json_data = self.load_json(self.json_path)

        experience_elements = driver.find_elements(By.XPATH, "//div[starts-with(@data-automation-id, 'workExperience-')]")

        if len(experience_elements) != len(list(json_data['employment_history'].values())):

            # Remove all and then add one-by-one.
            for div_tags in experience_elements:
                pass

    def fill_application_questions_1(self, driver):
        
        # WebDriverWait(driver, WAIT_TIME).until(
        #     EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Application Questions 1 of 2')]"))
        # )

        # Waiting for the page to load the content.
        sleep(SLEEP_TIME)

        body = driver.find_element(By.TAG_NAME, 'body')
        body.send_keys(Keys.TAB)
        sleep(SHORT_SLEEP_TIME)
        body.send_keys('Y')
        sleep(SHORT_SLEEP_TIME)

        sleep(SLEEP_TIME)

    def fill_application_questions_2(self, driver):
        pass

    #region Automative Form Filling

    def load_json(self, file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def save_and_continue(self, driver):
        WebDriverWait(driver, WAIT_TIME).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="bottom-navigation-next-button"]'))
        ).click()

    def fill_form(self, driver, fields):
        wait = WebDriverWait(driver, WAIT_TIME)

        for field in fields.values():
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-automation-id="{ field["location"] }"]')))

            if field['type'] == 'text':
                element.clear()
                element.send_keys(field['value'])
            elif field['type'] == 'dropdown': # NOTE: Using different/specialized/customized logic for dropdowns at moment only but will optimize in the future.
                # Wait for the dropdown button to be present and click it to open the dropdown menu
                dropdown_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-automation-id="{ field["location"] }"]')))
                dropdown_button.click()

                # Wait for the dropdown options to be visible and locate the option for Ontario
                ontario_option = wait.until(EC.element_to_be_clickable((By.XPATH, f'//li[@data-value="{ field["key"] }"]/div[contains(text(), "{ field["value"] }")]')))

                # Click the Ontario option to select it
                ontario_option.click()

                #region Code for the normal dropdowns
                # element.click()
                # option = WebDriverWait(driver, WAIT_TIME).until(
                #     EC.presence_of_element_located((By.XPATH, f"//option[text()='{ field['value'] }']"))
                # )
                # option.click()
                #endregion
            elif field['type'] == 'radio':
                element.click()
            elif field['type'] == 'checkbox':
                if not element.is_selected():
                    element.click()

        self.save_and_continue()

    #endregion

    def delete_missing_resume_log(self, path):
        if os.path.exists(path):
            os.remove(path)

    def run_application_process(self):
        # Delete the old logs.
        self.delete_missing_resume_log(self.log_path)

        driver = self.login()

        #region Debug
        # self.search_jobs(driver)
        driver.get('https://walmart.wd5.myworkdayjobs.com/en-US/WalmartExternal/job/Toronto-(Stockyards)%2C-ON/XMLNAME--CAN--Stock-Unloader-Associate_R-1905256-1/apply/autofillWithResume?q=Stock')
        self.resume_file = 'Stock Unloader Associate.pdf'
        self.uploading_resume(driver)
        self.choose_personal_details(driver)
        self.fill_experiences_and_languages(driver)
        self.fill_application_questions_1(driver)
        self.fill_application_questions_2(driver)
        return None
        #endregion
        
        # Iterate through job listings and open each job in a new tab
        job_listings = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ul[aria-label^="Page"] > li'))
        )

        for job in job_listings:

            # Finding the section (li element) having job details.
            job_title_element = job.find_element(By.CSS_SELECTOR, 'a[data-automation-id="jobTitle"]')

            # Pulling out the Job-Title and the Job-Link to apply for it.
            job_title = job_title_element.text
            job_link = job_title_element.get_attribute('href')

            # Opening the tab in the new window.
            self.open_job_in_new_tab(driver, job_title, job_link)

        # Close the driver session
        driver.quit()

if __name__ == "__main__":
    walmart_app = WalmartJobApplication()
    walmart_app.run_application_process()