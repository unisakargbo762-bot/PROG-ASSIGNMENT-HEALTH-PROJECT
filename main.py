"""Command-line interface for the Vaccination Tracker.

Run:
    python main.py              start the interactive menu
    python main.py --demo       run a short scripted demonstration
    python main.py --data FILE  use a different data file
"""

import argparse
from datetime import date

from models import DISTRICTS, Patient, VaccinationRecord
from tracker import VaccinationTracker

DEFAULT_DATA_FILE = "data/records.json"
DEMO_TODAY = date(2026, 11, 7)  # fixed date so the demo output never changes

MENU = """
=== Vaccination Tracker ===
 1. Register a new patient
 2. Record a vaccine dose
 3. View a patient card
 4. List all patients
 5. Overdue vaccinations report
 6. Vaccine coverage summary
 7. List vaccines
 0. Save and exit
"""


# ----- input helpers (plain language, clear errors) -------------------------
def ask_int(prompt: str) -> int:
    text = input(prompt).strip()
    try:
        return int(text)
    except ValueError:
        raise ValueError("Please type a whole number, for example 2025.") from None


def ask_date(prompt: str) -> date:
    text = input(prompt + " [YYYY-MM-DD, or press Enter for today]: ").strip()
    if text == "":
        return date.today()
    return VaccinationRecord.parse_date(text)


# ----- menu actions ---------------------------------------------------------
def action_register(tracker: VaccinationTracker) -> None:
    print("Districts: " + ", ".join(DISTRICTS))
    year = ask_int("Year of birth (for example 2025): ")
    district = input("District: ")
    patient = tracker.register_patient(year, district)
    print("Registered. Write this code on the vaccination card: "
          + patient.patient_code)


def action_record_dose(tracker: VaccinationTracker) -> None:
    code = input("Patient code (for example PT-0001): ")
    print(tracker.display_vaccines())
    vaccine_code = input("Vaccine code (for example PENTA): ")
    dose_date = ask_date("Date the dose was given")
    record = tracker.record_vaccination(code, vaccine_code, dose_date)
    vaccine = tracker.find_vaccine(vaccine_code)
    print("Saved: {} dose {} of {}.".format(
        vaccine.code, record.doses_received, vaccine.doses_required))
    if record.next_due_date:
        print("Next dose due on " + str(record.next_due_date))
    else:
        print("This vaccine is now complete.")


def action_view_patient(tracker: VaccinationTracker) -> None:
    print(tracker.display_patient(input("Patient code: ")))


def action_list_patients(tracker: VaccinationTracker) -> None:
    print(tracker.display_all_patients())


def action_overdue(tracker: VaccinationTracker) -> None:
    print(tracker.overdue_report())


def action_coverage(tracker: VaccinationTracker) -> None:
    print(tracker.coverage_summary())


def action_vaccines(tracker: VaccinationTracker) -> None:
    print(tracker.display_vaccines())


def run_menu(tracker: VaccinationTracker, data_file: str) -> None:
    # A dictionary maps each menu choice to the function that handles it.
    actions = {
        "1": action_register, "2": action_record_dose,
        "3": action_view_patient, "4": action_list_patients,
        "5": action_overdue, "6": action_coverage, "7": action_vaccines,
    }
    try:
        while True:
            print(MENU)
            choice = input("Choose an option (0-7): ").strip()
            if choice == "0":
                break
            action = actions.get(choice)
            if action is None:
                print("Please type a number from 0 to 7.")
                continue
            try:
                action(tracker)
            except ValueError as error:
                print("Problem: {}".format(error))
    except (EOFError, KeyboardInterrupt):
        print("\nClosing.")
    tracker.save(data_file)
    print("Data saved to " + data_file + ". Goodbye.")


# ----- scripted demonstration ----------------------------------------------
def run_demo() -> None:
    Patient.set_counter(0)
    tracker = VaccinationTracker.with_default_vaccines()
    today = DEMO_TODAY
    parse = VaccinationRecord.parse_date

    print("=== DEMO (today is {}) ===\n".format(today))
    print(tracker.display_vaccines())

    print("--- 1. Register three patients (no names stored) ---")
    infant = tracker.register_patient(2026, "Bo", today)
    toddler = tracker.register_patient(2025, "Western Area Urban", today)
    child = tracker.register_patient(2024, "Kenema", today)
    for patient in (infant, toddler, child):  # tuple of objects, loop only
        print("Registered {} ({}, born {})".format(
            patient.patient_code, patient.district, patient.year_of_birth))

    print("\n--- 2. Record doses ---")
    schedule = (
        (infant.patient_code, "BCG", "2026-08-10"),
        (infant.patient_code, "PENTA", "2026-09-21"),
        (toddler.patient_code, "PENTA", "2025-12-01"),
        (toddler.patient_code, "PENTA", "2025-12-29"),
        (toddler.patient_code, "PENTA", "2026-01-26"),
        (toddler.patient_code, "MR", "2026-09-01"),
        (child.patient_code, "BCG", "2024-03-02"),
        (child.patient_code, "OPV", "2024-03-02"),
        (child.patient_code, "OPV", "2024-03-30"),
    )
    for patient_code, vaccine_code, when in schedule:
        record = tracker.record_vaccination(
            patient_code, vaccine_code, parse(when), today)
        print("{}  {:<5} dose {} on {}".format(
            patient_code, vaccine_code, record.doses_received, when))

    print("\n--- 3. Patient card ---")
    print(tracker.display_patient(infant.patient_code, today))
    print(tracker.display_patient(toddler.patient_code, today))

    print("--- 4. All patients ---")
    print(tracker.display_all_patients())

    print("--- 5. Follow-up list ---")
    print(tracker.overdue_report(today))

    print("--- 6. Coverage ---")
    print(tracker.coverage_summary())

    print("--- 7. Input checks (errors are explained, never a crash) ---")
    checks = (
        ("Fourth PENTA dose",
         lambda: tracker.record_vaccination(
             toddler.patient_code, "PENTA", parse("2026-10-01"), today)),
        ("Dose in the future",
         lambda: tracker.record_vaccination(
             infant.patient_code, "OPV", parse("2027-01-01"), today)),
        ("Unknown district",
         lambda: tracker.register_patient(2025, "Atlantis", today)),
        ("Bad date text", lambda: parse("07/11/2026")),
    )
    for label, attempt in checks:
        try:
            attempt()
        except ValueError as error:
            print("{}: {}".format(label, error))

    print("\n--- 8. Privacy proof: exactly what is stored for a patient ---")
    print(infant.to_dict())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open-source Vaccination Tracker (privacy-respecting).")
    parser.add_argument("--demo", action="store_true",
                        help="run a scripted demo and exit")
    parser.add_argument("--data", default=DEFAULT_DATA_FILE,
                        help="path of the JSON data file")
    args = parser.parse_args()

    if args.demo:
        run_demo()
        return 0
    try:
        tracker = VaccinationTracker.load_or_create(args.data)
    except ValueError as error:
        print(error)
        return 1
    run_menu(tracker, args.data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
