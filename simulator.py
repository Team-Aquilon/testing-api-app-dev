import time
import random
import requests
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ==========================================
# CONFIGURATION
# ==========================================
# Backend API URL - Change this to your local or deployed backend URL
BACKEND_URL = "https://pattiya-backend-v1.vercel.app/api/v1" 
# Note: If the backend is deployed, use the deployed URL (e.g., https://pattiya-backend.onrender.com/api/v1)

GATEWAY_ID = "GW_001"
HARDWARE_SECRET = "gw_secret_ridiyagama_001" # Must match the backend DB

COWS = [
    {"cow_id": "COW_101", "mac": "A4:CF:12:89:C3:D1", "name": "Kalu"},
    {"cow_id": "COW_102", "mac": "A4:CF:12:89:C3:D2", "name": "Suddi"},
    {"cow_id": "COW_103", "mac": "A4:CF:12:89:C3:D3", "name": "Raththi"}
]

# Time to wait between simulation cycles (in seconds)
# Set to 60-120 seconds as requested
CYCLE_DELAY = 60 

# ==========================================
# HTTP CLIENT WITH AUTHENTICATION
# ==========================================
class BackendClient:
    def __init__(self, base_url, gateway_id, secret):
        self.base_url = base_url.rstrip('/')
        self.gateway_id = gateway_id
        self.secret = secret
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None

    def login(self):
        url = f"{self.base_url}/gateway/auth/login"
        body = {"gateway_id": self.gateway_id, "hardware_secret": self.secret}
        logging.info(f"Logging in to {url}...")
        try:
            resp = self.session.post(url, json=body, timeout=30)
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                self.token = data.get("gateway_access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logging.info("Login successful. Token acquired.")
                return True
            else:
                logging.error(f"Login failed: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logging.error(f"Login error: {e}")
            return False

    def post(self, endpoint, payload):
        if not self.token:
            if not self.login():
                return
        
        url = f"{self.base_url}{endpoint}"
        try:
            resp = self.session.post(url, json=payload, timeout=30)
            if resp.status_code == 401:
                logging.warning("Token expired. Re-authenticating...")
                self.token = None
                self.post(endpoint, payload) # Retry
            elif resp.status_code >= 400:
                logging.error(f"Failed to post to {endpoint}: {resp.status_code} - {resp.text}")
            else:
                logging.info(f"Successfully posted to {endpoint}")
        except Exception as e:
            logging.error(f"Error posting to {endpoint}: {e}")

# ==========================================
# SIMULATION SCENARIOS
# ==========================================

def get_iso_time():
    return datetime.utcnow().isoformat() + "Z"

def simulate_normal_behavior(client, cow):
    """Simulates normal resting/grazing behavior for a cow."""
    logging.info(f"--- Simulating NORMAL behavior for {cow['cow_id']} ---")
    now = get_iso_time()
    
    # 1. Activity (Normal)
    client.post("/gateway/telemetry/activity-prediction", {
        "gateway_id": GATEWAY_ID,
        "cow_id": cow["cow_id"],
        "mac_address": cow["mac"],
        "timestamp": now,
        "features": {"mean_acc": 0.5, "energy_acc": 2.0},
        "predicted_activity": random.choice(["eating", "standing", "lying"]),
        "activity_state": "normal_activity",
        "confidence": round(random.uniform(0.7, 0.95), 2),
        "battery": round(random.uniform(80, 100), 1),
        "rssi_dbm": -65, "snr_db": 8.0
    })

    # 2. Sound (Normal)
    client.post("/gateway/telemetry/sound-prediction", {
        "gateway_id": GATEWAY_ID,
        "mac_address": cow["mac"],
        "timestamp": now,
        "event_start_ms": 0,
        "oestrus_probability": round(random.uniform(0.01, 0.1), 2),
        "label": "normal",
        "rssi_dbm": -65, "snr_db": 8.0
    })

    # 3. Status Heartbeat
    client.post("/gateway/telemetry/status", {
        "gateway_id": GATEWAY_ID,
        "cow_id": cow["cow_id"],
        "mac_address": cow["mac"],
        "lat": 6.14 + random.uniform(-0.001, 0.001),
        "lon": 80.12 + random.uniform(-0.001, 0.001),
        "uptime_ms": 3600000,
        "battery": round(random.uniform(80, 100), 1),
        "gps_age_ms": 500,
        "rssi_dbm": -65, "snr_db": 8.0
    })

def simulate_oestrus_alert(client, cow):
    """Simulates a cow going into heat (high activity + vocalization)."""
    logging.info(f"--- Simulating OESTRUS ALERT for {cow['cow_id']} ---")
    now = get_iso_time()
    
    # Activity (High)
    client.post("/gateway/telemetry/activity-prediction", {
        "gateway_id": GATEWAY_ID,
        "cow_id": cow["cow_id"],
        "mac_address": cow["mac"],
        "timestamp": now,
        "features": {"mean_acc": 2.5, "energy_acc": 15.0},
        "predicted_activity": "mounting",
        "activity_state": "high_activity",
        "confidence": 0.92,
        "battery": 75.0,
        "rssi_dbm": -60, "snr_db": 9.0
    })

    # Sound (Likely Oestrus)
    client.post("/gateway/telemetry/sound-prediction", {
        "gateway_id": GATEWAY_ID,
        "mac_address": cow["mac"],
        "timestamp": now,
        "event_start_ms": 12345,
        "oestrus_probability": 0.88,
        "label": "likely_oestrus",
        "rssi_dbm": -60, "snr_db": 9.0
    })

    # Fusion Decision (Triggers Notification)
    client.post("/gateway/telemetry/oestrus-fusion", {
        "gateway_id": GATEWAY_ID,
        "cow_id": cow["cow_id"],
        "mac_address": cow["mac"],
        "decision": "LIKELY_OESTRUS",
        "sound_label": "likely_oestrus",
        "sound_probability": 0.88,
        "activity_label": "mounting",
        "activity_state": "high_activity",
        "temperature_c": 28.5,
        "humidity_percent": 75.0,
        "rssi_dbm": -60, "snr_db": 9.0
    })

def simulate_methane_alert(client, cow):
    """Simulates a high methane reading from the Methane Tower."""
    logging.info(f"--- Simulating HIGH METHANE for {cow['cow_id']} ---")
    client.post("/gateway/telemetry/methane/session", {
        "gateway_id": GATEWAY_ID,
        "device_id": "methane_monitor_sim",
        "cow_id": cow["cow_id"],
        "rfid_tag": cow["cow_id"], # Usually numeric, but ID works for matching
        "session_start_time": get_iso_time(),
        "session_duration_seconds": 600,
        "valid_sample_count": 600,
        "invalid_sample_count": 0,
        "avg_delta_ch4_ppm": 650.5, # > 600 triggers alert
        "avg_airflow_lpm": 7.2,
        "avg_methane_flow_ml_min": 2.5,
        "status": "valid"
    })

def simulate_environment(client, heat_stress=False):
    """Simulates the environment sensor on the Pi."""
    temp = 35.5 if heat_stress else 28.0
    hum = 85.0 if heat_stress else 60.0
    logging.info(f"--- Simulating ENVIRONMENT (Heat Stress: {heat_stress}) ---")
    
    client.post("/gateway/telemetry/environment", {
        "gateway_id": GATEWAY_ID,
        "timestamp": get_iso_time(),
        "uptime_ms": 3600000,
        "temperature_c": temp,
        "humidity_percent": hum,
        "valid": True
    })

# ==========================================
# MAIN LOOP
# ==========================================
if __name__ == "__main__":
    logging.info("Starting Pattiya Backend Simulator for Flutter App Development")
    logging.info(f"Target URL: {BACKEND_URL}")
    logging.info("Press Ctrl+C to stop.")
    
    client = BackendClient(BACKEND_URL, GATEWAY_ID, HARDWARE_SECRET)
    
    # Try logging in immediately
    if not client.login():
        logging.error("Initial login failed. Make sure your backend is running!")
        logging.error("Check BACKEND_URL, GATEWAY_ID, and HARDWARE_SECRET.")
        # We will continue anyway, the post() method will retry login automatically

    cycle = 0
    try:
        while True:
            cycle += 1
            logging.info(f"=== Starting Simulation Cycle {cycle} ===")
            
            # 1. Normal Environment (mostly) but occasionally Heat Stress
            simulate_environment(client, heat_stress=(cycle % 5 == 0))
            
            # 2. Iterate through cows
            for i, cow in enumerate(COWS):
                if cycle % 3 == 1 and i == 0:
                    # Make Cow 1 go into oestrus every 3rd cycle
                    simulate_oestrus_alert(client, cow)
                elif cycle % 4 == 2 and i == 1:
                    # Make Cow 2 have high methane every 4th cycle
                    simulate_methane_alert(client, cow)
                else:
                    # Otherwise, normal behavior
                    simulate_normal_behavior(client, cow)
            
            logging.info(f"=== Cycle {cycle} Complete. Waiting {CYCLE_DELAY} seconds... ===")
            time.sleep(CYCLE_DELAY)
            
    except KeyboardInterrupt:
        logging.info("Simulator stopped by user.")
