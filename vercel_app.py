# vercel_app.py
import os
import sys

# This trick tells Vercel to run the Streamlit CLI
from streamlit.web.cli import main

if __name__ == "__main__":
    sys.argv = [
        "streamlit",
        "run",
        "app.py",
        "--server.port", "8080",
        "--server.address", "0.0.0.0",
    ]
    main()
