import os

EDITION = os.environ.get("EDITION", "international")  # "international" | "cn"

def is_cn() -> bool:
    return EDITION == "cn"
