import streamlit as st
import requests
import time
import folium
import pandas as pd
from datetime import datetime, timezone
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderUnavailable

# Streamlit setup
st.set_page_config(page_title="ISS Real-Time Tracker", layout="centered")
st.title("Real-Time ISS Tracker")
st.markdown("Display of the current position of the International Space Station (ISS).")

# Slider for refresh rate
refresh_rate = st.slider("Refresh interval (seconds)", 5, 60, 10)

# Initialize geocoder (only once)
geolocator = Nominatim(user_agent="iss_tracker_app")

# Session state: store previous positions
if 'position_log' not in st.session_state:
    st.session_state.position_log = []

# --- Function to Get Current ISS Position + Location Name ---
def get_iss_position():
    url = "https://api.wheretheiss.at/v1/satellites/25544"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        latitude = data['latitude']
        longitude = data['longitude']
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Try reverse geocoding
        try:
            location = geolocator.reverse((latitude, longitude), language='en', timeout=5)
            location_name = location.address if location else "Over Ocean or Unknown"
        except GeocoderUnavailable:
            location_name = "Geocoder Offline"
        except Exception:
            location_name = "Lookup Failed"

        return {
            "timestamp": timestamp,
            "latitude": latitude,
            "longitude": longitude,
            "location": location_name
        }

    except Exception as e:
        print("!!!! API Error:", e)
        return None

# --- Get and log position ---
position = get_iss_position()

if position:
    # Append and limit to last 10
    st.session_state.position_log.append(position)
    st.session_state.position_log = st.session_state.position_log[-10:]

    # Create folium map
    m = folium.Map(
    location=[position["latitude"], position["longitude"]],
    zoom_start=2,
    tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
    attr="© OpenStreetMap, © CARTO"
)

    # Add ISS marker
    folium.Marker(
        location=[position["latitude"], position["longitude"]],
        tooltip=f"ISS \n{position['timestamp']}",
        popup=position['location'],
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(m)

    # Draw trail (polyline)
    trail_points = [[p["latitude"], p["longitude"]] for p in st.session_state.position_log]
    folium.PolyLine(trail_points, color="red", weight=2.5, opacity=0.8, tooltip="ISS Trail").add_to(m)

    # Show map
    st_folium(m, width=1000, height=500)

    # Show table
    st.subheader("Last 10 Positions (UTC)")
    df = pd.DataFrame(st.session_state.position_log)[::-1]  # latest first
    st.table(df)

else:
    st.error("Could not fetch ISS data. Check your internet connection.")

# --- Auto-refresh the app ---
time.sleep(refresh_rate)
st.rerun()
