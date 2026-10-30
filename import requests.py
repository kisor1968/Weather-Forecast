from datetime import datetime
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


# --- HEADER CONTAINER WITH NATIVE STREAMLIT COLUMNS & LOGO ---
col_logo, col_title, col_time = st.columns([0.4, 3.6, 1.2])

with col_logo:
  try:
    st.image("image_f6e73075.jpg", width=65)
  except Exception:
    st.write("Logo")

with col_title:
  st.markdown(
      f"""
        <div style="margin-top: 2px;">
            <h3 style="margin: 0; padding: 0; font-weight: bold; color: {text_color}; font-size: 1.5rem; line-height: 1.1;">{COLLEGE_NAME}</h3>
            <p style="margin: 2px 0 0 0; padding: 0; color: {sub_text}; font-size: 0.9rem;">{COLLEGE_SUB}</p>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col_time:
  now_obj = datetime.now()
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
    no2 = aq_current.get("nitrogen_dioxide", 0)
    o3 = aq_current.get("ozone", 0)

    status_label, status_color, advisory = interpret_aqi(
        pm25, is_india=is_india_location
    )

    col_aqi1, col_aqi2, col_aqi3, col_aqi4, col_aqi5 = st.columns(5)

    with col_aqi1:
      st.markdown(
          f"""
            <div class="weather-card" style="border-left: 4px solid {status_color}; text-align: left; padding: 10px 12px;">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">Standard Category</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: {status_color};">{status_label}</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with col_aqi2:
      st.markdown(
          f"""
            <div class="weather-card">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">PM₂.₅ (Fine Particulates)</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{pm25} µg/m³</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with col_aqi3:
      st.markdown(
          f"""
            <div class="weather-card">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">PM₁₀ (Coarse Dust)</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{pm10} µg/m³</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with col_aqi4:
      st.markdown(
          f"""
            <div class="weather-card">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">NO₂ (Nitrogen Dioxide)</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{no2} µg/m³</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    with col_aqi5:
      st.markdown(
          f"""
            <div class="weather-card">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">O₃ (Ground Ozone)</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{o3} µg/m³</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown(
        f"""
        <div style="background: {card_bg}; border: {card_border}; color: {text_color}; padding: 10px 14px; border-radius: 10px; margin-top: 10px; font-size: 0.85rem;">
            💡 <b>Campus Health Advisory:</b> {advisory}
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- HOURLY FORECAST CARDS ---
  if hourly:
    st.markdown("### ⏱️ UPCOMING HOURLY FORECAST CARDS")

    current_hour_iso = datetime.now().strftime("%Y-%m-%dT%H:00")
    try:
      start_idx = hourly["time"].index(current_hour_iso)
    except ValueError:
      start_idx = 0

    hours_cols = st.columns(8)

    for col_idx, i in enumerate(range(start_idx, start_idx + 8)):
      if i < len(hourly["time"]):
        time_val = hourly["time"][i]
        dt_obj = datetime.fromisoformat(time_val)
        time_formatted = dt_obj.strftime("%I:%M %p")

        temp_val = hourly["temperature_2m"][i]
        humidity_val = hourly["relativehumidity_2m"][i]
        w_code = hourly["weathercode"][i]
        icon, _ = get_weather_display(w_code)

        with hours_cols[col_idx]:
          st.markdown(
              f"""
                    <div class="weather-card">
                        <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{time_formatted}</div>
                        <div style="font-size: 1.5rem; margin: 5px 0;">{icon}</div>
                        <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{temp_val}°C</div>
                        <div style="font-size: 0.75rem; color: #38bdf8; margin-top: 4px;">💧 {humidity_val}%</div>
                    </div>
                    """,
              unsafe_allow_html=True,
          )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- 7-DAY CAMPUS OUTLOOK CARDS ---
  if daily:
    st.markdown("### 📅 7-DAY CAMPUS OUTLOOK")
    day_cols = st.columns(7)

    for i in range(7):
      date_str = daily["time"][i]
      dt_day = datetime.strptime(date_str, "%Y-%m-%d")
      day_name = "Today" if i == 0 else dt_day.strftime("%a")
      date_short = dt_day.strftime("%m/%d")

      max_t = daily["temperature_2m_max"][i]
      min_t = daily["temperature_2m_min"][i]
      rain_sum = daily["precipitation_sum"][i]
      w_code = daily["weathercode"][i]
      icon, _ = get_weather_display(w_code)

      with day_cols[i]:
        st.markdown(
            f"""
                <div class="weather-card" style="padding: 12px 4px;">
                    <div style="font-weight: bold; font-size: 0.9rem; color: {text_color};">{day_name}</div>
                    <div style="font-size: 0.7rem; color: {sub_text}; margin-bottom: 6px;">{date_short}</div>
                    <div style="font-size: 1.8rem; margin: 6px 0;">{icon}</div>
                    <div style="font-size: 0.95rem; font-weight: bold; color: {text_color};">{max_t}° <span style="font-weight: normal; color: {sub_text}; font-size: 0.85rem;">{min_t}°</span></div>
                    <div style="font-size: 0.75rem; color: #38bdf8; margin-top: 6px;">💧 {rain_sum}mm</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- HISTORICAL CLIMATE ARCHIVE COMPARISON SECTION ---
    st.markdown("### 📜 Historical Climate Archive (Same Date Last Year)")
    last_year_date = datetime.now() - pd.DateOffset(years=1)
    ly_date_str = last_year_date.strftime("%Y-%m-%d")
    ly_display_str = last_year_date.strftime("%B %d, %Y")

    archive_data = fetch_historical_archive(lat, lon, ly_date_str)

    if archive_data and "daily" in archive_data:
      ly_daily = archive_data["daily"]
      ly_max = ly_daily.get("temperature_2m_max", [None])[0]
      ly_min = ly_daily.get("temperature_2m_min", [None])[0]
      ly_rain = ly_daily.get("precipitation_sum", [None])[0]

      today_max = daily["temperature_2m_max"][0]
      today_min = daily["temperature_2m_min"][0]
      today_rain = daily["precipitation_sum"][0]

      col_hist1, col_hist2, col_hist3 = st.columns(3)
      with col_hist1:
        st.markdown(
            f"""
                <div class="weather-card" style="text-align: left; padding: 12px 14px;">
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">Maximum Temperature</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">Today: {today_max}°C</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year ({ly_display_str}): {ly_max}°C</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
      with col_hist2:
        st.markdown(
            f"""
                <div class="weather-card" style="text-align: left; padding: 12px 14px;">
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">Minimum Temperature</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">Today: {today_min}°C</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year ({ly_display_str}): {ly_min}°C</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
      with col_hist3:
        st.markdown(
            f"""
                <div class="weather-card" style="text-align: left; padding: 12px 14px;">
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">Precipitation Sum</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">Today: {today_rain} mm</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year ({ly_display_str}): {ly_rain} mm</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
      st.info("Historical archive data unavailable for this coordinate date.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- COMPACT BOTTOM SECTION: TREND PLOT (LEFT) & LOCATION MAP (RIGHT) ---
    bottom_col_left, bottom_col_right = st.columns(2)

    with bottom_col_left:
      st.markdown("### 📈 7-Day Visual Temperature Trend")
      df_daily = pd.DataFrame({
          "Date": [
              datetime.strptime(d, "%Y-%m-%d").strftime("%a (%m/%d)")
              for d in daily["time"][:7]
          ],
          "Max Temp (°C)": daily["temperature_2m_max"][:7],
          "Min Temp (°C)": daily["temperature_2m_min"][:7],
      }).set_index("Date")
      st.line_chart(df_daily, height=300)

    with bottom_col_right:
      st.markdown("### 🗺️ Location Map")
      df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
      st.map(df_map, zoom=12, height=300)

else:
  st.error("Failed to retrieve weather information. Please check your connection.")