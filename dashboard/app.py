import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('/home/koopa/weather-pipeline/.env')

st.set_page_config(page_title='Weather Pipeline', layout='wide')
st.title('Weather Data Pipeline — Portfolio Dashboard')

@st.cache_data(ttl=300)
def load_data():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )
    df = pd.read_sql('''
        SELECT c.city_name, t.ts, f.temp_celsius,
               f.humidity_pct, f.wind_speed_ms, f.weather_main
        FROM staging.fact_weather f
        JOIN staging.dim_city c USING (city_id)
        JOIN staging.dim_time  t USING (time_id)
        ORDER BY t.ts DESC LIMIT 500
    ''', conn)
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning('No data yet — pipeline is still running. Check back soon!')
else:
    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox('City', sorted(df['city_name'].unique()))
    with col2:
        st.metric('Total rows loaded', len(df))

    city_df = df[df['city_name'] == city].sort_values('ts')
    st.line_chart(city_df.set_index('ts')['temp_celsius'], height=300)
    st.subheader('Recent readings')
    st.dataframe(city_df.head(20), use_container_width=True)
