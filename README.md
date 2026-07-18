# Pattiya Backend Simulator for Flutter Development

This Python script is designed to simulate the hardware layer of the Pattiya system (Raspberry Pi Base Station, ESP32 Smart Collars, and Methane Tower). Since the physical hardware isn't always running during app development, this simulator continuously generates realistic mock data and sends it to your backend API.

This ensures the Flutter developer can test live charts, dashboard updates, and Push Notifications without needing the physical sensors.

## Features
- **Authentication**: Automatically handles gateway login and JWT tokens.
- **Normal Data Flow**: Continuously sends normal activity, sound, and environment data.
- **Oestrus Simulation**: Periodically triggers a `LIKELY_OESTRUS` fusion event to test the heat detection UI and Push Notifications.
- **Methane Alert Simulation**: Periodically sends a session with $>600$ PPM methane to test the `HIGH_METHANE_WARNING` flow.
- **Heat Stress Simulation**: Occasionally spikes the temperature and humidity to test the THI alerts.

## Requirements
- Python 3.7+
- `requests` library

## Setup & Running

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Backend URL:**
   Open `simulator.py` and ensure the `BACKEND_URL` is pointing to the correct API server (local or deployed). Also ensure `GATEWAY_ID` and `HARDWARE_SECRET` match a valid gateway in your MongoDB database.
   ```python
   BACKEND_URL = "http://localhost:5000/api/v1" 
   ```

3. **Run the Simulator:**
   ```bash
   python simulator.py
   ```

The script will loop infinitely, generating new data every 60 seconds. Press `Ctrl+C` to stop it.
