"""Tests for frontend functionality."""
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from flask import url_for

@pytest.fixture
def driver():
    """Create a Selenium WebDriver instance."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_bypass_button_initial_state(driver, live_server, app):
    """Test the initial state of the bypass button."""
    with app.test_request_context():
        url = url_for('root.index', _external=True)
        driver.get(url)
        
        # Wait for the bypass button to be present
        bypass_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "bypassToggle"))
        )
        
        # Check initial state
        assert "btn-warning" in bypass_button.get_attribute("class")
        assert "Schwab Bypass: Off" in bypass_button.text

def test_bypass_button_toggle(driver, live_server, app):
    """Test toggling the bypass button."""
    with app.test_request_context():
        url = url_for('root.index', _external=True)
        driver.get(url)
        
        # Wait for the bypass button
        bypass_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "bypassToggle"))
        )
        
        # Click the button
        bypass_button.click()
        
        # Wait for the state to change
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "btn-success" in bypass_button.get_attribute("class") and
                         "Schwab Bypass: On" in bypass_button.text
            )
        except TimeoutException:
            pytest.fail("Bypass button state did not change after click")

def test_force_bypass_off_button(driver, live_server, app):
    """Test the force bypass off button."""
    with app.test_request_context():
        url = url_for('root.index', _external=True)
        driver.get(url)
        
        # Wait for both buttons
        bypass_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "bypassToggle"))
        )
        force_off_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "forceBypassOff"))
        )
        
        # First enable bypass
        bypass_button.click()
        WebDriverWait(driver, 10).until(
            lambda d: "btn-success" in bypass_button.get_attribute("class")
        )
        
        # Then force it off
        force_off_button.click()
        
        # Wait for the state to change back
        try:
            WebDriverWait(driver, 10).until(
                lambda d: "btn-warning" in bypass_button.get_attribute("class") and
                         "Schwab Bypass: Off" in bypass_button.text
            )
        except TimeoutException:
            pytest.fail("Bypass button state did not change after force off") 