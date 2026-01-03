#!/bin/bash

# Navigate to the project directory
cd /Users/bala/Projects/PinterestPost

# Activate virtual environment if you have one (optional, uncomment if needed)
# source venv/bin/activate

# Run the script using the full path to python
# Adjust '/usr/bin/python3' to your specific python path if different (e.g., /opt/homebrew/bin/python3)
/Library/Frameworks/Python.framework/Versions/3.11/bin/python3 post_pin.py >> daily_log.txt 2>&1
