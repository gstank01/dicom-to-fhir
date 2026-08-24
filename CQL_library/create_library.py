import os
import json
import base64 #encoding
import requests
import logging
import shutil
from utils.logging_setup import setup_logging

#Step 1:Load CQL file
def load_cql_file(rules_dir):
    cql_files = [f for f in os.listdir(rules_dir) if f.endswith(".cql")]
    if not cql_files:
        logging.critical("No .cql files found in the 'rules/' directory.")
        exit(1)
    latest_file = max(cql_files, key=lambda f: os.path.getmtime(os.path.join(rules_dir, f)))
    return os.path.join(rules_dir, latest_file)
#Step 2: Encode CQL file
def encode_cql(cql_text):
    logging.info("Using direct CQL encoding (bypassing translator)")
    return base64.b64encode(cql_text.encode('utf-8')).decode('utf-8')
#Step3:Build library
def build_library(rule_name, rule_version, encoded_cql, cql_text):
    logical_id = f"{rule_name}-library"
    
    return {
        "resourceType": "Library",
        "id": logical_id,
        "name": rule_name,
        "title": f"{rule_name} CQL Library",
        "status": "active",
        "version": rule_version,
        "type": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/library-type",
                "code": "logic-library"
            }]
        },
        "content": [{
            "contentType": "text/cql",
            "data": encoded_cql
        }]
    }
 
#Step 4:Upload Library 
def upload_library(fhir_url, library_resource):
    resource_id = library_resource["id"]
    url = f"{fhir_url}/Library/{resource_id}"
    headers = {"Content-Type": "application/fhir+json"}
    response = requests.put(url, headers=headers, json=library_resource)
    logging.info(f"Library upload response: {response.status_code}")
    if response.status_code not in (200, 201):
        logging.error("Failed to upload Library.")
        return False
    else:
        logging.info("Library uploaded successfully.")
        return True
#Step 5: Archive file
def archive_cql_file(cql_path, rules_dir="rules", archive_dir_name="archive"):
    archive_dir = os.path.join(rules_dir, archive_dir_name)
    os.makedirs(archive_dir, exist_ok=True)
    dest_path = os.path.join(archive_dir, os.path.basename(cql_path))
    shutil.move(cql_path, dest_path)
    logging.info(f"Archived processed CQL file to: {dest_path}")
#Run main function to execute work flow
def main():
    setup_logging(log_file_prefix="cds_upload.log")
    logging.info("CDS Library upload starting...")

    FHIR_SERVER = "http://localhost:8081/fhir" # the path to the server, replace if running on a different server 
    RULES_DIR = "rules"
    RULE_VERSION = "1.0.0"

    os.makedirs(RULES_DIR, exist_ok=True)

    cql_path = load_cql_file(RULES_DIR)
    rule_name = os.path.splitext(os.path.basename(cql_path))[0].replace("_", "")

    with open(cql_path, 'r', encoding='utf-8') as f:
        cql_text = f.read()

    encoded_cql = encode_cql(cql_text)  # encoding CQL into Base64
    library = build_library(rule_name, RULE_VERSION, encoded_cql, cql_text)
    library_success = upload_library(FHIR_SERVER, library)

    if not library_success:
        logging.error("Library upload failed. Stopping.")
        exit(1)

    archive_cql_file(cql_path, rules_dir=RULES_DIR)

    logging.info(f" Library upload successful: {library['id']}")
    
if __name__ == "__main__":
    main()