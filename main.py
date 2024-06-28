import utils

def main():
    company = "walmart"  # or "lcbo" or any other company
    config = utils.load_config(company)
    credentials = utils.load_credentials()
    driver = utils.get_driver()
    
    # Assuming the login URL is part of the config
    driver.get(config['login_url'])
    
    # Perform login
    driver.find_element_by_id("username").send_keys(credentials[company]['username'])
    driver.find_element_by_id("password").send_keys(credentials[company]['password'])
    driver.find_element_by_id("login-button").click()
    
    # Perform steps from the config
    for step in config['steps']:
        value = None
        if 'value' in step:
            value = step['value']
        utils.perform_action(driver, step, value)
    
    # Answer questions
    for q in config['questions']:
        # Code to handle questions
        pass
    
    driver.quit()

if __name__ == "__main__":
    main()