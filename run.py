# import subprocess
# import time
# import logging
# import requests
# from requests.auth import HTTPBasicAuth

# # Initialize logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# def run_uvicorn():
#     """Run the FastAPI app."""
#     try:
#         logger.info("Starting Uvicorn...")
#         uvicorn_process = subprocess.Popen(
#             ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#         )
#         uvicorn_process.wait()
#     except Exception as e:
#         logger.error("Failed to start Uvicorn: %s", e)

# # def run_ngrok():
# #     """Run ngrok."""
# #     try:
# #         time.sleep(15)  # Wait for Uvicorn to initialize
# #         logger.info("Starting Ngrok...")
# #         ngrok_process = subprocess.Popen(
# #             ["ngrok", "start", "static-tunnel", "--config", "C:/Users/projectadmin/.ngrok2/ngrok.yml"]
# #         )
# #         ngrok_process.wait()
# #     except Exception as e:
# #         logger.error("Failed to start Ngrok: %s", e)

# def run_ngrok():
#     """Run ngrok."""
#     try:
#         # Allow some time for Uvicorn to initialize
#         time.sleep(15)
#         logger.info("Starting Ngrok...")
#         ngrok_process = subprocess.Popen(
#             ["ngrok", "start", "static-tunnel", "--config", "C:/Users/projectadmin/.ngrok2/ngrok.yml"]
#         )
#         logger.info("Ngrok started with PID: %s", ngrok_process.pid)

#         # Keep fetching the public URL until the ngrok process terminates
#         while ngrok_process.poll() is None:
#             try:
#                 response = requests.get("http://127.0.0.1:4040/api/tunnels", 
#                                         timeout=5, 
#                                         auth=HTTPBasicAuth('admin', 'glokale1')  # Adding Basic Auth in the request
#                 )
#                 response.raise_for_status()
#                 tunnels = response.json()["tunnels"]
#                 public_url = tunnels[0]["public_url"]
#                 logger.info(f"Ngrok Public URL: {public_url} (Ctrl+Click to open in browser)")
#             except Exception as e:
#                 logger.error("Failed to fetch Ngrok URL: %s", e)
#             time.sleep(10)  # Refresh every 10 seconds

#         logger.info("Ngrok process terminated.")
#     except Exception as e:
#         logger.error("Failed to start Ngrok: %s", e)


# def terminate_processes(processes):
#     """Terminate all running processes gracefully."""
#     for process in processes:
#         try:
#             logger.info(f"Terminating process PID {process.pid}...")
#             process.terminate()
#         except Exception as e:
#             logger.warning(f"Failed to terminate process PID {process.pid}: {e}")

# if __name__ == "__main__":
#     uvicorn_process = None
#     ngrok_process = None
#     try:
#         # Start Uvicorn
#         uvicorn_process = subprocess.Popen(
#             ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#         )
#         logger.info("Uvicorn started with PID: %s", uvicorn_process.pid)

#         # Wait for Uvicorn to initialize
#         time.sleep(15)

#         # Start Ngrok
#         ngrok_process = subprocess.Popen(
#             ["ngrok", "start", "static-tunnel", "--config", "C:/Users/projectadmin/.ngrok2/ngrok.yml"]
#         )
#         logger.info("Ngrok started with PID: %s", ngrok_process.pid)

#         # Wait for both processes
#         uvicorn_process.wait()
#         ngrok_process.wait()

#     except KeyboardInterrupt:
#         logger.info("Keyboard interrupt received. Shutting down processes...")
#     finally:
#         terminate_processes([uvicorn_process, ngrok_process])
#         logger.info("All processes terminated.")


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
