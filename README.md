# Vaccination Tracker

An open-source, privacy-respecting **vaccination tracking system** written in Python using Object-Oriented Programming (OOP). It helps a health worker register children, record vaccine doses, see who is **overdue** for the next dose, and view **coverage** per vaccine.

- **Module:** PROG211 Object-Oriented Programming 1 (Individual Assignment, 10%)
- **Domain:** Health: Vaccination Tracker
- **Author:** [Your Full Name] · Student ID: [Your ID]
- **Lecturer / collaborator:** Amandus Benjamin Coker
- **Python:** 3.8 or newer. **No external libraries**, works offline.

---

## The real-world problem

When children miss a follow-up dose, a vaccine course stays incomplete and the child stays unprotected, often because nobody notices the missed date. This tool keeps each child's dose history, **calculates the next due date**, and produces a **follow-up list** of overdue children so health workers can act on it.

---

## How it meets Digital Public Goods (DPG) standards

| DPG principle | How this project meets it |
|---|---|
| **Open-source** | Plain Python source under the **MIT License** (see `LICENSE`), hosted publicly on GitHub. Anyone may use, study, adapt and share it. |
| **Inclusive and accessible design** | Numbered, plain-language menu; no jargon; every error says *what went wrong and how to fix it* (e.g. "Date must look like YYYY-MM-DD, for example 2026-11-07"); no colour or mouse needed, so it works with screen readers and basic terminals; runs on low-spec, offline computers with no internet or installs; includes all 16 districts of Sierra Leone. |
| **Privacy-respecting** | **No sensitive personal data is stored.** No names, phone numbers, addresses or national IDs. A patient is only a pseudonymous code (`PT-0001`), a **year** of birth and a **district**. The code is written on the child's paper vaccination card. Data stays in a local file; nothing is sent over a network. `data/` is git-ignored so records are never uploaded by accident. |
| **Modular and reusable** | Three separate modules with one responsibility each: `models.py` (data objects), `tracker.py` (storage and reports), `main.py` (user interface). The models and tracker can be imported into a web or mobile app without changing them. Includes unit tests. |

---

## Project structure

```
vaccination-tracker/
├── models.py          # Vaccine, VaccinationRecord, Patient classes
├── tracker.py         # VaccinationTracker: storage, reports, save/load
├── main.py            # Command-line menu and demo
├── test_tracker.py    # 13 unit tests
├── docs/
│   ├── sample_output.txt              # output of: python main.py --demo
│   └── sample_interactive_session.txt # output of a menu session
├── LICENSE            # MIT
├── .gitignore
└── README.md
```

---

## How the assignment requirements are met

### Task 1: OOP basics (classes, attributes, methods, objects)

| Class | Attributes | Key methods |
|---|---|---|
| `Vaccine` | `code`, `name`, `doses_required`, `interval_days` | `describe()`, `to_dict()` |
| `VaccinationRecord` | `vaccine_code`, `doses_received`, `last_dose_date`, `next_due_date` | `add_dose()`, `is_complete()`, `status()`, `days_overdue()` |
| `Patient` | `patient_code`, `year_of_birth`, `district`, `records` | `receive_vaccine()`, `display_info()`, `overdue_records()`, `approximate_age()` |
| `VaccinationTracker` | `vaccines`, `patients` | `register_patient()`, `record_vaccination()`, `display_all_patients()`, `overdue_report()`, `coverage_summary()`, `save()` |

**Object creation and interaction:** `Patient.receive_vaccine(vaccine, date)` takes a `Vaccine` object, creates or updates the patient's `VaccinationRecord`, and the record uses the vaccine's `doses_required` and `interval_days` to compute the next due date. Three objects cooperate in a single action.

### Task 2: Python data structure (dictionary)

The program stores multiple objects in **dictionaries only**:
- `tracker.patients`: `{ "PT-0001": Patient, ... }` keyed by the unique patient code
- `tracker.vaccines`: `{ "PENTA": Vaccine, ... }` keyed by vaccine code
- `patient.records`: `{ "PENTA": VaccinationRecord, ... }`

Functions to **add** and **display** records: `register_patient()` / `add_vaccine()` and `display_all_patients()` / `display_patient()` / `display_vaccines()`.

**Bonus (tuples):** Tuples are used correctly for fixed, read-only reference data that must never change: `DISTRICTS`, `STATUS_LABELS`, `DEFAULT_VACCINES`.

### Task 3: Classes, methods and DPG alignment

| Method type | Examples in the code |
|---|---|
| **Instance method** (uses `self`) | `Vaccine.describe()`, `VaccinationRecord.add_dose()`, `Patient.receive_vaccine()`, `Patient.display_info()` |
| **Class method** (`@classmethod`, uses `cls`) | `Patient.create()` (issues the next patient code using the class attribute `_counter`), `Patient.set_counter()`, `Patient.from_dict()`, `Vaccine.from_dict()`, `VaccinationTracker.with_default_vaccines()`, `VaccinationTracker.load()` |
| **Static method** (`@staticmethod`) | `VaccinationRecord.parse_date()`, `Patient.is_valid_year()`, `Patient.match_district()` |

---

## How to run

```bash
git clone https://github.com/[your-username]/vaccination-tracker.git
cd vaccination-tracker

python main.py --demo      # scripted demonstration (no data saved)
python main.py             # interactive menu (saves to data/records.json)
python -m unittest -v      # run the 13 tests
```

### Example usage (sample input and output)

**Input** (menu choices typed by the user, shown after each prompt):

```
Choose an option (0-7): 1
Year of birth (for example 2025): 2025
District: Bo
Choose an option (0-7): 2
Patient code (for example PT-0001): PT-0001
Vaccine code (for example PENTA): PENTA
Date the dose was given [YYYY-MM-DD, or press Enter for today]: 2026-10-01
Choose an option (0-7): 3
Patient code: PT-0001
```

**Output:**

```
Registered. Write this code on the vaccination card: PT-0001
Saved: PENTA dose 1 of 3.
Next dose due on 2026-10-29

Patient card: PT-0001
  Year of birth : 2025 (about 1 year old)
  District      : Bo
  Vaccinations  :
    PENTA  Pentavalent (DPT-HepB-Hib)   1/3 doses  In progress   last 2026-10-01, next due 2026-10-29 (OVERDUE by 9 days)
```

**Follow-up list** (`python main.py --demo`, option 5 equivalent):

```
Overdue vaccinations as of 2026-11-07
  PT-0001  PENTA  due 2026-10-19  (19 days overdue)
  PT-0003  OPV    due 2024-04-27  (924 days overdue)
Total overdue: 2
```

Full runs are in `docs/sample_output.txt` and `docs/sample_interactive_session.txt`.

---

## Data model: exactly what is stored

```json
{
  "patient_code": "PT-0001",
  "year_of_birth": 2026,
  "district": "Bo",
  "records": {
    "PENTA": {"vaccine_code": "PENTA", "doses_received": 1,
              "last_dose_date": "2026-09-21", "next_due_date": "2026-10-19"}
  }
}
```

A unit test (`test_only_pseudonymous_fields_are_stored`) fails if any extra field is ever added to a patient.

---

## Input validation

Impossible data is rejected with a clear message and the program keeps running: unknown district, impossible birth year, a fourth dose of a 3-dose vaccine, a dose dated in the future, before the previous dose or before birth, and badly formatted dates. A rejected dose never leaves a half-created record behind (covered by a test).

---

## Limitations and future work

- The vaccine schedules in `tracker.py` are **illustrative**. Confirm them against the national EPI schedule before real use.
- Pseudonymous codes protect privacy but mean health workers must keep the paper card safe. A lost card cannot be looked up by name by design.
- The tool does not enforce *minimum* intervals between doses, only the due date.
- Possible extensions: a web or mobile front end reusing `models.py`, SMS reminders, CSV export for district reports, translations (e.g. Krio).

---

## License

Released under the **MIT License**. See `LICENSE`.
