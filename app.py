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

