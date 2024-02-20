from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import datetime
import os
import time  # Importing time module
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
strava_email = os.getenv('STRAVA_EMAIL')
strava_password = os.getenv('STRAVA_PASSWORD')
strava_client_id = os.getenv('STRAVA_CLIENT_ID')
strava_client_secret = os.getenv('STRAVA_CLIENT_SECRET')

# Initialize variables
code = None

# Open the browser and navigate to the URL
driver = webdriver.Chrome()
url = f"https://www.strava.com/oauth/authorize?client_id={strava_client_id}&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=read_all,profile:write,activity:write"
driver.get(url)

# Check if redirected to the login page
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "email")))
    email_input = driver.find_element(By.ID, "email")
    password_input = driver.find_element(By.ID, "password")
    login_button = driver.find_element(By.ID, "login-button")

    email_input.send_keys(strava_email)
    password_input.send_keys(strava_password)
    login_button.click()
except Exception as e:
    print("Not on login page or login elements not found.", e)

# Wait for the authorization page and click 'Authorize' button
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "authorize")))
    authorize_button = driver.find_element(By.ID, "authorize")
    authorize_button.click()
except Exception as e:
    print("Authorize button not found.", e)

# Wait for the redirect and extract the code from the URL
try:
    time.sleep(5)  # Wait for a few seconds to allow the URL to change
    redirected_url = driver.current_url

    # Check if the 'code' parameter is in the URL
    if "code=" in redirected_url:
        code = redirected_url.split("code=")[1].split("&")[0]
    else:
        print("Redirected URL does not contain code parameter.")
except Exception as e:
    print("Error during redirect or code extraction.", e)
finally:
    driver.quit()

# Proceed only if code is extracted
if code:
    try:
        # Make a POST request to exchange the code for a token
        response = requests.post(
            "https://www.strava.com/oauth/token",
            data={
                "client_id": strava_client_id,
                "client_secret": strava_client_secret,
                "code": code,
                "grant_type": "authorization_code"
            }
        )

        # Check if the request was successful
        if response.status_code == 200:
            access_token = response.json().get('access_token')
            print("Access Token:", access_token)
        else:
            print("Failed to obtain access token. Status code:", response.status_code)
            print("Response content:", response.content)

        # Only proceed if access token is received
        if access_token:
            # Format the current date in ISO 8601 format
            current_date = datetime.datetime.now().strftime("%Y-%m-%d") + "T06:30:00.000"

            # Make a POST request to create an activity
            activity_response = requests.post(
                "https://www.strava.com/api/v3/activities",
                headers={"Authorization": f"Bearer {access_token}"},
                json={
                    "name": "Morning Warm-up",
                    "type": "Workout",
                    "sport_type": "Workout",
                    "start_date_local": current_date,
                    "elapsed_time": "900"
                }
            )

            if activity_response.status_code == 201:
                print("Activity created successfully.")
                print(activity_response.json())
            else:
                print("Failed to create activity. Status code:", activity_response.status_code)
                print("Response content:", activity_response.content)
        else:
            print("Access token not obtained.")

    except Exception as e:
        print("An error occurred:", e)
else:
    print("Script did not obtain the authorization code.")
