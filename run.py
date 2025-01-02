import subprocess
import time
import logging
import requests
import psutil
from threading import Thread

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variable for ngrok public URL
ngrok_public_url = None

# Function to kill existing ngrok processes
def kill_ngrok_processes():
    """Kill any existing ngrok processes to avoid conflicts."""
    for process in psutil.process_iter(['pid', 'name']):
        try:
            if process.info['name'] == 'ngrok.exe':
                logger.info(f"Killing ngrok process: PID {process.info['pid']}")
                process.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

# Function to start ngrok
def start_ngrok():
    """Start ngrok and retrieve the public URL."""
    global ngrok_public_url

    # Kill existing ngrok processes
    kill_ngrok_processes()

    # Start ngrok process
    ngrok_config_path = r"C:\Users\projectadmin\.ngrok2\ngrok.yml"
    command = f"ngrok start static-tunnel --config={ngrok_config_path}"
    subprocess.Popen(command, shell=True)
    time.sleep(3)  # Reduced wait time for faster initialization

    # Retrieve ngrok public URL
    url = "http://127.0.0.1:4040/api/tunnels"
    retries = 1
    while retries > 0:
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            tunnels = response.json()["tunnels"]
            ngrok_public_url = tunnels[0]["public_url"]
            logger.info(f"ngrok public URL: {ngrok_public_url}")
            return
        except Exception as e:
            logger.error(f"Error retrieving ngrok URL: {e}")
            retries -= 1
            time.sleep(1)  # Reduced retry delay for faster response

    logger.error("Failed to retrieve ngrok URL after multiple retries.")

# Function to run Uvicorn
def run_uvicorn():
    """Run the FastAPI app with Uvicorn."""
    subprocess.run(["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"])

if __name__ == "__main__":
    uvicorn_thread = Thread(target=run_uvicorn)
    uvicorn_thread.start()

    # Wait for FastAPI app to initialize
    time.sleep(2)  # for faster response

    # Start ngrok tunnel
    start_ngrok()

    # Wait for Uvicorn thread to complete
    uvicorn_thread.join()
