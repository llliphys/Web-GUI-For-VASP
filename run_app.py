import os
import sys
from streamlit.web import cli as stcli

def main():
    sys.argv = ["streamlit", "run", os.path.join(os.path.dirname(__file__), "app.py")]
    sys.exit(stcli.main())
