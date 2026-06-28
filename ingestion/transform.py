import os, psycopg2, json, logging
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_conn():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )

def upsert_city(cur, data):
    cur.execute(
        '''INSERT INTO staging.dim_city (city_name, country, latitude, longitude)
           VALUES (%s, %s, %s, %s)
           ON CONFLICT (city_name) DO NOTHING RETURNING city_id''',
        (data['name'], data['sys']['country'],
         data['coord']['lat'], data['coord']['lon'])
    )
    row = cur.fetchone()
    if row: return row[0]
    cur.execute('SELECT city_id FROM staging.dim_city WHERE city_name = %s', (data['name'],))
    return cur.fetchone()[0]

def upsert_time(cur, ts):
    cur.execute(
        '''INSERT INTO staging.dim_time (ts, hour, day_of_week, month, year)
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (ts) DO NOTHING RETURNING time_id''',
        (ts, ts.hour, ts.isoweekday(), ts.month, ts.year)
    )
    row = cur.fetchone()
    if row: return row[0]
    cur.execute('SELECT time_id FROM staging.dim_time WHERE ts = %s', (ts,))
    return cur.fetchone()[0]

def transform():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute('SELECT raw_json, api_response_dt FROM raw.weather_api_response')
        rows = cur.fetchall()
        for raw_json, ts in rows:
            d = raw_json
            city_id = upsert_city(cur, d)
            time_id = upsert_time(cur, ts)
            cur.execute(
                '''INSERT INTO staging.fact_weather
                   (city_id, time_id, temp_celsius, feels_like,
                    humidity_pct, wind_speed_ms, weather_main, weather_desc)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT DO NOTHING''',
                (city_id, time_id,
                 d['main']['temp'], d['main']['feels_like'],
                 d['main']['humidity'], d['wind']['speed'],
                 d['weather'][0]['main'], d['weather'][0]['description'])
            )
        conn.commit()
        log.info(f'Transformed {len(rows)} rows')
    conn.close()

if __name__ == '__main__':
    transform()
