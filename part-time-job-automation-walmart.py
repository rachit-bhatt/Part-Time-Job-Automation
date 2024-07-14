import os
import re
import json
import configparser
from time import sleep
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Constants
WAIT_TIME = 10  # Common wait time.
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
        try: # Preventing to crash when the login is already done.
            sign_in_button.send_keys(Keys.SPACE) # This was only in the case when the system would not login on the first try.
        except StaleElementReferenceException as sere:
            print(sere)

        # Wait for login to complete
        WebDriverWait(driver, WAIT_TIME).until(EC.url_contains('userHome')) # Scrum NOTE: Remove in future or place it outside this function and find better way to determine whether the user has been successfully logged in.

        sleep(SLEEP_TIME) # Waiting a little for letting the system login

        # Storing the driver for executing a JavaScript on the page.
        self.executable_driver = driver

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

        # Get the referral value from the config file
        referral_value = self.config.get('walmart', 'referral_email')

        # Wait for the text box to appear
        referral_text_box = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="referral"]'))
        )

        referral_text_box.clear()

        del referral_text_box

        sleep(SHORT_SLEEP_TIME) # Waiting for the instance to be deleted.

        referral_text_box = WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-automation-id="referral"]'))
        )

        # Input the referral value into the text box
        referral_text_box.send_keys(referral_value)

        #endregion

        #region Other Personal Details from Resume

        json_data = self.load_json(self.json_path)
        self.fill_form(driver, json_data['personal_information'])

        #endregion

        # Going to the next page to fill other details of the form.
        self.save_and_continue(driver)

    def fill_experiences(self, driver):
        
        # Waiting for the page to load the content.
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'h2[class="css-1j9bnzb"]'))
        )

        # Waiting for the page-content to be loaded as the changes will take a while to be loaded.
        # This depends on the internet speed on the system/network running.
        sleep(SLEEP_TIME)

        json_data = self.load_json(self.json_path)

        # Fetching all of the previous experiences' objects already available in the form.
        experience_elements = driver.find_elements(By.XPATH, "//div[starts-with(@data-automation-id, 'workExperience-')]")

        # Remove all and then add one-by-one.
        for _ in experience_elements:

            # Clicking the delete button for each of the job experiences already present on the web-page.
            WebDriverWait(driver, WAIT_TIME).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-automation-id="panel-set-delete-button"]'))
            ).click()

        sleep(SHORT_SLEEP_TIME) # Waiting for the page to get loaded with the fresh UI.

        # Adding number of experiences forms as the number of for experiences.
        for _ in json_data['employment_history']:

            WebDriverWait(driver, WAIT_TIME).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'button[data-automation-id="Add"], button[data-automation-id="Add Another"]'))
            ).click()

        sleep(SHORT_SLEEP_TIME) # Waiting for a short break for letting the UI be loaded.

        # Again, getting the objects to manipuate the data to the latest sources/ids.
        experience_elements = driver.find_elements(By.XPATH, "//div[starts-with(@data-automation-id, 'workExperience-')]")

        # Iterate over each experience to fill it in the form.
        for experience_index in range(len(json_data['employment_history'])):
            self.fill_form(experience_elements[experience_index], json_data['employment_history'][experience_index])

    def execute_java_script(self, java_script):
        self.executable_driver.execute_script(java_script)

    def fill_languages(self, driver):
        pass

    def fill_experiences_and_languages(self, driver):
        # Filling the experiences.
        self.fill_experiences(driver)

        # Filling the languages.
        self.fill_languages(driver) # This step is optional and skippable.

        # Submitting the information.
        self.save_and_continue(driver)

    def tab_and_type(self, driver, key : str | Keys):

        driver.send_keys(Keys.TAB)

        sleep(SHORT_SLEEP_TIME)

        driver.send_keys(key)

        sleep(SHORT_SLEEP_TIME)

    def fill_application_questions_1(self, driver):
        # WebDriverWait(driver, WAIT_TIME).until(
        #     EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Application Questions 1 of 2')]"))
        # )

        sleep(SLEEP_TIME)

        json_data = self.load_json(self.json_path)

        self.fill_form(driver, json_data['application_questions_1'])

        # Submitting the information and going to the next page.
        self.save_and_continue(driver)

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

        #region Clears the text in one-go.

        for field in fields.values():

            if field['type'] == 'text' or \
                field['type'] == 'paragraph':
                try:
                    element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-automation-id="{ field["location"] }"]')))
                    element.clear()
                    del element
                except TimeoutException as te: # When the text-box is not found or will take time to render.
                    print('TimeoutException:\n', te) # Ignore it and move further.

        #endregion

        #region Fills the data in the empty containers.

        for field_name, field in fields.items():
            element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'[data-automation-id="{ field["location"] }"]')))

            if field['type'] == 'text':
                try:
                    element.send_keys(field['value'])

                    try:
                        # Set the value of the text box using JavaScript
                        driver.execute_script(f"arguments[0].value = '{ field['value'] }';", element)
                    except AttributeError as ae:
                        # When the `driver` doesn't support `execute_script()` functionality.
                        print('AttributeError - Text:\n', ae)

                except StaleElementReferenceException as sere:
                    print('StaleElementReferenceException - Text:\n', sere)

            elif field['type'] == 'paragraph': # This type is used to write a whole paragraph and also includes the code-snippets.
                try:
                    # Iterating over each element of the list to be written.
                    for item in field['items']:
                        element.send_keys(item)
                        element.send_keys(Keys.ENTER)

                except StaleElementReferenceException as sere:
                    print('StaleElementReferenceException - Paragraph:\n', sere)

            elif field['type'] == 'dropdown': # NOTE: Using different/specialized/customized logic for dropdowns at moment only but will optimize in the future.
                # Wait for the dropdown button to be present and click it to open the dropdown menu
                wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, f'button[data-automation-id="{ field["location"] }"]'))).click()

                # Wait for the dropdown options to be visible and locate the option for State.
                wait.until(EC.element_to_be_clickable((By.XPATH, f'//li[@data-value="{ field["key"] }"]/div[contains(text(), "{ field["value"] }")]'))).click()

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

            elif field['type'] == 'date':
                element = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, f'input[data-automation-id="{ field["location"] }"]'))) # Expecting two objects at least from this script.

                if field_name[ : 5] == 'start':

                    #region Start-Date

                    element = element[0]

                    #endregion

                elif field_name[ : 3] == 'end':

                    #region End-Date

                    element = element[1]

                    if field['value'] == 'present':
                        query = 'input[data-automation-id="currentlyWorkHere"]'
                        # check_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, query)))

                        # Check the check-box if not selected.
                        # if not check_box.is_selected():
                            # check_box.click()

                        self.execute_java_script(f'''
                            var checkbox = document.querySelector('{ query }');
                            if (checkbox && !checkbox.checked) {{
                                checkbox.click();
                                console.log('Checkbox is now checked!');
                            }} else {{
                                console.log('Checkbox was already checked.');
                            }}
                        ''')

                        del element

                        return

                    #endregion

                element.send_keys(field['value'])

            elif field['type'] == 'qna':
                # Element's Parent's Input Tag.
                # Structure:
                # - Parent
                #   - Element
                #   - Input Tag

                # Execute JavaScript to get the next sibling
                # next_sibling = driver.execute_script("return arguments[0].nextElementSibling;", element)

                # Assigning the actual value of the application question in the drop-down.
                # driver.execute_script("arguments[0].value = arguments[1];", element, field['value']) # For Button Tag.
                # driver.execute_script("arguments[0].text = arguments[1];", element, field['context']) # For Button Text.
                # driver.execute_script("arguments[0].value = arguments[1];", next_sibling, field['value']) # For Input Tag.

                # Simulate tabbing and key presses
                active_element = driver.switch_to.active_element

                #region Question 1

                # Going to the first question.
                active_element.send_keys(Keys.TAB)
                sleep(SHORT_SLEEP_TIME)

                # Selecting the active element which is currently on focus.
                active_element = driver.switch_to.active_element

                # Answering first question.
                active_element.send_keys('Y')
                sleep(SHORT_SLEEP_TIME)  # 2-second delay

                #endregion

                #region Question 2

                # Answering second question.
                active_element.send_keys(Keys.TAB)
                sleep(SHORT_SLEEP_TIME)

                # Selecting the active element which is currently on focus.
                active_element = driver.switch_to.active_element

                # Simulate pressing 'O'
                active_element.send_keys('O')
                sleep(SHORT_SLEEP_TIME)

                #endregion

                # Simulate pressing Tab
                active_element.send_keys(Keys.TAB)
                sleep(SHORT_SLEEP_TIME)
            
            del element

        #endregion

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