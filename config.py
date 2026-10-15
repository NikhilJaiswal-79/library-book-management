"""
Configuration settings for Library Book Usage Analysis System.

MySQL credentials are read from environment variables so that no secret is ever
committed to version control. Copy `.env.example` to `.env` and fill in your
values before running the application.
"""

import os

# Load variables from a local .env file if python-dotenv is available.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # python-dotenv is optional; plain environment variables still work.
    pass

# MySQL Settings
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "library_analysis_db"),
}

# Library Circulation Business Rules
DEFAULT_LOAN_DAYS = int(os.getenv("DEFAULT_LOAN_DAYS", "14"))  # Loan period before overdue

# Output directories
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "reports_and_charts")