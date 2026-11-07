"""VaccinationTracker: the manager that stores and reports on all records.

Data structure (Lecture 2): DICTIONARIES only. Patients are stored with their
unique code as the key, and vaccines with their short code as the key, so any
record can be found instantly without searching a list.
"""

import json
import os
from datetime import date
from typing import Dict, Optional

from models import Patient, Vaccine

# Illustrative schedules for demonstration. Always confirm against the
# national EPI schedule before any real-world use.
DEFAULT_VACCINES = (
    ("BCG", "BCG (Tuberculosis)", 1, 0),
    ("OPV", "Oral Polio Vaccine", 4, 28),
    ("PENTA", "Pentavalent (DPT-HepB-Hib)", 3, 28),
    ("PCV", "Pneumococcal Conjugate", 3, 28),
    ("MR", "Measles-Rubella", 2, 270),
)


class VaccinationTracker:
    """Registers patients, records doses and produces reports."""

    def __init__(self) -> None:
        self.vaccines: Dict[str, Vaccine] = {}
        self.patients: Dict[str, Patient] = {}

    # ----- class methods (alternative constructors) -----------------------
    @classmethod
    def with_default_vaccines(cls) -> "VaccinationTracker":
        tracker = cls()
        for code, name, doses, interval in DEFAULT_VACCINES:
            tracker.add_vaccine(Vaccine(code, name, doses, interval))
        return tracker

    @classmethod
    def load(cls, path: str) -> "VaccinationTracker":
        """Rebuild a tracker from a JSON file written by save()."""
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            tracker = cls()
            for code, item in data["vaccines"].items():
                tracker.vaccines[code] = Vaccine.from_dict(item)
            highest = 0
            for code, item in data["patients"].items():
                tracker.patients[code] = Patient.from_dict(item)
                highest = max(highest, int(code.split("-")[1]))
            Patient.set_counter(highest)
        except (OSError, KeyError, ValueError, IndexError, TypeError) as error:
            raise ValueError(
                "Could not read data file '{}': {}".format(path, error)
            ) from error
        return tracker

    @classmethod
    def load_or_create(cls, path: str) -> "VaccinationTracker":
        """Open the saved file if it exists, otherwise start fresh."""
        if os.path.exists(path):
            return cls.load(path)
        return cls.with_default_vaccines()

    # ----- add records ----------------------------------------------------
    def add_vaccine(self, vaccine: Vaccine) -> None:
        if vaccine.code in self.vaccines:
            raise ValueError("Vaccine {} already exists.".format(vaccine.code))
        self.vaccines[vaccine.code] = vaccine

    def register_patient(self, year_of_birth: int, district: str,
                         today: Optional[date] = None) -> Patient:
        """Add a new patient to the dictionary and return it."""
        patient = Patient.create(year_of_birth, district, today)
        self.patients[patient.patient_code] = patient
        return patient

    def record_vaccination(self, patient_code: str, vaccine_code: str,
                           dose_date: date, today: Optional[date] = None):
        patient = self.find_patient(patient_code)
        vaccine = self.find_vaccine(vaccine_code)
        return patient.receive_vaccine(vaccine, dose_date, today)

    # ----- look-ups -------------------------------------------------------
    def find_patient(self, patient_code: str) -> Patient:
        patient = self.patients.get(str(patient_code).strip().upper())
        if patient is None:
            raise ValueError(
                "No patient with code '{}'. Use option 4 to see all codes."
                .format(patient_code))
        return patient

    def find_vaccine(self, vaccine_code: str) -> Vaccine:
        vaccine = self.vaccines.get(str(vaccine_code).strip().upper())
        if vaccine is None:
            raise ValueError(
                "No vaccine with code '{}'. Use option 7 to see all codes."
                .format(vaccine_code))
        return vaccine

    # ----- display records ------------------------------------------------
    def display_vaccines(self) -> str:
        text = "Available vaccines\n"
        for vaccine in self.vaccines.values():
            text += "  " + vaccine.describe() + "\n"
        return text

    def display_patient(self, patient_code: str,
                        today: Optional[date] = None) -> str:
        return self.find_patient(patient_code).display_info(
            self.vaccines, today)

    def display_all_patients(self) -> str:
        text = "Registered patients: {}\n".format(len(self.patients))
        if not self.patients:
            return text + "  (none yet)\n"
        text += "  {:<8} {:<6} {:<20} {:>7} {:>9}\n".format(
            "Code", "Born", "District", "Started", "Complete")
        for code, patient in self.patients.items():
            complete = 0
            for vaccine_code, record in patient.records.items():
                vaccine = self.vaccines.get(vaccine_code)
                if vaccine is not None and record.is_complete(vaccine):
                    complete += 1
            text += "  {:<8} {:<6} {:<20} {:>7} {:>9}\n".format(
                code, patient.year_of_birth, patient.district,
                len(patient.records), complete)
        return text

    # ----- reports --------------------------------------------------------
    def overdue_report(self, today: Optional[date] = None) -> str:
        """List every patient whose next dose is late (follow-up list)."""
        today = today or date.today()
        text = "Overdue vaccinations as of {}\n".format(today)
        total = 0
        for code, patient in self.patients.items():
            for vaccine_code, record in patient.overdue_records(today).items():
                text += "  {:<8} {:<6} due {}  ({} days overdue)\n".format(
                    code, vaccine_code, record.next_due_date,
                    record.days_overdue(today))
                total += 1
        if total == 0:
            return text + "  None - every patient is on schedule.\n"
        return text + "Total overdue: {}\n".format(total)

    def coverage_summary(self) -> str:
        """Per-vaccine counts: how many patients started and finished."""
        total = len(self.patients)
        text = "Vaccine coverage ({} registered patients)\n".format(total)
        text += "  {:<6} {:>7} {:>9} {:>9}\n".format(
            "Code", "Started", "Complete", "Coverage")
        for code, vaccine in self.vaccines.items():
            started = 0
            complete = 0
            for patient in self.patients.values():
                record = patient.records.get(code)
                if record is not None:
                    started += 1
                    if record.is_complete(vaccine):
                        complete += 1
            percent = (complete / total * 100) if total else 0.0
            text += "  {:<6} {:>7} {:>9} {:>8.1f}%\n".format(
                code, started, complete, percent)
        return text

    # ----- save -----------------------------------------------------------
    def save(self, path: str) -> None:
        """Write all data to a JSON file (safe write: temp file, then rename)."""
        vaccines: Dict[str, Dict] = {}
        for code, vaccine in self.vaccines.items():
            vaccines[code] = vaccine.to_dict()
        patients: Dict[str, Dict] = {}
        for code, patient in self.patients.items():
            patients[code] = patient.to_dict()
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        temp_path = path + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump({"vaccines": vaccines, "patients": patients},
                      handle, indent=2)
        os.replace(temp_path, path)
