import os #import operating system dependent functionality
import pydicom #python package for working with DICOM files
import requests #allows to send HTTP requests using Python
import logging #allow for the creation of log files
import glob #allows for file automation pattern: removes the need to type file names manually
import shutil #allows to move files to folders
import json #allow json files to be read
import datetime #allows for the use of datetime
from utils.logging_setup import setup_logging # import the logging function that is stored in a separate folder
from utils.load_loinc_map import load_loinc_map #import the LOINC mapping function

FHIR_URL = "http://localhost:8081/fhir" # the path to the server, replace if running on a different server 
DICOM_INPUT_DIR = "in" #the path to the directory where the DICOM SR files are stored
ARCHIVE_DIR = "out" # 
CARDS_OUTPUT_DIR = "cards_output" #the dierctory where the evaluated logic is stored
LOINC_MAP_PATH = "mappings/loinc_map.json"  # Path to JSON that contains loinc map
loinc_map = load_loinc_map(LOINC_MAP_PATH) #load the mapping once globaly 


#Step 1: Find and load the DICOM file 
def find_and_load_dicom(DICOM_INPUT_DIR):
    dicom_files = glob.glob(os.path.join(DICOM_INPUT_DIR, "*.dcm"))# identify .dcm files
    if not dicom_files:
        logging.critical(f"No DICOM files found in directory: {DICOM_INPUT_DIR}")
        return None, None
    dicom_path = dicom_files[0]
    try:
        ds = pydicom.dcmread(dicom_path, force=True)
        logging.info(f"Loaded DICOM file: {dicom_path}")
        return ds, dicom_path
    except Exception as e:
        logging.critical(f"Failed to read DICOM file: {e}")
        return None, dicom_path
        
#Step 2: Get the patient ID from the DICOM file and match it to a patient on the server
def get_fhir_patient_reference(dicom_dataset, fhir_url):
    patient_id = getattr(dicom_dataset, "PatientID", None)#extract the patient ID from the DICOM file
    if not patient_id:
        logging.critical("No Patient ID found in DICOM file.")
        return None
    logging.info(f"Extracted Patient ID from DICOM: {patient_id}")
    search_url = f"{fhir_url}/Patient?identifier={patient_id}"# search the server for the patient ID
    response = requests.get(search_url, headers={"Accept": "application/fhir+json"})
    if response.status_code != 200 or response.json().get("total", 0) == 0:
        logging.critical(f"No matching Patient found for ID: {patient_id}")
        return None
    fhir_id = response.json()["entry"][0]["resource"]["id"]
    return f"Patient/{fhir_id}"

#Step 3:Get the ACC# as service request to assosiate the DICOM study with matching event on the server
def get_service_request_reference(dicom_dataset, fhir_url):
    accession_number = getattr(dicom_dataset, "AccessionNumber", None)#extract the accession number form the DICOM file
    if not accession_number:
        logging.critical("No Accession Number found in DICOM.")
        return None
    search_url = f"{fhir_url}/ServiceRequest?identifier={accession_number}"
    response = requests.get(search_url, headers={"Accept": "application/fhir+json"})
    if response.status_code != 200 or response.json().get("total", 0) == 0:
        logging.critical(f"No matching ServiceRequest found for Accession Number: {accession_number}")
        return None
    fhir_id = response.json()["entry"][0]["resource"]["id"]
    return f"ServiceRequest/{fhir_id}"
    
#Step 4: Post the observations to the server by converting them to FHIR observations
def post_observations(content_sequence, patient_ref, service_request_ref):
    for item in content_sequence:
        if hasattr(item, "MeasuredValueSequence"):#read the measurements from the DICOM file
            try:#for each item check if the measurement has MeasuredValueSequence to confirm it is a measurement
                name = item.ConceptNameCodeSequence[0].CodeMeaning #extract the name of the measurement
                value = item.MeasuredValueSequence[0].NumericValue #extract the numeric value of the measurment
                unit = item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeMeaning #extract the units assosiated with the measurement
                
                
                loinc = loinc_map.get(name.strip(), {"code": "99999-9", "display": name})
                logging.debug(f"Mapping used for '{name}': {loinc}")

                obs = { #build the observations in json format
                    "resourceType": "Observation",
                    "status": "final",
                    "category": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                            "code": "imaging"
                        }]
                    }],
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": loinc["code"],
                            "display": loinc["display"]
                        }],
                        "text": name
                    },
                    "subject": {"reference": patient_ref},
                    "valueQuantity": {
                        "value": value,
                        "unit": unit,
                        "system": "http://unitsofmeasure.org",
                        "code": unit
                    }
                }

                if service_request_ref:
                    obs["basedOn"] = [{"reference": service_request_ref}]

                res = requests.post(f"{FHIR_URL}/Observation", json=obs, headers={"Content-Type": "application/fhir+json"})
                if res.status_code == 201:
                    logging.info(f"Posted Observation: {name} = {value} {unit}")
                else:
                    logging.warning(f"Failed to post {name} [Status: {res.status_code}]: {res.text}")
            except Exception as e:
                logging.error(f"Error processing item: {e}")

        if hasattr(item, "ContentSequence"):
            post_observations(item.ContentSequence, patient_ref, service_request_ref)
                
            
#Step 5: Evaluate the observations agains the library
def evaluate_library(fhir_url, library_id, patient_id):
    eval_url = f"{fhir_url}/Library/{library_id}/$evaluate"
    params = {"resourceType": "Parameters", "parameter": [{"name": "subject", "valueString": f"Patient/{patient_id}"}]}
    headers = {"Content-Type": "application/fhir+json"}

    response = requests.post(eval_url, headers=headers, json=params)
    if response.status_code == 200:
        logging.info("Library evaluation successful.")
        return response.json()
    else:
        logging.error(f"Library evaluation failed: {response.text}")
        return None
        
#Step 6: Generate card with recomendations, this is a mock card, in real clinical workflows this  will be generated dinamically
def generate_card(patient_id, output_dir):
    card = {
        "summary": "Possible Hypertension Detected",
        "indicator": "warning",
        "detail": "Patient meets hypertension thresholds based on recent echocardiographic measurements.",
        "source": {"label": "Hypertension CQL Rule v1.0.0"},
        "suggestions": [
            {
                "label": "Schedule 24-hour BP monitoring",
                "actions": [
                    {
                        "type": "create",
                        "description": "Order 24-hour BP monitoring",
                        "resource": {
                            "resourceType": "ServiceRequest",
                            "status": "draft",
                            "intent": "order",
                            "code": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "698452002",
                                        "display": "24 hour blood pressure monitoring"
                                    }
                                ],
                                "text": "24 hour blood pressure monitoring"
                            },
                            "subject": {"reference": f"Patient/{patient_id}"}
                        }
                    }
                ]
            }
        ]
    }
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, f"card_{patient_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(card, f, indent=2)
    logging.info(f"Saved CDS card to: {file_path}")

#Step 7: Process the file, this is the function that is called in the main file
def process_dicom_file(ds, dicom_path, FHIR_URL, library_id="minimaltest-library"):  
    if not ds or not hasattr(ds, "ContentSequence"):
        logging.warning("DICOM file missing ContentSequence or failed to load.")
        return

    patient_ref = get_fhir_patient_reference(ds, FHIR_URL)
    if not patient_ref:
        return

    service_request_ref = get_service_request_reference(ds, FHIR_URL)
    if not service_request_ref:
        logging.critical("Aborting processing: No valid ServiceRequest found.")
        return  # Exit early if no ServiceRequest is found

    post_observations(ds.ContentSequence, patient_ref, service_request_ref)
    patient_id = patient_ref.split("/")[-1]

    evaluation_result = evaluate_library(FHIR_URL, library_id, patient_id)
    if evaluation_result:
        logging.info(f"Evaluation result: {evaluation_result}")
        for param in evaluation_result.get("parameter", []):
            if param.get("name") == "Hypertension" and param.get("valueBoolean") is True:
                generate_card(patient_id, CARDS_OUTPUT_DIR)

    archive_file(dicom_path)



# Step 8: Archive the file
def archive_file(file_path):
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    archived_path = shutil.move(file_path, os.path.join(ARCHIVE_DIR, os.path.basename(file_path)))
    logging.info(f"Archived processed file to: {archived_path}")