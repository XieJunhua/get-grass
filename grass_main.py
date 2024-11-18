#!/usr/bin/env python3
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random
import time
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


# function to handle cookie banner: If a cookie banner is present press the button containing the accept text
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
    if not email or not password:
        logging.error(
            "No username or password provided. Please set the GRASS_USER and GRASS_PASS environment variables."
        )
        return  # Exit the script if credentials are not provided

    chrome_options = Options()
    chrome_options.add_extension(f"./{extension_id}.crx")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0"
    )
    chrome_options.add_argument(
        f"--proxy-server=http://{proxy_user}:{proxy_pass}@{proxy_host}:{proxy_port}"
    )

    # Initialize the WebDriver
    driver = webdriver.Chrome(options=chrome_options)
    ipinfo = driver.get("http://ip-api.com/json")  # Or any other IP check service
    logging.info(f"Proxy connection successful: {ipinfo}")

    try:
        # Navigate to a webpage
        logging.info(f"Navigating to {extension_url} website...")
        driver.get(extension_url)
        time.sleep(random.randint(3, 7))
        handle_cookie_banner(driver)
        logging.info("Entering credentials...")

        # Wait for page load and try multiple selectors
        username = None
        selectors = [
            (By.CSS_SELECTOR, "input[name='user']"),
            (By.ID, "field-:r9:"),
            (By.CLASS_NAME, "chakra-input"),
            (By.CSS_SELECTOR, "input[placeholder='Username or Email']"),
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
            raise Exception("Could not find username field with any selector")

        username.clear()
        username.send_keys(email)

        # Find password field
        passwd = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "password"))
        )
        passwd.clear()
        passwd.send_keys(password)

        logging.info("Clicking the login button...")
        button = driver.find_element(By.XPATH, "//button")
        button.click()
        logging.info("Waiting response...")

        time.sleep(random.randint(10, 50))
        logging.info("Accessing extension settings page...")
        driver.get(f"chrome-extension://{extension_id}/index.html")
        time.sleep(random.randint(3, 7))

        logging.info("Clicking the extension button...")
        button = driver.find_element(By.XPATH, "//button")
        button.click()

        logging.info("Logged in successfully.")
        handle_cookie_banner(driver)
        logging.info("Earning...")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.debug(f"Current URL: {driver.current_url}")
        logging.debug(f"Page source: {driver.page_source}")
        driver.quit()
        time.sleep(60)
        run()

    while True:
        try:
            time.sleep(3600)
        except KeyboardInterrupt:
            logging.info("Stopping the script...")
            driver.quit()
            break


run()
