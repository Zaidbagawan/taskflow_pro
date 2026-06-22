import random

import json
import os
from datetime import datetime

def generate_otp():
    return str(random.randint(100000, 999999))

def save_audit_json(data):
    folder = "audit_logs"

    if not os.path.exists(folder):
        os.makedirs(folder)

    filename = f"{folder}/log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filename, "w") as f:
        json.dump(data, f, indent=4)