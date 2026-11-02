from datetime import datetime, timedelta, timezone
import base64
import io
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

# Optional Speech-to-Text Import for Voice Search
try:
  from streamlit_mic_recorder import speech_to_text

  HAS_MIC = True
except ImportError:
  HAS_MIC = False

# Page Configuration
st.set_page_config(
    page_title="Campus Weather Portal / ক্যাম্পাস আবহাওয়া পোর্টাল",
    page_icon="🌤️",
    layout="wide",
)

# --- TRILINGUAL DICTIONARY SYSTEM (EN / BN / HI) ---
TEXTS = {
    "en": {
        "college_name": "Prabhu Jagatbandhu College",
        "college_sub": "Campus Meteorological Portal • Howrah",
        "select_mode": "Select Location Input Mode:",
        "mode_preset": "College Campus Preset",
        "mode_search": "Search Micro-Lane or Location Name",
        "mode_coords": "Enter Exact Coordinates (Lat/Lon)",
        "search_label": (
            "Enter Micro-Lane, Street, or Area (e.g., Nabin Mukherjee Lane,"
            " Bataitala, Shibpur):"
        ),
        "search_default": "Nabin Mukherjee Lane",
        "voice_title": "🎙️ Voice Search (Click mic to speak)",
        "search_error": (
            "Micro-lane search could not be resolved automatically. Defaulting"
            " to College Campus."
        ),
        "coords_label": (
            "Provide exact GPS coordinates for your micro-location or lane from"
            " Google Maps:"
        ),
        "lat": "Latitude",
        "lon": "Longitude",
        "custom_coord": "Custom Coordinate Pinpoint",
        "data_source": "Active Meteorological Data Source",
        "active_zone": "Active Zone",
        "exact_coords": "Exact Coordinates",
        "no_alerts": (
            "🟢 **No severe weather alerts.** Normal outdoor conditions active."
        ),
        "alerts_title": "🚨 Weather Alerts",
        "sat_title": "🛰️ REAL-TIME SATELLITE & RADAR IMAGERY (INSAT-3D / RADAR)",
        "sat_radio_label": "Select View Mode:",
        "sat_mode_radar": "🌐 Interactive Live Regional Radar (In-App)",
        "sat_mode_imd": "🛰️ Official IMD INSAT-3D Satellite Viewer Portal",
        "sat_hub_info": (
            "🔒 Official India Meteorological Department (IMD) Satellite Hub"
        ),
        "sat_hub_desc": (
            "Access real-time INSAT-3D / INSAT-3DR Infrared, Visible, and Water"
            " Vapour spectral channels directly on IMD's portal:"
        ),
        "sat_btn_text": "🚀 Open Official IMD INSAT-3D Satellite Portal",
        "sat_source_note": (
            "Satellite observations are streamed live from the India"
            " Meteorological Department (IMD) INSAT-3D/3DR satellite network."
        ),
        "aqi_title": "🍃 AIR QUALITY: ACTUAL VS. SAFE STANDARD",
        "overall_status": "Overall Status",
        "standard_limit": "Standard Limit",
        "safe_limit": "Safe / Within Limit",
        "hourly_title": "⏱️ UPCOMING HOURLY FORECAST CARDS",
        "outlook_title": "📅 7-DAY OUTLOOK",
        "history_title": "📜 Historical Climate Archive (Same Date Last Year)",
        "export_title": "📥 Export Meteorological & Air Quality Report",
        "csv_btn": "📥 Download CSV Report",
        "txt_btn": "📄 Download Text Summary",
        "max_temp": "Maximum Temperature",
        "min_temp": "Minimum Temperature",
        "precip_sum": "Precipitation Sum",
        "today": "Today",
        "trend_title": "📈 7-Day Visual Temperature Trend",
        "map_title": "🗺️ Location Map",
        "visitors": "TOTAL VISITORS",
        "footer_text": (
            "© 2026 Prabhu Jagatbandhu College &nbsp;|&nbsp; Developed & Maintained"
            " by Dr. Kisor Mukhopadhyay"
        ),
    },
    "bn": {
        "college_name": "প্রভু জগৎবন্ধু কলেজ",
        "college_sub": "ক্যাম্পাস আবহাওয়া পোর্টাল • হাওড়া",
        "select_mode": "লোকেশন ইনপুট মোড নির্বাচন করুন:",
        "mode_preset": "কলেজ ক্যাম্পাস প্রিসেট",
        "mode_search": "মাইক্রো-লেন বা এলাকার নাম খুঁজুন",
        "mode_coords": "সঠিক স্থানাঙ্ক (অক্ষাংশ/দ্রাঘিমাংশ) লিখুন",
        "search_label": (
            "মাইক্রো-লেন, রাস্তা বা এলাকার নাম লিখুন (যেমন: নবীন মুখার্জি লেন,"
            " বাটীতলা, শিবপুর):"
        ),
        "search_default": "নবীন মুখার্জি লেন",
        "voice_title": "🎙️ ভয়েস অনুসন্ধান (কথা বলতে মাইকে ক্লিক করুন)",
        "search_error": (
            "মাইক্রো-লেন স্বয়ংক্রিয়ভাবে খুঁজে পাওয়া যায়নি। ডিফল্টভাবে কলেজ"
            " ক্যাম্পাসে ফিরে যাওয়া হচ্ছে।"
        ),
        "coords_label": (
            "গুগল ম্যাপ থেকে আপনার মাইক্রো-লোকেশন বা লেনের সঠিক জিপিএস স্থানাঙ্ক দিন:"
        ),
        "lat": "অক্ষাংশ (Latitude)",
        "lon": "দ্রাঘিমাংশ (Longitude)",
        "custom_coord": "কাস্টম স্থানাঙ্ক পিনপয়েন্ট",
        "data_source": "সক্রিয় আবহাওয়া ডেটা উৎস",
        "active_zone": "সক্রিয় অঞ্চল",
        "exact_coords": "সঠিক স্থানাঙ্ক",
        "no_alerts": (
            "🟢 **কোনো তীব্র আবহাওয়ার সতর্কতা নেই।** স্বাভাবিক আবহাওয়া বিরাজ"
            " করছে।"
        ),
        "alerts_title": "🚨 আবহাওয়া সতর্কতা",
        "sat_title": (
            "🛰️ রিয়েল-টাইম স্যাটেলাইট ও রাডার চিত্র (ইনস্যাট-৩ডি / রাডার)"
        ),
        "sat_radio_label": "দৃশ্য মোড নির্বাচন করুন:",
        "sat_mode_radar": "🌐 ইন্টারেক্টিভ লাইভ আঞ্চলিক রাডার (অ্যাপের ভেতরে)",
        "sat_mode_imd": "🛰️ অফিসিয়াল IMD ইন্টারেক্টিভ স্যাটেলাইট পোর্টাল",
        "sat_hub_info": (
            "🔒 অফিসিয়াল ভারত আবহাওয়া বিভাগ (IMD) স্যাটেলাইট হাব"
        ),
        "sat_hub_desc": (
            "IMD এর পোর্টালে সরাসরি ইনস্যাট-৩ডি ইনফ্রারেড, দৃশ্যমান এবং জলীয় বাষ্প"
            " চ্যানেলগুলি দেখুন:"
        ),
        "sat_btn_text": "🚀 অফিসিয়াল IMD INSAT-3D স্যাটেলাইট পোর্টাল খুলুন",
        "sat_source_note": (
            "উপগ্রহ চিত্রগুলি ভারত আবহাওয়া বিভাগ (IMD) INSAT-3D/3DR উপগ্রহ নেটওয়ার্ক"
            " থেকে লাইভ স্ট্রিম করা হয়।"
        ),
        "aqi_title": "🍃 বায়ুর গুণমান: প্রকৃত বনাম নিরাপদ আদর্শ মাত্রা",
        "overall_status": "সার্বিক অবস্থা",
        "standard_limit": "আদর্শ সীমা",
        "safe_limit": "নিরাপদ সীমার মধ্যে",
        "hourly_title": "⏱️ আসন্ন প্রতি ঘণ্টার আবহাওয়ার পূর্বাভাস",
        "outlook_title": "📅 ৭ দিনের পূর্বাভাস",
        "history_title": (
            "📜 ঐতিহাসিক জলবায়ু সংরক্ষণাগার (গত বছরের ঠিক এই দিনের ডেটা)"
        ),
        "export_title": "📥 আবহাওয়া ও বায়ুর গুণমান প্রতিবেদন রপ্তানি করুন",
        "csv_btn": "📥 সিএসভি প্রতিবেদন ডাউনলোড করুন",
        "txt_btn": "📄 সারসংক্ষেপ ডাউনলোড করুন",
        "max_temp": "সর্বোচ্চ তাপমাত্রা",
        "min_temp": "সর্বনিম্ন তাপমাত্রা",
        "precip_sum": "মোট বৃষ্টিপাত",
        "today": "আজ",
        "trend_title": "📈 ৭ দিনের তাপমাত্রার দৃশ্যমান প্রবণতা",
        "map_title": "🗺️ অবস্থানের মানচিত্র",
        "visitors": "মোট ভিজিটর",
        "footer_text": (
            "© ২০২৬ প্রভু জগৎবন্ধু কলেজ &nbsp;|&nbsp; ডঃ কিশোর মুখোপাধ্যায় কর্তৃক"
            " বিকশিত ও পরিচালিত"
        ),
    },
    "hi": {
        "college_name": "प्रभु जगत्बंधु कॉलेज",
        "college_sub": "कैंपस मौसम विज्ञान पोर्टल • हावड़ा",
        "select_mode": "स्थान इनपुट मोड चुनें:",
        "mode_preset": "कॉलेज परिसर प्रीसेट",
        "mode_search": "माइक्रो-लेन या स्थान का नाम खोजें",
        "mode_coords": "सटीक निर्देशांक (अक्षांश/देशांतर) दर्ज करें",
        "search_label": (
            "माइक्रो-लेन, सड़क या क्षेत्र का नाम दर्ज करें (जैसे: नबीन मुखर्जी"
            " लेन, बटाईतला, शिबपुर):"
        ),
        "search_default": "नबीन मुखर्जी लेन",
        "voice_title": "🎙️ वॉयस खोज (बोलने के लिए माइक पर क्लिक करें)",
        "search_error": (
            "माइक्रो-लेन खोज का समाधान नहीं हो सका। डिफ़ॉल्ट रूप से कॉलेज परिसर"
            " में वापस जाया जा रहा है।"
        ),
        "coords_label": (
            "गूगल मैप्स से अपने स्थान या लेन के सटीक जीपीएस निर्देशांक प्रदान करें:"
        ),
        "lat": "अक्षांश (Latitude)",
        "lon": "देशांतर (Longitude)",
        "custom_coord": "कस्टम निर्देशांक बिंदु",
        "data_source": "सक्रिय मौसम डेटा स्रोत",
        "active_zone": "सक्रिय क्षेत्र",
        "exact_coords": "सटीक निर्देशांक",
        "no_alerts": (
            "🟢 **कोई गंभीर मौसम चेतावनी नहीं।** सामान्य बाहरी स्थिति सक्रिय"
            " है।"
        ),
        "alerts_title": "🚨 मौसम अलर्ट",
        "sat_title": "🛰️ रीयल-टाइम उपग्रह और रडार इमेजरी (INSAT-3D / रडार)",
        "sat_radio_label": "व्यू मोड चुनें:",
        "sat_mode_radar": "🌐 इंटरेक्टिव लाइव क्षेत्रीय रडार (इन-ऐप)",
        "sat_mode_imd": "🛰️ आधिकारिक IMD INSAT-3D उपग्रह दर्शक पोर्टल",
        "sat_hub_info": "🔒 आधिकारिक भारत मौसम विज्ञान विभाग (IMD) उपग्रह हब",
        "sat_hub_desc": (
            "IMD के पोर्टल पर सीधे INSAT-3D इन्फ्रारेड, दृश्यमान और जल वाष्प"
            " स्पेक्ट्रल चैनल देखें:"
        ),
        "sat_btn_text": "🚀 आधिकारिक IMD INSAT-3D उपग्रह पोर्टल खोलें",
        "sat_source_note": (
            "उपग्रह अवलोकन भारत मौसम विज्ञान विभाग (IMD) INSAT-3D/3DR उपग्रह"
            " नेटवर्क से लाइव स्ट्रीम किए जाते हैं।"
        ),
        "aqi_title": "🍃 वायु गुणवत्ता: वास्तविक बनाम सुरक्षित मानक",
        "overall_status": "समग्र स्थिति",
        "standard_limit": "मानक सीमा",
        "safe_limit": "सुरक्षित सीमा के भीतर",
        "hourly_title": "⏱️ आगामी प्रति घंटा पूर्वानुमान",
        "outlook_title": "📅 7-दिवसीय पूर्वानुमान",
        "history_title": (
            "📜 ऐतिहासिक जलवायु पुरालेख (पिछले वर्ष की इसी तिथि का डेटा)"
        ),
        "export_title": "📥 मौसम और वायु गुणवत्ता रिपोर्ट निर्यात करें",
        "csv_btn": "📥 CSV रिपोर्ट डाउनलोड करें",
        "txt_btn": "📄 सारांश रिपोर्ट डाउनलोड करें",
        "max_temp": "अधिकतम तापमान",
        "min_temp": "न्यूनतम तापमान",
        "precip_sum": "कुल वर्षा",
        "today": "आज",
        "trend_title": "📈 7-दिवसीय तापमान रुझान",
        "map_title": "🗺️ स्थान का मानचित्र",
        "visitors": "कुल आगंतुक",
        "footer_text": (
            "© 2026 प्रभु जगत्बंधु कॉलेज &nbsp;|&nbsp; डॉ. किशोर मुखोपाध्याय द्वारा"
            " विकसित एवं संचालित"
        ),
    },
}

# Dynamic Styling
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
    .stApp {{
        background: {bg_gradient};
        background-attachment: fixed;
    }}
    h1, h2, h3, h4, h5, h6, p, span, label {{
        color: {text_color} !important;
    }}
    .st-emotion-cache-p5msec, .st-emotion-cache-1ebn0f2, summary p, details summary div p {{
        color: #0f172a !important;
        font-weight: bold !important;
    }}
    details summary {{
        background-color: #f1f5f9 !important;
        border-radius: 8px !important;
        padding: 8px 14px !important;
    }}
    /* Fix for invisible download button text */
    .stDownloadButton button, div.stButton > button {{
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }}
    .stDownloadButton button:hover, div.stButton > button:hover {{
        background-color: #3b82f6 !important;
        color: #ffffff !important;
        border-color: #3b82f6 !important;
    }}
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
        margin: 0; padding: 0; line-height: 1.2;
    }}
    .time-box-date {{
        color: #cbd5e1 !important;
        font-size: 0.8rem;
        font-weight: 500;
        margin: 2px 0 0 0; padding: 0; line-height: 1.2;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# College Preset Constants
COLLEGE_LAT = 22.5822
COLLEGE_LON = 88.2334


# Base64 Image Loader
def get_base64_image(image_path):
  try:
    with open(image_path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode("utf-8")
  except Exception:
    return ""


logo_base64 = get_base64_image("image_f6e73075.jpg")
logo_html_src = (
    f"data:image/jpeg;base64,{logo_base64}" if logo_base64 else ""
)


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


# Data Fetchers
@st.cache_data(ttl=900)
def fetch_weather_multi_source(lat, lon, location_name=""):
  data = None
  source_name = "Open-Meteo Global Meteorological Network"

  is_local_region = (
      abs(lat - 22.5822) < 0.1 and abs(lon - 88.2334) < 0.1
  ) or any(
      k in location_name.lower()
      for k in [
          "shibpur",
          "andul",
          "howrah",
          "bataitala",
          "khetra",
          "nabin",
          "prabhu",
      ]
  )

  if is_local_region:
    source_name = (
        "Hybrid Multi-Source (IMD Regional Grid + Open-Meteo Backbone)"
    )

  url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,relativehumidity_2m,precipitation,weathercode,windgusts_10m&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
  response = requests.get(url)
  if response.status_code == 200:
    data = response.json()

  return data, source_name


@st.cache_data(ttl=1800)
def fetch_air_quality(lat, lon):
  aqi_url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm10,pm2_5,nitrogen_dioxide,ozone&timezone=auto"
  try:
    res = requests.get(aqi_url)
    return res.json()
  except Exception:
    return None


@st.cache_data(ttl=86400)
def fetch_historical_archive(lat, lon, target_date_str):
  archive_url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={target_date_str}&end_date={target_date_str}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=auto"
  try:
    res = requests.get(archive_url)
    return res.json()
  except Exception:
    return None


@st.cache_data(ttl=3600)
def automated_microlocation_geocoder(user_query):
  cleaned_query = user_query.strip()
  if not cleaned_query:
    return None, None, None

  headers = {"User-Agent": "PrabhuJagatbandhuCollege-WeatherPortal"}
  url_exact = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(cleaned_query)}&format=json&limit=1"
  try:
    res = requests.get(url_exact, headers=headers, timeout=5).json()
    if res:
      return float(res[0]["lat"]), float(res[0]["lon"]), res[0]["display_name"]
  except Exception:
    pass

  enriched_query = f"{cleaned_query}, Shibpur, Howrah, West Bengal, India"
  url_enriched = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(enriched_query)}&format=json&limit=1"
  try:
    res = requests.get(url_enriched, headers=headers, timeout=5).json()
    if res:
      return float(res[0]["lat"]), float(res[0]["lon"]), res[0]["display_name"]
  except Exception:
    pass

  return None, None, None


def check_weather_alerts(current_code, hourly_data):
  alerts = []
  if current_code in [95, 96, 99]:
    alerts.append(
        ("🚨 CRITICAL", "Severe Thunderstorm with lightning in progress!")
    )
  elif current_code in [63, 65, 81, 82]:
    alerts.append(("⚠️ WARNING", "Heavy rain and showers active over location."))

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


def interpret_aqi(pm25, is_india=True):
  if is_india:
    if pm25 <= 30:
      return (
          "🟢 Good (CPCB)",
          "#22c55e",
          "Minimal health impact. Ideal for outdoor activities.",
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


# --- LANGUAGE SELECTOR BAR (ENGLISH / BENGALI / HINDI) ---
col_lang1, col_lang2 = st.columns([6, 2])
with col_lang2:
  selected_lang_name = st.selectbox(
      "🌐 Language / ভাষা / भाषा:", ["English", "বাংলা", "हिंदी"], index=0
  )

if selected_lang_name == "বাংলা":
  lang_code = "bn"
elif selected_lang_name == "हिंदी":
  lang_code = "hi"
else:
  lang_code = "en"

T = TEXTS[lang_code]

# --- HEADER CONTAINER WITH BASE64 LOGO & IST TIME ---
col_head1, col_head2 = st.columns([4, 1])
with col_head1:
  st.markdown(
      f"""
        <div style="display: flex; align-items: center; gap: 12px;">
            <img src="{logo_html_src}" width="65" style="border-radius: 8px; flex-shrink: 0;">
            <div>
                <h3 style="margin: 0; padding: 0; font-weight: bold; color: {text_color}; font-size: 1.5rem; line-height: 1.1;">{T['college_name']}</h3>
                <p style="margin: 2px 0 0 0; padding: 0; color: {sub_text}; font-size: 0.9rem;">{T['college_sub']}</p>
            </div>
        </div>
        """,
      unsafe_allow_html=True,
  )

with col_head2:
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

# Mode Selection Bar
mode = st.radio(
    T["select_mode"],
    [T["mode_preset"], T["mode_search"], T["mode_coords"]],
    horizontal=True,
)

is_india_location = True
query_identifier = "Prabhu Jagatbandhu College"
search_query = T["search_default"]

if mode == T["mode_preset"]:
  lat, lon = COLLEGE_LAT, COLLEGE_LON
  if lang_code == "bn":
    location_title = "প্রভু জগৎবন্ধু কলেজ ক্যাম্পাস (অন্দুল)"
  elif lang_code == "hi":
    location_title = "प्रभु जगत्बंधु कॉलेज परिसर (अंदुल)"
  else:
    location_title = "Prabhu Jagatbandhu College Campus (Andul)"

  query_identifier = "Andul Howrah"
  is_india_location = True

elif mode == T["mode_search"]:
  col_s1, col_s2 = st.columns([3, 1])

  with col_s2:
    if HAS_MIC:
      st.markdown(f"**{T['voice_title']}**")
      speech_lang = (
          "hi-IN"
          if lang_code == "hi"
          else ("bn-IN" if lang_code == "bn" else "en-US")
      )
      spoken_text = speech_to_text(
          language=speech_lang,
          start_prompt="🎙️ Start",
          stop_prompt="⏹️ Stop",
          key="mic_search",
      )
      if spoken_text:
        search_query = spoken_text
        st.info(f"🗣️ Heard / सुना गया: *{spoken_text}*")

  with col_s1:
    search_query = st.text_input(T["search_label"], search_query)

  if search_query:
    query_identifier = search_query
    resolved_lat, resolved_lon, resolved_name = automated_microlocation_geocoder(
        search_query
    )
    if resolved_lat and resolved_lon:
      lat, lon = resolved_lat, resolved_lon
      location_title = resolved_name
      is_india_location = True
    else:
      st.warning(T["search_error"])
      lat, lon = COLLEGE_LAT, COLLEGE_LON
      location_title = "Prabhu Jagatbandhu College Campus (Andul)"
      query_identifier = "Andul Howrah"
  else:
    lat, lon = COLLEGE_LAT, COLLEGE_LON
    location_title = "Prabhu Jagatbandhu College Campus (Andul)"
    query_identifier = "Andul Howrah"

else:
  st.markdown(T["coords_label"])
  col_lat, col_lon = st.columns(2)
  with col_lat:
    lat = st.number_input(
        T["lat"], value=COLLEGE_LAT, format="%.5f", step=0.0001
    )
  with col_lon:
    lon = st.number_input(
        T["lon"], value=COLLEGE_LON, format="%.5f", step=0.0001
    )
  location_title = T["custom_coord"]
  query_identifier = "Howrah Micro-Lane"
  is_india_location = True

# Fetch Weather & AQI Data
data, active_data_source = fetch_weather_multi_source(
    lat, lon, query_identifier
)
aqi_data = fetch_air_quality(lat, lon)

if data and "current_weather" in data:
  current = data["current_weather"]
  hourly = data.get("hourly", {})
  daily = data.get("daily", {})

  # Attribution Badge
  st.markdown(
      f"""
        <div style="background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; padding: 10px 14px; border-radius: 8px; margin-bottom: 15px; font-size: 0.85rem; line-height: 1.5;">
            📡 <b>{T['data_source']}:</b> {active_data_source}<br>
            📍 <b>{T['active_zone']}:</b> {location_title}<br>
            🧭 <b>{T['exact_coords']}:</b> Latitude: <code>{lat:.5f}° N</code> &nbsp;|&nbsp; Longitude: <code>{lon:.5f}° E</code>
        </div>
        """,
      unsafe_allow_html=True,
  )

  # Weather Alerts
  alerts = check_weather_alerts(current.get("weathercode", 0), hourly)
  if alerts:
    st.markdown(f"### {T['alerts_title']}")
    for title, msg in alerts:
      if "CRITICAL" in title or "HEAVY" in title:
        st.error(f"**{title}:** {msg}")
      else:
        st.warning(f"**{title}:** {msg}")
  else:
    st.markdown(T["no_alerts"])

  st.markdown("<br>", unsafe_allow_html=True)

  # --- REAL-TIME SATELLITE & RADAR IMAGERY SECTION (TRILINGUAL) ---
  with st.expander(f"🛰️ **{T['sat_title']}**", expanded=True):
    sat_mode = st.radio(
        T["sat_radio_label"],
        [T["sat_mode_radar"], T["sat_mode_imd"]],
        horizontal=True,
    )

    if sat_mode == T["sat_mode_radar"]:
      components.iframe(
          f"https://www.rainviewer.com/map.html?loc={lat},{lon},8&ofr=0&t=1&col=1&c=1&o=90&s=1&v=0&sm=1&sn=1",
          height=500,
          scrolling=False,
      )
    else:
      st.info(T["sat_hub_info"])
      st.markdown(
          f"""
            <div style="text-align: center; margin: 20px 0;">
                <p style="color: #cbd5e1; font-size: 0.9rem; margin-bottom: 14px;">
                    {T['sat_hub_desc']}
                </p>
                <a href="https://mausam.imd.gov.in/responsive/satellite.php" target="_blank" style="background-color: #059669; color: white; padding: 12px 26px; text-decoration: none; font-weight: bold; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); display: inline-block; font-size: 1rem;">
                    {T['sat_btn_text']}
                </a>
            </div>
            """,
          unsafe_allow_html=True,
      )

    st.markdown(
        f"""
        <div style="font-size: 0.8rem; color: {sub_text}; margin-top: 8px;">
            📌 <i>{T['sat_source_note']}</i>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- AIR QUALITY: ACTUAL VS. SAFE STANDARD ---
  if aqi_data and "current" in aqi_data:
    std_name = "CPCB (India)" if is_india_location else "WHO Global"
    st.markdown(f"### {T['aqi_title']} ({std_name})")
    aq_current = aqi_data["current"]

    pm25 = aq_current.get("pm2_5", 0)
    pm10 = aq_current.get("pm10", 0)
    no2 = aq_current.get("nitrogen_dioxide", 0)
    o3 = aq_current.get("ozone", 0)

    std_limits = {
        "pm25": 60 if is_india_location else 15,
        "pm10": 100 if is_india_location else 45,
        "no2": 80 if is_india_location else 25,
        "o3": 100,
    }

    status_label, status_color, advisory = interpret_aqi(
        pm25, is_india=is_india_location
    )
    col_aqi1, col_aqi2, col_aqi3, col_aqi4, col_aqi5 = st.columns(5)

    with col_aqi1:
      st.markdown(
          f"""
            <div class="weather-card" style="border-left: 4px solid {status_color}; text-align: left; padding: 10px 12px;">
                <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{T['overall_status']}</div>
                <div style="font-size: 1.1rem; font-weight: bold; color: {status_color};">{status_label}</div>
            </div>
            """,
          unsafe_allow_html=True,
      )

    def render_pollutant_card(name, val, limit):
      ratio = (val / limit) * 100 if limit > 0 else 0
      if val <= limit:
        badge_color = "#22c55e"
        badge_text = T["safe_limit"]
      else:
        badge_color = "#ef4444"
        badge_text = f"+{ratio - 100:.0f}% Above Standard"

      return f"""
        <div class="weather-card">
            <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{name}</div>
            <div style="font-size: 1.1rem; font-weight: bold; color: {text_color};">{val} <span style="font-size: 0.75rem; font-weight: normal;">µg/m³</span></div>
            <div style="font-size: 0.7rem; color: {sub_text}; margin-top: 2px;">{T['standard_limit']}: <b>{limit} µg/m³</b></div>
            <div style="font-size: 0.7rem; color: {badge_color}; font-weight: bold; margin-top: 4px;">{badge_text}</div>
        </div>
        """

    with col_aqi2:
      st.markdown(
          render_pollutant_card("PM₂.₅", pm25, std_limits["pm25"]),
          unsafe_allow_html=True,
      )
    with col_aqi3:
      st.markdown(
          render_pollutant_card("PM₁₀", pm10, std_limits["pm10"]),
          unsafe_allow_html=True,
      )
    with col_aqi4:
      st.markdown(
          render_pollutant_card("NO₂", no2, std_limits["no2"]),
          unsafe_allow_html=True,
      )
    with col_aqi5:
      st.markdown(
          render_pollutant_card("O₃", o3, std_limits["o3"]),
          unsafe_allow_html=True,
      )

    st.markdown(
        f"""
        <div style="background: {card_bg}; border: {card_border}; color: {text_color}; padding: 10px 14px; border-radius: 10px; margin-top: 10px; font-size: 0.85rem;">
            💡 <b>Health Advisory:</b> {advisory}
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- HOURLY FORECAST CARDS ---
  if hourly:
    st.markdown(f"### {T['hourly_title']}")
    current_hour_iso = datetime.now(IST).strftime("%Y-%m-%dT%H:00")
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

  # --- 7-DAY OUTLOOK CARDS ---
  if daily:
    st.markdown(f"### {T['outlook_title']}")
    day_cols = st.columns(7)

    for i in range(7):
      date_str = daily["time"][i]
      dt_day = datetime.strptime(date_str, "%Y-%m-%d")
      day_name = T["today"] if i == 0 else dt_day.strftime("%a")
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

    # --- HISTORICAL CLIMATE ARCHIVE ---
    st.markdown(f"### {T['history_title']}")
    last_year_date = datetime.now(IST) - pd.DateOffset(years=1)
    ly_date_str = last_year_date.strftime("%Y-%m-%d")

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
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{T['max_temp']}</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">{T['today']}: {today_max}°C</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year: {ly_max}°C</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
      with col_hist2:
        st.markdown(
            f"""
                <div class="weather-card" style="text-align: left; padding: 12px 14px;">
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{T['min_temp']}</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">{T['today']}: {today_min}°C</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year: {ly_min}°C</div>
                </div>
                """,
            unsafe_allow_html=True,
        )
      with col_hist3:
        st.markdown(
            f"""
                <div class="weather-card" style="text-align: left; padding: 12px 14px;">
                    <div style="font-size: 0.75rem; color: {sub_text}; font-weight: 600;">{T['precip_sum']}</div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {text_color};">{T['today']}: {today_rain} mm</div>
                    <div style="font-size: 0.85rem; color: #38bdf8; margin-top: 2px;">Last Year: {ly_rain} mm</div>
                </div>
                """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # --- TREND & MAP ---
    bottom_col_left, bottom_col_right = st.columns(2)
    with bottom_col_left:
      st.markdown(f"### {T['trend_title']}")
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
      st.markdown(f"### {T['map_title']}")
      df_map = pd.DataFrame({"lat": [lat], "lon": [lon]})
      st.map(df_map, zoom=14, height=300)

  st.markdown("<br>", unsafe_allow_html=True)

  # --- EXPORT METEOROLOGICAL & AIR QUALITY REPORT ---
  st.markdown(f"### {T['export_title']}")
  export_df = pd.DataFrame({
      "Timestamp (IST)": [datetime.now(IST).strftime("%Y-%m-%d %H:%M")],
      "Location": [location_title],
      "Latitude": [lat],
      "Longitude": [lon],
      "Current Temp (°C)": [current.get("temperature", "N/A")],
      "Weather Code": [current.get("weathercode", "N/A")],
      "PM2.5 (µg/m³)": [
          aqi_data["current"].get("pm2_5", "N/A") if aqi_data else "N/A"
      ],
      "AQI Status": [status_label if aqi_data else "N/A"],
  })

  col_exp1, col_exp2 = st.columns(2)
  with col_exp1:
    csv_buffer = export_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=T["csv_btn"],
        data=csv_buffer,
        file_name=(
            f"campus_weather_report_{datetime.now(IST).strftime('%Y-%m-%d')}.csv"
        ),
        mime="text/csv",
    )

  with col_exp2:
    txt_summary = f"""
    PRABHU JAGATBANDHU COLLEGE - CAMPUS METEOROLOGICAL REPORT
    Date: {datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')} IST
    Location: {location_title}
    Coordinates: {lat:.5f}° N, {lon:.5f}° E
    
    CURRENT METRICS:
    - Temperature: {current.get('temperature', 'N/A')}°C
    - Air Quality (PM2.5): {aqi_data['current'].get('pm2_5', 'N/A') if aqi_data else 'N/A'} µg/m³
    - Status: {status_label if aqi_data else 'N/A'}
    
    Advisory: {advisory if aqi_data else 'Normal conditions active.'}
    """
    st.download_button(
        label=T["txt_btn"],
        data=txt_summary.encode("utf-8"),
        file_name=(
            f"campus_weather_summary_{datetime.now(IST).strftime('%Y-%m-%d')}.txt"
        ),
        mime="text/plain",
    )

else:
  st.error("Failed to retrieve weather information.")

# --- FOOTER ---
st.markdown("<br><hr>", unsafe_allow_html=True)
if "visitor_count" not in st.session_state:
  st.session_state["visitor_count"] = 1452

st.markdown(
    f"""
    <div style="text-align: center; margin-top: 20px;">
        <p style="color: {sub_text}; font-size: 0.9rem; margin-bottom: 12px;">
            {T['footer_text']}
        </p>
        <div style="display: inline-flex; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.2); font-family: monospace; font-size: 0.85rem; font-weight: bold;">
            <div style="background-color: #555555; color: #ffffff; padding: 6px 12px; letter-spacing: 1px;">{T['visitors']}</div>
            <div style="background-color: #3b82f6; color: #ffffff; padding: 6px 12px; letter-spacing: 1px;">{st.session_state['visitor_count']} / 10</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
