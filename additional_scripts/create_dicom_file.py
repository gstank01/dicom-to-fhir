# references:
# DICOM data generation tutorial at https://pydicom.github.io/pydicom/stable/auto_examples/input_output/plot_write_dicom.html
# Guide to DICOM Data elements https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_6.html
# UID format https://dicom.nema.org/medical/dicom/current/output/chtml/part06/chapter_a.html
# Write DICOM file tutorila https://pydicom.github.io/pydicom/1.1/ref_guide.html

import datetime
from pathlib import Path
import pydicom
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.uid import UID, ExplicitVRLittleEndian

print("Creating multi-trigger mock DICOM SR with accurate units...")

# Dataset
ds = Dataset()
ds.PatientName = "Test^MaleHypertrophy" #change to generate new patient
ds.PatientID = "HTN456789" ##change to generate new ID
ds.AccessionNumber = "ACC789101101" ##change to generate new accession number
ds.Modality = "SR"
ds.SeriesNumber = 1
ds.InstanceNumber = 1
ds.PatientSex = "M"  # needed for LVMI_High_Male rule (change if F needed)

now = datetime.datetime.now()
ds.StudyDate = now.strftime("%Y%m%d")
ds.StudyTime = now.strftime("%H%M%S")
ds.ContentDate = now.strftime("%Y%m%d")
ds.ContentTime = now.strftime("%H%M%S.%f")
#Generate UID
ds.SOPClassUID = UID("1.2.840.10008.5.1.4.1.1.88.33")
ds.SOPInstanceUID = UID("1.2.826.0.1.3680043.2.1125.1.2")
ds.StudyInstanceUID = UID("1.2.826.0.1.3680043.2.1125.3.2")
ds.SeriesInstanceUID = UID("1.2.826.0.1.3680043.2.1125.4.2")

# Construct measurements 
def add_measurement(name, value, unit):
    item = Dataset()
    item.ValueType = "NUM"
    item.ConceptNameCodeSequence = [Dataset()]
    item.ConceptNameCodeSequence[0].CodeValue = "999"
    item.ConceptNameCodeSequence[0].CodeMeaning = name
    item.ConceptNameCodeSequence[0].CodingSchemeDesignator = "99TEST"
    
    item.MeasuredValueSequence = [Dataset()]
    item.MeasuredValueSequence[0].NumericValue = value
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence = [Dataset()]
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeValue = unit
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodeMeaning = unit
    item.MeasuredValueSequence[0].MeasurementUnitsCodeSequence[0].CodingSchemeDesignator = "UCUM"
    return item

#  Measurements: values + units 
measurements = { # add more if needed. Useful if new CQL is introduced
    "Interventricular Septum Diastolic Thickness": (13, "mm"),
    "Left Ventricle Posterior Wall Diastolic Thickness": (12, "mm"),
    "Left Atrium Antero-posterior Systolic Dimension": (42, "mm"),
    "Left Ventricular Mass Index by Echocardiography": (120, "g/m2")
}

ds.ContentSequence = [add_measurement(name, val, unit) for name, (val, unit) in measurements.items()]

#  File Meta 
file_meta = FileMetaDataset()
file_meta.MediaStorageSOPClassUID = ds.SOPClassUID
file_meta.MediaStorageSOPInstanceUID = ds.SOPInstanceUID
file_meta.ImplementationClassUID = UID("1.2.826.0.1.3680043.2.1125.2.2")
file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
ds.file_meta = file_meta

#  Save 
output_path = Path("in") / "mock_multi_trigger_sr.dcm"
output_path.parent.mkdir(parents=True, exist_ok=True)
ds.save_as(str(output_path))
print(f"DICOM SR saved to: {output_path.resolve()}")
