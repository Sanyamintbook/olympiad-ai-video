import os
import sys
import time
import json
from pathlib import Path
from fastapi.testclient import TestClient

# Add project root to path
PROJECT_ROOT = Path("C:/Users/Sanyami Jain/Documents/Vidoe_Automation/olympiad-ai-video")
sys.path.append(str(PROJECT_ROOT))
os.chdir(str(PROJECT_ROOT))

# Import the app
from main import app
from app.config.settings import get_settings

def test_e2e():
    client = TestClient(app)
    settings = get_settings()
    
    # 1. Prepare PDF path
    pdf_path = PROJECT_ROOT / "uploads" / "test.pdf"
    if not pdf_path.exists():
        print(f"Error: test PDF not found at {pdf_path}")
        return
        
    print(f"Starting E2E async validation. Uploading {pdf_path}...")
    
    # 2. Upload file
    with open(pdf_path, "rb") as f:
        response = client.post(
            "/upload",
            files={"file": ("test.pdf", f, "application/pdf")}
        )
        
    if response.status_code != 200:
        print(f"Upload failed: {response.status_code} - {response.text}")
        return
        
    res_data = response.json()
    job_id = res_data["job_id"]
    document_id = res_data["document_id"]
    print(f"Upload success! Job ID: {job_id}, Document ID: {document_id}")
    
    # 3. Poll status
    print("Polling job status...")
    status = "PENDING"
    start_time = time.time()
    max_wait = 180  # 3 minutes maximum wait
    
    while status in ["PENDING", "RUNNING"] and (time.time() - start_time) < max_wait:
        time.sleep(3)
        status_resp = client.get(f"/api/jobs/{job_id}/status")
        if status_resp.status_code != 200:
            print(f"Status check failed: {status_resp.status_code} - {status_resp.text}")
            break
            
        status_data = status_resp.json()
        status = status_data["status"]
        stage = status_data["stage"]
        progress = status_data["progress"]
        done = status_data["units_done"]
        total = status_data["units_total"]
        
        print(f"[{round(time.time() - start_time, 1)}s] Status: {status} | Stage: {stage} | Progress: {progress}% ({done}/{total} units)")
        
        if status in ["DONE", "FAILED"]:
            break
            
    print(f"\nFinal status reached: {status}")
    if status == "DONE":
        # Check generated output files
        job_dir = Path(settings.output_directory) / document_id
        print(f"Checking outputs in: {job_dir}")
        
        pptx_exists = (job_dir / "output.pptx").exists()
        script_exists = (job_dir / "script.json").exists()
        audio_metadata_exists = (job_dir / "audio_metadata.json").exists()
        
        print(f"  output.pptx exists: {pptx_exists}")
        print(f"  script.json exists: {script_exists}")
        print(f"  audio_metadata.json exists: {audio_metadata_exists}")
        
        if script_exists:
            with open(job_dir / "script.json", "r", encoding="utf-8") as f:
                script_data = json.load(f)
            print(f"  Parsed segments count: {len(script_data['segments'])}")
            
        if audio_metadata_exists:
            with open(job_dir / "audio_metadata.json", "r", encoding="utf-8") as f:
                meta = json.load(f)
            print(f"  Audio clips successfully synthesized: {len(meta['clips'])}")
            
        # Check for failures directory files
        failures = [f.name for f in job_dir.glob("failure_*.json")]
        if failures:
            print(f"  Encountered unit failures: {failures}")
            
    else:
        print(f"Job failed or timed out. Status data: {status_data}")

if __name__ == "__main__":
    test_e2e()
