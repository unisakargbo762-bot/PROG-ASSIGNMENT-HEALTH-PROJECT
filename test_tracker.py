"""Unit tests. Run with:  python -m unittest -v"""

import os
import tempfile
import unittest
from datetime import date

from models import Patient, VaccinationRecord
from tracker import VaccinationTracker

TODAY = date(2026, 11, 7)


def d(text):
    return VaccinationRecord.parse_date(text)


class TrackerTests(unittest.TestCase):
    def setUp(self):
        Patient.set_counter(0)
        self.tracker = VaccinationTracker.with_default_vaccines()

    # ----- registration ---------------------------------------------------
    def test_codes_are_issued_in_order(self):
        first = self.tracker.register_patient(2025, "Bo", TODAY)
        second = self.tracker.register_patient(2024, "kono", TODAY)
        self.assertEqual(first.patient_code, "PT-0001")
        self.assertEqual(second.patient_code, "PT-0002")
        self.assertEqual(second.district, "Kono")  # spelling normalised

    def test_invalid_year_and_district_are_rejected(self):
        with self.assertRaises(ValueError):
            self.tracker.register_patient(1850, "Bo", TODAY)
        with self.assertRaises(ValueError):
            self.tracker.register_patient(2025, "Atlantis", TODAY)

    def test_failed_registration_does_not_use_up_a_code(self):
        with self.assertRaises(ValueError):
            self.tracker.register_patient(2025, "Atlantis", TODAY)
        patient = self.tracker.register_patient(2025, "Bo", TODAY)
        self.assertEqual(patient.patient_code, "PT-0001")

    # ----- dose rules -----------------------------------------------------
    def test_next_due_date_follows_the_interval(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        record = self.tracker.record_vaccination(
            patient.patient_code, "PENTA", d("2026-09-21"), TODAY)
        self.assertEqual(record.next_due_date, d("2026-10-19"))

    def test_completed_vaccine_rejects_extra_dose(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        self.tracker.record_vaccination(
            patient.patient_code, "BCG", d("2026-08-10"), TODAY)
        with self.assertRaises(ValueError):
            self.tracker.record_vaccination(
                patient.patient_code, "BCG", d("2026-09-10"), TODAY)

    def test_dates_must_make_sense(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        code = patient.patient_code
        self.tracker.record_vaccination(code, "OPV", d("2026-09-01"), TODAY)
        with self.assertRaises(ValueError):  # before previous dose
            self.tracker.record_vaccination(code, "OPV", d("2026-08-01"), TODAY)
        with self.assertRaises(ValueError):  # in the future
            self.tracker.record_vaccination(code, "OPV", d("2027-01-01"), TODAY)
        with self.assertRaises(ValueError):  # before birth year
            self.tracker.record_vaccination(code, "BCG", d("2020-01-01"), TODAY)
        with self.assertRaises(ValueError):  # text is not a date
            d("07/11/2026")

    def test_rejected_dose_leaves_no_empty_record(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        with self.assertRaises(ValueError):
            self.tracker.record_vaccination(
                patient.patient_code, "OPV", d("2027-01-01"), TODAY)
        self.assertEqual(len(patient.records), 0)

    def test_unknown_patient_and_vaccine(self):
        with self.assertRaises(ValueError):
            self.tracker.record_vaccination("PT-9999", "BCG", TODAY, TODAY)
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        with self.assertRaises(ValueError):
            self.tracker.record_vaccination(
                patient.patient_code, "XYZ", TODAY, TODAY)

    # ----- reports --------------------------------------------------------
    def test_overdue_detection(self):
        late = self.tracker.register_patient(2026, "Bo", TODAY)
        on_time = self.tracker.register_patient(2026, "Bo", TODAY)
        self.tracker.record_vaccination(
            late.patient_code, "PENTA", d("2026-09-21"), TODAY)
        self.tracker.record_vaccination(
            on_time.patient_code, "PENTA", d("2026-10-25"), TODAY)
        self.assertEqual(len(late.overdue_records(TODAY)), 1)
        self.assertEqual(len(on_time.overdue_records(TODAY)), 0)
        self.assertIn("19 days overdue", self.tracker.overdue_report(TODAY))

    def test_coverage_percentage(self):
        a = self.tracker.register_patient(2026, "Bo", TODAY)
        self.tracker.register_patient(2026, "Bo", TODAY)
        self.tracker.record_vaccination(
            a.patient_code, "BCG", d("2026-08-10"), TODAY)
        self.assertIn("50.0%", self.tracker.coverage_summary())

    # ----- privacy and persistence ---------------------------------------
    def test_only_pseudonymous_fields_are_stored(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        self.assertEqual(
            set(patient.to_dict()),
            {"patient_code", "year_of_birth", "district", "records"})

    def test_save_and_load_round_trip(self):
        patient = self.tracker.register_patient(2026, "Bo", TODAY)
        self.tracker.record_vaccination(
            patient.patient_code, "PENTA", d("2026-09-21"), TODAY)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "records.json")
            self.tracker.save(path)
            Patient.set_counter(0)
            loaded = VaccinationTracker.load(path)
            record = loaded.find_patient("PT-0001").records["PENTA"]
            self.assertEqual(record.doses_received, 1)
            self.assertEqual(record.next_due_date, d("2026-10-19"))
            # a new patient must not reuse PT-0001
            self.assertEqual(
                loaded.register_patient(2026, "Bo", TODAY).patient_code,
                "PT-0002")

    def test_damaged_file_gives_a_clear_error(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "records.json")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write("{not json")
            with self.assertRaises(ValueError):
                VaccinationTracker.load(path)


if __name__ == "__main__":
    unittest.main()
