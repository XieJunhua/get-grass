#!/usr/bin/env python3
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import random
import time
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def handle_cookie_banner(driver):
    """
    Handle the cookie banner by clicking the "Accept" button if it's present.

    Args:
        driver (webdriver): The WebDriver instance.
    """
    try:
        cookie_banner = driver.find_element(
            By.XPATH, "//button[contains(text(), 'ACCEPT')]"
        )
        if cookie_banner:
            logging.info("Cookie banner found. Accepting cookies...")
            cookie_banner.click()
            time.sleep(random.randint(3, 11))
            logging.info("Cookies accepted.")
    except Exception:
        pass


def setup_driver(chrome_options=None):
    if chrome_options is None:
        chrome_options = Options()

    # Modify WebDriver characteristics
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    # Disable automation features
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return driver
    except WebDriverException as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise


def run():
    setup_logging()
    logging.info("Starting the script...")

    # Read variables from the OS env
    email = os.getenv("GRASS_USER")
    password = os.getenv("GRASS_PASS")
    extension_id = os.getenv("EXTENSION_ID")
    extension_url = os.getenv("EXTENSION_URL")
    proxy_host = os.getenv("PROXY_HOST")
    proxy_port = os.getenv("PROXY_PORT")
    proxy_user = os.getenv("PROXY_USER")
    proxy_pass = os.getenv("PROXY_PASS")

    # Check if credentials are provided
    if not all([email, password, extension_id, extension_url]):
        logging.error(
            "Missing required environment variables. Please check configuration."
        )
        return

    chrome_options = Options()
    chrome_options.add_extension(f"./{extension_id}.crx")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    )

    if all([proxy_host, proxy_port, proxy_user, proxy_pass]):
        chrome_options.add_argument(
            f"--proxy-server=http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
        )

    driver = None
    try:
        driver = setup_driver(chrome_options)

        # Check proxy connection
        driver.get("http://ip-api.com/json")
        time.sleep(3)
        logging.info("Proxy connection successful")

        # Navigate to extension URL
        logging.info(f"Navigating to {extension_url}...")
        driver.get(extension_url)
        time.sleep(5)

        handle_cookie_banner(driver)
        time.sleep(3)

        logging.info("Entering credentials...")

        # Find username field with multiple selectors
        username = None
        selectors = [
            (By.CSS_SELECTOR, "input[name='user']"),
            (By.ID, "field-:r9:"),
            (By.CLASS_NAME, "chakra-input"),
            (By.CSS_SELECTOR, "input[placeholder='Username or Email']"),
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[type='text']"),
            (By.XPATH, "//input[@placeholder='Email' or @placeholder='Username']"),
            (
                By.XPATH,
                "//input[contains(@class, 'login') or contains(@class, 'email')]",
            ),
        ]

        for by, selector in selectors:
            try:
                username = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((by, selector))
                )
                if username:
                    logging.info(f"Found username field using selector: {selector}")
                    break
            except TimeoutException:
                continue

        if not username:
            raise Exception("Could not find username field")

        username.clear()
        username.send_keys(email)

        # Find and fill password field
        passwd = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        passwd.clear()
        passwd.send_keys(password)

        # Click login button
        logging.info("Clicking login button...")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    "//button[contains(text(), 'Login') or contains(text(), 'Sign in')]",
                )
            )
        )
        login_button.click()

        # Wait for login
        time.sleep(random.randint(10, 20))

        # Access extension page
        logging.info("Accessing extension settings...")
        driver.get(f"chrome-extension://{extension_id}/index.html")
        time.sleep(random.randint(3, 7))

        # Click extension button
        extension_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button"))
        )
        extension_button.click()

        logging.info("Successfully logged in and initialized extension")
        handle_cookie_banner(driver)
        logging.info("Starting earning process...")

        # Main loop
        while True:
            try:
                time.sleep(3600)
            except KeyboardInterrupt:
                logging.info("Stopping script...")
                if driver:
                    driver.quit()
                break

    except Exception as e:
        logging.error(f"An error occurred: {e}")
        if driver:
            logging.debug(f"Current URL: {driver.current_url}")
            driver.quit()
        time.sleep(60)
        run()


if __name__ == "__main__":
    run()
