import os, requests, psycopg2, json, logging
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger(__name__)

CITIES = [
    {'name': 'New York',      'lat': 40.7128,  'lon': -74.0060},
    {'name': 'London',        'lat': 51.5074,  'lon': -0.1278},
    {'name': 'Tokyo',         'lat': 35.6762,  'lon': 139.6503},
    {'name': 'Sydney',        'lat': -33.8688, 'lon': 151.2093},
    {'name': 'Mansfield CT',  'lat': 41.7762,  'lon': -72.2329},
    {'name': 'Hartford CT',   'lat': 41.7658,  'lon': -72.6851},
    {'name': 'Litchfield CT', 'lat': 41.7473,  'lon': -73.1879},
]

def fetch_weather(city):
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'lat': city['lat'], 'lon': city['lon'],
              'appid': os.getenv('OPENWEATHER_API_KEY'), 'units': 'metric'}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    data['name'] = city['name']
    return data

def load_to_postgres(city_name, data):
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
            (city_name, json.dumps(data), api_dt)
        )
        conn.commit()
    conn.close()

def main():
    for city in CITIES:
        try:
            data = fetch_weather(city)
            load_to_postgres(city['name'], data)
            log.info(f"Loaded {city['name']}")
        except Exception as e:
            log.error(f"Failed {city['name']}: {e}")

if __name__ == '__main__':
    main()
