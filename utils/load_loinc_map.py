import json
import logging

def load_loinc_map(loinc_map_path):
    try:
        with open(loinc_map_path, "r", encoding="utf-8") as f:
            loinc_map = json.load(f)
            logging.info(f"Loaded LOINC map with {len(loinc_map)} entries.")
            return loinc_map
    except Exception as e:
        logging.critical(f"Failed to load LOINC map: {e}")
        return {}
