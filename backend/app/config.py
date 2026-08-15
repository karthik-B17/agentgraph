"""
config.py
---------
Reads database connection details from environment variables.
Nothing sensitive is ever hardcoded here — this is what makes it
safe to commit this file to GitHub.
"""

import os
from dotenv import load_dotenv

# Loads variables from a local .env file (if present) into the environment.
load_dotenv()

COGNODB_URI = os.getenv("COGNODB_URI")
COGNODB_USER = os.getenv("COGNODB_USER")
COGNODB_PASSWORD = os.getenv("COGNODB_PASSWORD")
COGNODB_DATABASE = os.getenv("COGNODB_DATABASE", "neo4j")

# Fail loudly and early if something critical is missing.
missing = [
    name
    for name, value in [
        ("COGNODB_URI", COGNODB_URI),
        ("COGNODB_USER", COGNODB_USER),
        ("COGNODB_PASSWORD", COGNODB_PASSWORD),
    ]
    if not value
]

if missing:
    raise RuntimeError(
        f"Missing required environment variables: {', '.join(missing)}. "
        f"Did you create a .env file?"
    )