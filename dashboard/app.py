import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv('/home/koopa/weather-pipeline/.env')

st.set_page_config(page_title='Weather Pipeline', layout='wide')
st.title('Weather Data Pipeline — Portfolio Dashboard')
st.caption('Live data pipeline built with Python, PostgreSQL, and Apache Airflow')

@st.cache_data(ttl=300)
def load_data():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'), dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD')
    )
    df = pd.read_sql('''
        SELECT c.city_name, t.ts, f.temp_celsius, f.feels_like,
               f.humidity_pct, f.wind_speed_ms, f.weather_main, f.weather_desc
        FROM staging.fact_weather f
        JOIN staging.dim_city c USING (city_id)
        JOIN staging.dim_time  t USING (time_id)
        ORDER BY t.ts DESC LIMIT 1000
    ''', conn)
    conn.close()
    return df

df = load_data()

if df.empty:
    st.warning('No data yet — pipeline is still running. Check back soon!')
    st.stop()

# ── Top metrics row ──
latest = df.sort_values('ts').groupby('city_name').last().reset_index()
cols = st.columns(len(latest))
for i, row in latest.iterrows():
    with cols[i]:
        st.metric(
            label=row['city_name'],
            value=f"{row['temp_celsius']:.1f}°C",
            delta=f"{row['humidity_pct']}% humidity"
        )

st.divider()

# ── City selector and charts ──
col1, col2 = st.columns([1, 3])
with col1:
    city = st.selectbox('Select City', sorted(df['city_name'].unique()))
    city_df = df[df['city_name'] == city].sort_values('ts')
    if not city_df.empty:
        latest_row = city_df.iloc[-1]
        st.markdown(f"**Condition:** {latest_row['weather_desc'].title()}")
        st.markdown(f"**Feels like:** {latest_row['feels_like']:.1f}°C")
        st.markdown(f"**Wind:** {latest_row['wind_speed_ms']:.1f} m/s")
        st.markdown(f"**Last updated:** {latest_row['ts'].strftime('%H:%M %b %d')}")

with col2:
    tab1, tab2, tab3 = st.tabs(["🌡 Temperature", "💧 Humidity", "💨 Wind Speed"])
    with tab1:
        st.line_chart(city_df.set_index('ts')['temp_celsius'], height=250)
    with tab2:
        st.line_chart(city_df.set_index('ts')['humidity_pct'], height=250)
    with tab3:
        st.line_chart(city_df.set_index('ts')['wind_speed_ms'], height=250)

st.divider()

# ── Compare all cities ──
st.subheader('Compare All Cities — Current Temperature')
latest_chart = latest.set_index('city_name')['temp_celsius'].sort_values(ascending=False)
st.bar_chart(latest_chart)

st.subheader('Recent Readings')
st.dataframe(
    df.sort_values('ts', ascending=False).head(50),
    use_container_width=True
)
