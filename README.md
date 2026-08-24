Run the project locally.
Ensure server is running on localhost:8081.
Send POST http://localhost:8081/fhir/Patient (code availabe in ../JSON).
Send POST http://localhost:8081/fhir/ServiceRequest (code availabe in ../JSON).
Send POST ttp://localhost:8081/fhir/Observation (code availabe in ../JSON).
Ensure .cql file is in ../CQL_library/rules (it will archive after processing).
In CDM (or preffered method) run your_directory/ python create_library.py.
Check log.
Ensure DICOM SR file is in ../in directory (it will move to ../out after processing).
In CDM (or preffered method) run your_directory/python main.py.
Check log flies for output.
File should be generated in ../cards_output if logic evaluate to true.
Notes:
Generate new SR file by modiffing the script in ../additional scripts.
Not all LOINC codes are availabe in ../mappings/loinc_map.json. Add more if different cql logic is introduced.
