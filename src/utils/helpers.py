# utils/helpers.py
# This file can contain various utility functions like data parsing, string manipulation etc.
# For now, it's mostly a placeholder.

def parse_switch_config(config_text, vendor):
    """
    Parses switch configuration text based on vendor.
    This is a highly simplified placeholder.
    """
    if vendor.lower() == "cisco":
        # Example: extract hostname
        lines = config_text.splitlines()
        for line in lines:
            if line.strip().startswith("hostname"):
                return {"hostname": line.split()[-1]}
    
    return {"raw_config_length": len(config_text)}