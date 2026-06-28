import os, requests, psycopg2, json, logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

CITIES = ['New York', 'London', 'Tokyo', 'Sydney']

def fetch_weather(city: str) -> dict:
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': city, 'appid': os.getenv('OPENWEATHER_API_KEY'), 'units': 'metric'}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def load_to_postgres(city: str, data: dict):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )
    api_dt = datetime.utcfromtimestamp(data['dt'])
    with conn.cursor() as cur:
        cur.execute(
            '''INSERT INTO raw.weather_api_response (city_name, raw_json, api_response_dt)
               VALUES (%s, %s, %s)
               ON CONFLICT (city_name, api_response_dt) DO NOTHING''',
            (city, json.dumps(data), api_dt)
        )
        conn.commit()
    conn.close()

def main():
    for city in CITIES:
        try:
            data = fetch_weather(city)
            load_to_postgres(city, data)
            log.info(f'Loaded {city}')
        except Exception as e:
            log.error(f'Failed {city}: {e}')

if __name__ == '__main__':
    main()
