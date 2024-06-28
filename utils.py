import yaml
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def load_config(company):
    with open(f'configs/{company}.yaml', 'r') as file:
        return yaml.safe_load(file)

def load_credentials():
    with open('credentials/credentials.txt', 'r') as file:
        return yaml.safe_load(file)

def get_driver():
    # Initialize the webdriver (e.g., Chrome)
    return webdriver.Chrome()

def perform_action(driver, action, value=None):
    if action['action'] == 'click':
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, action['selector']))
        ).click()
    elif action['action'] == 'fill':
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, action['selector']))
        )
        element.clear()
        element.send_keys(value)
    elif action['action'] == 'select':
        # Code for selecting an option from a dropdown
        pass