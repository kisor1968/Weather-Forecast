from datetime import datetime, timedelta, timezone
import pandas as pd
import requests
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Campus Weather Portal", page_icon="🌤️", layout="wide"
)

# --- DYNAMIC STYLING & BACKGROUND INJECTION ---
THEME = "dark"

if THEME == "dark":
  bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)"
  card_bg = "rgba(30, 41, 59, 0.75)"
  card_border = "1px solid rgba(255, 255, 255, 0.1)"
  text_color = "#f8fafc"
  sub_text = "#94a3b8"
else:
  bg_gradient = "linear-gradient(135deg, #e0f2fe 0%, #f0fdf4 50%, #e0e7ff 100%)"
  card_bg = "rgba(255, 255, 255, 0.85)"
  card_border = "1px solid rgba(0, 0, 0, 0.08)"
  text_color = "#0f172a"
  sub_text = "#475569"

st.markdown(
    f"""
    <style>
    /* Global App Background */
    .stApp {{
        background: {bg_gradient};
        background-attachment: fixed;
    }}
    
    /* Default Text Colors */
    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: {text_color} !important;
    }}
    
    /* Custom Weather Card Styling */
    .weather-card {{
        background: {card_bg};
        backdrop-filter: blur(10px);
        border: {card_border};
        border-radius: 14px;
        padding: 12px 8px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        transition: transform 0.2s ease;
    }}
    .weather-card:hover {{
        transform: translateY(-3px);
    }}
    
    /* Dedicated Top-Right Date-Time Container */
    .time-box-container {{
        text-align: right;
        background: rgba(15, 23, 42, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 10px;
        padding: 8px 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    .time-box-time {{
        color: #ffffff !important;
        font-size: 0.95rem;
        font-weight: 700;
        margin: 0;
        padding: 0;
        line-height: 1.2;
    }}
    
    .time-box-date {{
        color: #cbd5e1 !important;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 2px 0 0 0;
        padding: 0;
        line-height: 1.2;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# College Preset Constants (Prabhu Jagatbandhu College, Howrah)
COLLEGE_NAME = "Prabhu Jagatbandhu College"
COLLEGE_SUB = "Campus Meteorological Portal • Howrah"
COLLEGE_LAT = 22.5822
COLLEGE_LON = 88.2334


# Helper: Map WMO weather codes to emojis and labels
def get_weather_display(code):
  if code == 0:
    return "☀️", "Sunny"
  elif code in [1, 2]:
    return "⛅", "Partly Cloudy"
  elif code == 3:
    return "☁️", "Overcast"
  elif code in [51, 53, 55, 56, 57]:
    return "🌧️", "Drizzle"
  elif code in [61, 63, 65, 66, 67]:
    return "🌧️", "Rain"
  elif code in [71, 73, 75, 77]:
    return "❄️", "Snow"
  elif code in [80, 81, 82]:
    return "🌦️", "Showers"
  elif code in [95, 96, 99]:
    return "⚡", "Thunderstorm"
  else:
    return "🌤️", "Fair"


# Caching Weather API request for 15 minutes
@st.cache_data(ttl=900)
def fetch_weather(lat, lon):
  url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,precipitation,weathercode,windgusts_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
  response = requests.get(url)
  return response.json()


# Caching Air Quality API request
@st.cache_data(ttl=1800)
def fetch_air_quality(lat, lon):
  aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone&timezone=auto"
  try:
    res = requests.get(aqi_url)
    return res.json()
  except Exception:
    return None


# Caching Open-Meteo Archive API request for historical climate comparison
@st.cache_data(ttl=86400)
def fetch_historical_archive(lat, lon, target_date_str):
  archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={target_date_str}&end_date={target_date_str}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
  try:
    res = requests.get(archive_url)
    return res.json()
  except Exception:
    return None


# Geocoding function for custom search
@st.cache_data(ttl=3600)
def geocode_location(location_name):
  geo_url = (
      f"https://geocoding-api.open-meteo.com/v1/search?name={location_name}&count=1"
  )
  res = requests.get(geo_url).json()
  if res.get("results"):
    return (
        res["results"][0]["latitude"],
        res["results"][0]["longitude"],
        res["results"][0]["name"],
        res["results"][0].get("country", ""),
    )
  return None


# Helper function to evaluate weather alerts
def check_weather_alerts(current_code, hourly_data):
  alerts = []
  if current_code in [95, 96, 99]:
    alerts.append(
        ("🚨 CRITICAL", "Severe Thunderstorm with lightning in progress!")
    )
  elif current_code in [63, 65, 81, 82]:
    alerts.append(("⚠️ WARNING", "Heavy rain and showers active over campus."))

  precip_list = hourly_data.get("precipitation", [])
  if precip_list:
    next_6h_rain = sum(precip_list[:6])
    if next_6h_rain >= 15.0:
      alerts.append((
          "🌧️ HEAVY RAIN ALERT",
          f"Significant rainfall expected ({next_6h_rain:.1f} mm) in the next"
          " 6 hours.",
      ))
    elif next_6h_rain >= 4.0:
      alerts.append((
          "🌧️ RAIN NOTICE",
          f"Moderate rain expected ({next_6h_rain:.1f} mm) in the next 6 hours.",
      ))

  gusts_list = hourly_data.get("windgusts_10m", [])
  if gusts_list:
    next_6h_gusts = max(gusts_list[:6])
    if next_6h_gusts >= 40.0:
      alerts.append((
          "💨 HIGH WIND ALERT",
          f"Strong wind gusts up to {next_6h_gusts:.1f} km/h forecasted.",
      ))

  return alerts


# Location-Aware AQI Interpreter (CPCB for India, WHO for Global)
def interpret_aqi(pm25, is_india=True):
  if is_india:
    if pm25 <= 30:
      return (
          "🟢 Good (CPCB)",
          "#22c55e",
          "Minimal health impact. Ideal for outdoor campus events.",
      )
    elif pm25 <= 60:
      return (
          "🟢 Satisfactory (CPCB)",
          "#84cc16",
          "Minor breathing discomfort to sensitive people.",
      )
    elif pm25 <= 90:
      return (
          "🟡 Moderate (CPCB)",
          "#eab308",
          "Breathing discomfort to individuals with lung or heart conditions.",
      )
    elif pm25 <= 120:
      return (
          "🟠 Poor (CPCB)",
          "#f97316",
          "Breathing discomfort on prolonged exposure. Mask advised.",
      )
    elif pm25 <= 250:
      return (
          "🔴 Very Poor (CPCB)",
          "#ef4444",
          "Respiratory illness risk. Move outdoor activities indoors.",
      )
    else:
      return (
          "🟣 Severe (CPCB)",
          "#a855f7",
          "Serious health impact across the entire population.",
      )
  else:
    if pm25 <= 15:
      return (
          "🟢 Good (WHO)",
          "#22c55e",
          "Air quality meets safe WHO health guidelines.",
      )
    elif pm25 <= 35:
      return (
          "🟡 Moderate (WHO)",
          "#eab308",
          "Exceeds WHO targets. Sensitive groups should exercise caution.",
      )
    elif pm25 <= 75:
      return (
          "🟠 Unhealthy (WHO)",
          "#f97316",
          "Unhealthy conditions. Limit prolonged outdoor physical exertion.",
      )
    else:
      return (
          "🔴 Hazardous (WHO)",
          "#ef4444",
          "High health risk. Outdoor activities strongly discouraged.",
      )


# --- HEADER CONTAINER WITH TIGHT HORIZONTAL SPACING & IST TIME ---
col_head1, col_head2 = st.columns([4, 1])

with col_head1:
  st.markdown(
      f"""
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="image_f6e73075.jpg" width="70" style="border-radius: 8px; flex-shrink: 0;">
            <div>
                <h3 style="margin: 0; padding: 0; font-weight: bold; color: {text_color}; font-size: 1.6rem; line-height: 1.2;">{COLLEGE_NAME}</h3>
                <p style="margin: 2px 0 0 0; padding: 0; color: {sub_text}; font-size: 0.95rem;">{COLLEGE_SUB}</p>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col_head2:
  # Explicitly force Indian Standard Time (IST = UTC + 5:30) regardless of cloud server location
  IST = timezone(timedelta(hours=5, minutes=30))
  now_obj = datetime.now(IST)
  time_str = now_obj.strftime("%I:%M:%S %p")
  date_str = now_obj.strftime("%a, %b %d, %Y")

  st.markdown(
      f"""
        <div class="time-box-container">
            <div class="time-box-time">🕒 {time_str}</div>
            <div class="time-box-date">{date_str}</div>
        </div>
        """,
      unsafe_allow_html=True,
  )

st.divider()

# Selection Mode Bar
mode = st.radio(
    "Select Mode:",
    ["Use College Preset Coordinate", "Search Other Location"],
    horizontal=True,
)

is_india_location = True

if mode == "Use College Preset Coordinate":
  lat, lon = COLLEGE_LAT, COLLEGE_LON
  is_india_location = True
else:
  custom_query = st.text_input("Enter City or Location Name:", "Kolkata")
  if custom_query:
    geo_data = geocode_location(custom_query)
    if geo_data:
      lat, lon, loc_name, country = geo_data
      is_india_location = True if country.lower() == "india" else False
    else:
      st.error("Location not found. Defaulting back to College Campus.")
      lat, lon = COLLEGE_LAT, COLLEGE_LON
      is_india_location = True
  else:
    lat, lon = COLLEGE_LAT, COLLEGE_LON
    is_india_location = True

# Fetch Weather Data & Air Quality Data
data = fetch_weather(lat, lon)
aqi_data = fetch_air_quality(lat, lon)

if data and "current_weather" in data:
  current = data["current_weather"]
  hourly = data.get("hourly", {})
  daily = data.get("daily", {})

  # --- SEVERE WEATHER & RAIN ALERT BANNER ---
  alerts = check_weather_alerts(current.get("weathercode", 0), hourly)

  if alerts:
    st.markdown("### 🚨 Campus Weather Alerts")
    for title, msg in alerts:
      if "CRITICAL" in title or "HEAVY" in title:
        st.error(f"**{title}:** {msg}")
      else:
        st.warning(f"**{title}:** {msg}")
  else:
    st.info("🟢 **No severe weather alerts.** Normal campus outdoor conditions.")

  st.markdown("<br>", unsafe_allow_html=True)

  # --- AIR QUALITY INDEX & HEALTH METRICS ---
  if aqi_data and "current" in aqi_data:
    standard_text = (
        "Indian CPCB Standard" if is_india_location else "WHO Global Standard"
    )
    st.markdown(f"### 🍃 AIR QUALITY & HEALTH METRICS ({standard_text})")
    aq_current = aqi_data["current"]

    pm25 = aq_current.get("pm2_5", 0)
    pm10 = aq_current.get("pm10", 0)
    no2 = aq_current.get("
