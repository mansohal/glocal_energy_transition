import subprocess
import time
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_uvicorn():
    """Run the FastAPI app."""
    try:
        logger.info("Starting Uvicorn...")
        uvicorn_process = subprocess.Popen(
            ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        )
        uvicorn_process.wait()
    except Exception as e:
        logger.error("Failed to start Uvicorn: %s", e)

def run_ngrok():
    """Run ngrok."""
    try:
        time.sleep(15)  # Wait for Uvicorn to initialize
        logger.info("Starting Ngrok...")
        ngrok_process = subprocess.Popen(
            ["ngrok", "start", "static-tunnel", "--config", "C:/Users/projectadmin/.ngrok2/ngrok.yml"]
        )
        ngrok_process.wait()
    except Exception as e:
        logger.error("Failed to start Ngrok: %s", e)

def terminate_processes(processes):
    """Terminate all running processes gracefully."""
    for process in processes:
        try:
            logger.info(f"Terminating process PID {process.pid}...")
            process.terminate()
        except Exception as e:
            logger.warning(f"Failed to terminate process PID {process.pid}: {e}")

if __name__ == "__main__":
    uvicorn_process = None
    ngrok_process = None
    try:
        # Start Uvicorn
        uvicorn_process = subprocess.Popen(
            ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
        )
        logger.info("Uvicorn started with PID: %s", uvicorn_process.pid)

        # Wait for Uvicorn to initialize
        time.sleep(15)

        # Start Ngrok
        ngrok_process = subprocess.Popen(
            ["ngrok", "start", "static-tunnel", "--config", "C:/Users/projectadmin/.ngrok2/ngrok.yml"]
        )
        logger.info("Ngrok started with PID: %s", ngrok_process.pid)

        # Wait for both processes
        uvicorn_process.wait()
        ngrok_process.wait()

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down processes...")
    finally:
        terminate_processes([uvicorn_process, ngrok_process])
        logger.info("All processes terminated.")
