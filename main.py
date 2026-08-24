from utils.logging_setup import setup_logging #run the loggong set up
from processing.dicom_handler import find_and_load_dicom, process_dicom_file#import functions from the dicom_handler.py script 

def main():
    setup_logging(log_file_prefix="dicom_and_cds.log")

    DICOM_INPUT_DIR = "in"# directory
    FHIR_URL = "http://localhost:8081/fhir" ## the path to the server, replace if running on a different server 
    LIBRARY_ID = "hypertensionclinical-library"  # This should match the Library ID on the server

    ds, dicom_path = find_and_load_dicom(DICOM_INPUT_DIR)

    if ds is None:
        print("No DICOM file was loaded.")
        return

    # Process the file, post Observations, evaluate CQL, generate card if needed
    process_dicom_file(ds, dicom_path, FHIR_URL, LIBRARY_ID)

if __name__ == "__main__":
    main()
