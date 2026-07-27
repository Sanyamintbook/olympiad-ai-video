import json
import os
from threading import Lock
from typing import Dict, Any

STATE_FILE = "local_state.json"
_lock = Lock()

def get_job_state(job_id: str) -> Dict[str, Any]:
    with _lock:
        if not os.path.exists(STATE_FILE):
            return {}
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(job_id, {})
        except Exception:
            return {}

def update_job_state(job_id: str, new_state: Dict[str, Any]) -> None:
    with _lock:
        data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
        
        if job_id not in data:
            data[job_id] = {}
        
        data[job_id].update(new_state)
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

def set_job_state(job_id: str, state: Dict[str, Any]) -> None:
    with _lock:
        data = {}
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
                
        data[job_id] = state
        
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
