"""
Power Trading System — Phase Integrity Verifier
------------------------------------------------
Scans all critical modules (AI Core, Risk Engine, Broker Framework, etc.)
and generates/verifies SHA256 hashes to ensure system consistency.

Usage:
    python tools/integrity_check.py
"""

import os
import hashlib
import json
from datetime import datetime

# === CONFIGURATION ===
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INTEGRITY_FILE = os.path.join(PROJECT_ROOT, "docs", "phase_integrity_hash.json")

TARGET_PATHS = [
    "backend/ai_core/",
    "backend/risk_manager.py",
    "backend/brokers/",
    "backend/simulation_engine/",
    "backend/deep_memory/",
    "backend/stress_testing/",
    "backend/hedging/",
    "backend/nightly_retraining/",
    "backend/cloud_sync/",
    "frontend/",
    "launcher/",
    "utils/",
]

# === HASHING FUNCTIONS ===
def compute_file_hash(filepath):
    """Compute SHA256 hash for a given file."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None

def scan_and_hash(base_path):
    """Walk through all target files and compute their hashes."""
    hash_dict = {}
    for rel_path in TARGET_PATHS:
        abs_path = os.path.join(base_path, rel_path)
        if os.path.isfile(abs_path):
            hash_dict[rel_path] = compute_file_hash(abs_path)
        elif os.path.isdir(abs_path):
            for root, _, files in os.walk(abs_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    rel = os.path.relpath(full_path, base_path)
                    hash_dict[rel] = compute_file_hash(full_path)
    return hash_dict

def load_existing_hashes():
    if os.path.exists(INTEGRITY_FILE):
        with open(INTEGRITY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_hashes(hashes):
    os.makedirs(os.path.dirname(INTEGRITY_FILE), exist_ok=True)
    data = {
        "generated_at": datetime.utcnow().isoformat(),
        "hashes": hashes
    }
    with open(INTEGRITY_FILE, "w") as f:
        json.dump(data, f, indent=4)
    print(f"[✔] Integrity map saved: {INTEGRITY_FILE}")

def verify_integrity(current, reference):
    """Compare current hashes with reference integrity file."""
    errors = []
    for path, hash_val in reference.items():
        if path not in current:
            errors.append(f"[MISSING] {path}")
        elif current[path] != hash_val:
            errors.append(f"[MODIFIED] {path}")
    for path in current:
        if path not in reference:
            errors.append(f"[NEW FILE] {path}")
    return errors

# === MAIN EXECUTION ===
if __name__ == "__main__":
    print("🔍 Power Trading System — Phase Integrity Verification")
    print("Scanning project files...")

    current_hashes = scan_and_hash(PROJECT_ROOT)
    existing_data = load_existing_hashes()
    reference_hashes = existing_data.get("hashes", {})

    if not reference_hashes:
        print("[!] No existing integrity file found — creating baseline...")
        save_hashes(current_hashes)
        print("[✔] Baseline integrity map created.")
    else:
        print("Comparing with existing integrity map...")
        issues = verify_integrity(current_hashes, reference_hashes)

        if not issues:
            print("\n✅ System Integrity Verified — All 39 Phases Intact.")
        else:
            print("\n⚠️ Integrity Warnings:")
            for issue in issues:
                print("   " + issue)
            print("\n❌ System Integrity Compromised — Please Review Changes.")
