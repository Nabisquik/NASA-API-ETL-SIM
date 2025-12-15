import os
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv('API_KEY')

def fetch_data():

    end_date = datetime.now()
    start_date = end_date - timedelta(days=1) # 1 day back for now

    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    print(f"Date range: {start_date_str} to {end_date_str}")

    API_URL = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={start_date_str}&end_date={end_date_str}&api_key={API_KEY}"

    try:
        response = requests.get(API_URL)
        response.raise_for_status()
        print("Inital API response received successfully.")
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        raise
    

def fetch_orbital_data(asteroid_id):
    """
    Orbital data must be pulled by id from date range api.
    This will take the parsed response from the previous call and search for it's full orbital data.
    """
    # Orbital data API
    API_URL2 = f"https://api.nasa.gov/neo/rest/v1/neo/{asteroid_id}?api_key={API_KEY}"

    try:
        response = requests.get(API_URL2)
        response.raise_for_status()
        # time.sleep(0.1) # for rate limiting
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        raise

    
