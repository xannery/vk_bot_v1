import os
from dotenv import load_dotenv

load_dotenv()

# VK
TOKEN = os.getenv("VK_TOKEN", "")
GROUP_ID = int(os.getenv("GROUP_ID", "0"))

# Google Sheets
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")

# Админы (VK user ids)
_admins_raw = os.getenv("ADMINS", "")
ADMINS = [int(x.strip()) for x in _admins_raw.split(",") if x.strip().isdigit()]