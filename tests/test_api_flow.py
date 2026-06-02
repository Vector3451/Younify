import requests
import time
import json
from typing import Dict, Any

# --- Configuration ---
API_BASE_URL = "http://localhost:3000/api/v1"

def submit_task(prompt: str, temp: float = 0.7) -> str:
    """Sends a task to the API Gateway and returns the job_id."""
    print("=" * 50)
    print("STEP 1: SUBMITTING TASK TO API GATEWAY...")
    print("=" * 50)
    
    headers = {"Content-Type": "application/json"}
    payload = {
        "prompt": prompt,
        "max_tokens": 512,
        "temperature": temp
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/generate", headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        print(f"SUCCESS: Job accepted. Job ID: {data['job_id']}")
        return data['job_id']
        
    except requests.exceptions.RequestException as e:
        print(f"FATAL ERROR: Could not connect to API Gateway: {e}")
        return None


def poll_status(job_id: str):
    """Polls the API Gateway until the job is resolved."""
    print("\n" + "=" * 50)
    print("STEP 2: POLLING JOB STATUS...")
    print("=" * 50)
    
    url = f"{API_BASE_URL}/status/{job_id}"
    
    while True:
        time.sleep(1) # Wait 1 second between polls
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            status = data['status']
            
            print(f"Current Status for {job_id}: {status}")
            
            if status == "COMPLETED":
                print("\n*** SUCCESS: Job completed successfully! ***")
                print(f"Final Content: {data['result']['choices'][0]['message']['content']}")
                return True
            
            elif status == "FAILED":
                print("\n*** FAILURE: Job encountered an error. ***")
                print(f"Error Detail: {data.get('error')}")
                return False

            elif status == "QUEUED":
                # Continue polling
                pass
                
        except requests.exceptions.HTTPError as e:
            print(f"FATAL ERROR: API returned error status code: {e}")
            return False
        except requests.exceptions.RequestException as e:
            # This usually means the server is down or unreachable
            print(f"FATAL ERROR: Connection lost while polling: {e}. Is the API Gateway running?")
            return False


if __name__ == "__main__":
    if 'requests' not in locals():
        print("NOTICE: 'requests' library is required for this test. Please run: pip install requests")
    
    TASK_PROMPT = "Design a simple, highly scalable architecture using microservices and Kubernetes for an e-commerce platform."
    
    # 1. Initiate the job
    job_id = submit_task(TASK_PROMPT)
    
    if job_id:
        # 2. Poll for the result
        success = poll_status(job_id)
        
        if success:
            print("\n--- SYSTEM TEST PASSED ---")
        else:
            print("\n--- SYSTEM TEST FAILED ---")

