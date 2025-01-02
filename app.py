# from fastapi import FastAPI, HTTPException
# from pydantic import BaseModel
# import subprocess
# import json
# import uvicorn
# import requests
# import time
# import os
# import logging
# import psutil
# from threading import Lock
# from fastapi.responses import RedirectResponse


# # Initialize logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # Initialize FastAPI app
# app = FastAPI()

# # Schema for input JSON
# class Cap(BaseModel):
#     ror: float  # Ensure the type matches what you're sending
#     gas: float

# class InputJSON(BaseModel):
#     cap: Cap

# # Global variable for ngrok URL
# ngrok_public_url = None
# ngrok_lock = Lock()

# # Root endpoint for testing
# @app.get("/")
# def redirect_to_docs():
#     return RedirectResponse(url="/docs")

# def read_root():
#     return {"message": "GAMSPy Model API is running!"}

# # Endpoint to run the GAMSPy model
# @app.post("/run-model")
# def run_model(input_json: InputJSON):
#     try:
#         # Ensure correct working directory
#         working_dir = "D:/glocal_energy_transition"
#         os.chdir(working_dir)
#         logger.info("Current Working Directory: %s", os.getcwd())
#         logger.info("Python Executable: D:/glocal_energy_transition/fastapi_env/Scripts/python.exe")
#         logger.info("Main.py Path Exists: %s", os.path.exists("main.py"))

#         # Save input JSON to a temporary file
#         with open("input.json", "w") as f:
#             json.dump(input_json.dict(), f)
#             logger.info("Saved input JSON: %s", input_json.dict())

#         # Execute the GAMSPy script as a subprocess
#         process = subprocess.run(
#             ["D:/glocal_energy_transition/fastapi_env/Scripts/python.exe", "main.py"],
#             env=os.environ,
#             capture_output=True,
#             text=True,
#             timeout=90,  # Timeout in seconds
#         )

#         # Debugging logs
#         logger.info("Process Raw Output: %s", process.stdout)
#         logger.error("Process Error Output: %s", process.stderr)

#         # Check if the script ran successfully
#         if process.returncode != 0:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Error running GAMSPy script: {process.stderr}",
#             )

#         # Parse the JSON output
#         output_json = None
#         for line in process.stdout.splitlines():
#             try:
#                 output_json = json.loads(line)
#                 break
#             except json.JSONDecodeError:
#                 continue

#         if not output_json:
#             raise HTTPException(
#                 status_code=500, detail="No valid JSON output found in script output."
#             )

#         return {"status": "success", "output": output_json}

#     except subprocess.TimeoutExpired as e:
#         logger.error("Subprocess execution timed out: %s", e)
#         raise HTTPException(status_code=504, detail="main.py execution timed out.")

#     except Exception as e:
#         logger.error("Exception occurred: %s", e)
#         raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

#     finally:
#         # Cleanup input.json
#         try:
#             if os.path.exists("input.json"):
#                 os.remove("input.json")
#                 logger.info("input.json file removed.")
#         except Exception as e:
#             logger.warning("Failed to remove input.json: %s", e)

# # Function to kill existing ngrok processes
# def kill_ngrok_processes():
#     """Kill any existing ngrok processes to avoid conflicts."""
#     with ngrok_lock:
#         for process in psutil.process_iter(['pid', 'name']):
#             try:
#                 if process.info['name'] == 'ngrok.exe':  # Change to 'ngrok' for Linux/MacOS
#                     logger.info(f"Killing ngrok process: PID {process.info['pid']}")
#                     process.terminate()
#             except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#                 pass

# def start_ngrok():
#     """Start ngrok after ensuring no conflicting processes."""
#     global ngrok_public_url

#     # Kill existing ngrok processes
#     kill_ngrok_processes()

#     # Start ngrok
#     ngrok_config_path = r"C:\Users\projectadmin\.ngrok2\ngrok.yml"
#     command = f"ngrok start static-tunnel --config={ngrok_config_path}"
#     subprocess.Popen(command, shell=True)
#     time.sleep(5)
#     logger.info("ngrok started")

#     # Retry fetching the ngrok public URL
#     url = "http://127.0.0.1:4040/api/tunnels"
#     retries = 5
#     while retries > 0:
#         try:
#             response = requests.get(url, timeout=5)
#             response.raise_for_status()  # Raise an error if the response is not 200
#             tunnels = response.json()["tunnels"]
#             ngrok_public_url = tunnels[0]["public_url"]
#             logger.info("ngrok public URL: %s", ngrok_public_url)
#             return
#         except Exception as e:
#             logger.error("Error retrieving ngrok URL: %s", e)
#             retries -= 1
#             time.sleep(2)  # Wait before retrying

#     logger.error("Failed to retrieve ngrok URL after multiple retries.")


# # # Endpoint to retrieve the ngrok public URL
# # @app.get("/ngrok-url")
# # def get_ngrok_url():
# #     if ngrok_public_url:
# #         return {"ngrok_public_url": ngrok_public_url}
# #     else:
# #         raise HTTPException(status_code=404, detail="ngrok URL not available.")

# # Main script
# if __name__ == "__main__":
#     import threading

#     def run_uvicorn():
#         uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

#     # Start FastAPI app in a separate thread
#     uvicorn_thread = threading.Thread(target=run_uvicorn)
#     uvicorn_thread.start()

#     # Wait for FastAPI app to start
#     time.sleep(3)

#     # Start ngrok
#     start_ngrok()

#     # Wait for uvicorn thread to finish
#     uvicorn_thread.join()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
import os
import logging
import requests
from fastapi.responses import RedirectResponse
from typing import Any

app: Any = FastAPI()

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Schema for input JSON
class Cap(BaseModel):
    ror: float
    gas: float

class InputJSON(BaseModel):
    cap: Cap

# Global variable for ngrok URL
ngrok_public_url = None

@app.on_event("startup")
def app_startup():
    """Perform startup tasks, including retrieving Ngrok public URL."""
    global ngrok_public_url
    logger.info("Running application startup tasks...")

    # Fetch the Ngrok public URL
    ngrok_api_url = "http://127.0.0.1:4040/api/tunnels"
    try:
        response = requests.get(ngrok_api_url, timeout=5)
        response.raise_for_status()
        tunnels = response.json().get("tunnels", [])
        if tunnels:
            ngrok_public_url = tunnels[0]["public_url"]
            logger.info(f"Forwarding: http://localhost:8000 -> {ngrok_public_url}")
            print(f"Static URL (Ngrok): {ngrok_public_url} (Ctrl+Click to open in browser)")
        else:
            logger.warning("No tunnels found. Ensure Ngrok is running.")
    except Exception as e:
        logger.error(f"Failed to retrieve Ngrok URL: {e}")
        print("Ngrok static URL not available. Ensure ngrok is running.")

@app.get("/")
def redirect_to_docs():
    """Redirect to Swagger UI for client convenience."""
    return RedirectResponse(url="/docs")

# define endpoint

@app.get("/ngrok-url")
def get_ngrok_url():
    """Retrieve the Ngrok public URL."""
    if ngrok_public_url:
        return {"ngrok_public_url": ngrok_public_url}
    else:
        raise HTTPException(status_code=404, detail="Ngrok URL not available.")

@app.post("/run-model")
def run_model(input_json: InputJSON):
    """Endpoint to execute the GAMSPy model."""
    try:
        # Save input JSON to a temporary file
        working_dir = "D:/glocal_energy_transition"
        os.chdir(working_dir)
        with open("input.json", "w") as f:
            json.dump(input_json.dict(), f)

        # Execute the GAMSPy script as a subprocess
        process = subprocess.run(
            ["D:/glocal_energy_transition/fastapi_env/Scripts/python.exe", "main.py"],
            env=os.environ,
            capture_output=True,
            text=True,
            timeout=90,
        )

        # Check if the script ran successfully
        if process.returncode != 0:
            raise HTTPException(
                status_code=500, detail=f"Error running GAMSPy script: {process.stderr}"
            )

        # Parse the JSON output
        output_json = None
        for line in process.stdout.splitlines():
            try:
                output_json = json.loads(line)
                break
            except json.JSONDecodeError:
                continue

        if not output_json:
            raise HTTPException(
                status_code=500, detail="No valid JSON output found in script output."
            )

        # Skip Ngrok warning by adding the header
        static_url = "https://gradually-nearby-leech.ngrok-free.app"  # Replace with static domain
        headers = {"ngrok-skip-browser-warning": "true"}
        response = requests.get(static_url, headers=headers)

        if response.status_code == 200:
            logger.info(f"Successfully bypassed ngrok warning for: {static_url}")
        else:
            logger.warning(f"Failed to bypass ngrok warning. Status code: {response.status_code}")

        return {"status": "success", "output": output_json}

    except subprocess.TimeoutExpired as e:
        logger.error(f"Subprocess execution timed out: {e}")
        raise HTTPException(status_code=504, detail="main.py execution timed out.")

    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    finally:
        # Cleanup input.json
        try:
            if os.path.exists("input.json"):
                os.remove("input.json")
                logger.info("input.json file removed.")
        except Exception as e:
            logger.warning(f"Failed to remove input.json: {e}")

