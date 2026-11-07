"""Domain models for the Vaccination Tracker (PROG211 - OOP Lectures 1-3).

Privacy by design
-----------------
No names, phone numbers, addresses or national IDs are stored anywhere in
this project. A patient is identified only by a pseudonymous code (for
example PT-0001), a year of birth and a district. The code is written on the
child's vaccination card, so a health worker can find the record without the
system holding any personal identifier.

Classes
-------
Vaccine            - a vaccine and its schedule rules.
VaccinationRecord  - one patient's progress on one vaccine.
Patient            - a pseudonymous patient who owns many records.
"""

from datetime import date, datetime, timedelta
from typing import Dict, Optional

# Tuples: fixed, read-only reference data that must never change at run time.
DISTRICTS = (
    "Bo", "Bombali", "Bonthe", "Falaba", "Kailahun", "Kambia", "Karene",
    "Kenema", "Koinadugu", "Kono", "Moyamba", "Port Loko", "Pujehun",
    "Tonkolili", "Western Area Rural", "Western Area Urban",
)
STATUS_LABELS = ("Not started", "In progress", "Complete")
DATE_FORMAT = "%Y-%m-%d"


def _iso(value: Optional[date]) -> Optional[str]:
    """Return a date as YYYY-MM-DD text, or None when there is no date."""
    return value.strftime(DATE_FORMAT) if value else None


class Vaccine:
    """A vaccine and the rules of its dose schedule."""

    def __init__(self, code: str, name: str, doses_required: int,
                 interval_days: int = 0) -> None:
        code = str(code).strip().upper()
        name = str(name).strip()
        if not code:
            raise ValueError("Vaccine code cannot be empty.")
        if not name:
            raise ValueError("Vaccine name cannot be empty.")
        if doses_required < 1:
            raise ValueError("A vaccine needs at least one dose.")
        if interval_days < 0:
            raise ValueError("The interval between doses cannot be negative.")
        if doses_required > 1 and interval_days == 0:
            raise ValueError("A multi-dose vaccine needs an interval in days.")
        self.code = code
        self.name = name
        self.doses_required = doses_required
        self.interval_days = interval_days

    # ----- instance method ------------------------------------------------
    def describe(self) -> str:
        """Return a one-line, plain-language description."""
        if self.doses_required == 1:
            return "{} - {}: 1 dose".format(self.code, self.name)
        return "{} - {}: {} doses, {} days apart".format(
            self.code, self.name, self.doses_required, self.interval_days)

    def to_dict(self) -> Dict:
        return {"code": self.code, "name": self.name,
                "doses_required": self.doses_required,
                "interval_days": self.interval_days}

    # ----- class method ---------------------------------------------------
    @classmethod
    def from_dict(cls, data: Dict) -> "Vaccine":
        """Alternative constructor: rebuild a Vaccine from saved data."""
        return cls(data["code"], data["name"],
                   data["doses_required"], data["interval_days"])


class VaccinationRecord:
    """One patient's progress on one vaccine."""

    def __init__(self, vaccine_code: str, doses_received: int = 0,
                 last_dose_date: Optional[date] = None,
                 next_due_date: Optional[date] = None) -> None:
        self.vaccine_code = vaccine_code
        self.doses_received = doses_received
        self.last_dose_date = last_dose_date
        self.next_due_date = next_due_date

    # ----- static method --------------------------------------------------
    @staticmethod
    def parse_date(text: str) -> date:
        """Convert 'YYYY-MM-DD' text to a date, with a helpful error."""
        try:
            return datetime.strptime(str(text).strip(), DATE_FORMAT).date()
        except ValueError:
            raise ValueError(
                "Date must look like YYYY-MM-DD, for example 2026-11-07."
            ) from None

    # ----- instance methods -----------------------------------------------
    def is_complete(self, vaccine: Vaccine) -> bool:
        return self.doses_received >= vaccine.doses_required

    def status(self, vaccine: Vaccine) -> str:
        """Pick a label from the STATUS_LABELS tuple."""
        if self.doses_received == 0:
            return STATUS_LABELS[0]
        if self.is_complete(vaccine):
            return STATUS_LABELS[2]
        return STATUS_LABELS[1]

    def days_overdue(self, today: date) -> int:
        """Days past the due date; 0 when on schedule or finished."""
        if self.next_due_date is None or today <= self.next_due_date:
            return 0
        return (today - self.next_due_date).days

    def add_dose(self, vaccine: Vaccine, dose_date: date,
                 today: Optional[date] = None) -> None:
        """Record one dose and work out when the next one is due."""
        today = today or date.today()
        if vaccine.code != self.vaccine_code:
            raise ValueError("This record belongs to a different vaccine.")
        if self.is_complete(vaccine):
            raise ValueError("{} is already complete ({} of {} doses).".format(
                vaccine.code, self.doses_received, vaccine.doses_required))
        if dose_date > today:
            raise ValueError("A dose date cannot be in the future.")
        if self.last_dose_date and dose_date < self.last_dose_date:
            raise ValueError("This dose is dated before the previous dose.")
        self.doses_received += 1
        self.last_dose_date = dose_date
        if self.is_complete(vaccine):
            self.next_due_date = None
        else:
            self.next_due_date = dose_date + timedelta(days=vaccine.interval_days)

    def to_dict(self) -> Dict:
        return {"vaccine_code": self.vaccine_code,
                "doses_received": self.doses_received,
                "last_dose_date": _iso(self.last_dose_date),
                "next_due_date": _iso(self.next_due_date)}

    @classmethod
    def from_dict(cls, data: Dict) -> "VaccinationRecord":
        last = data["last_dose_date"]
        due = data["next_due_date"]
        return cls(data["vaccine_code"], data["doses_received"],
                   cls.parse_date(last) if last else None,
                   cls.parse_date(due) if due else None)


class Patient:
    """A pseudonymous patient. Holds a dictionary of vaccination records."""

    _counter = 0  # class attribute: how many patient codes have been issued

    def __init__(self, patient_code: str, year_of_birth: int, district: str,
                 today: Optional[date] = None) -> None:
        if not Patient.is_valid_year(year_of_birth, today):
            raise ValueError(
                "Year of birth must be a whole year from 1900 to this year.")
        self.patient_code = patient_code
        self.year_of_birth = year_of_birth
        self.district = Patient.match_district(district)
        self.records: Dict[str, VaccinationRecord] = {}

    # ----- static methods -------------------------------------------------
    @staticmethod
    def is_valid_year(year: int, today: Optional[date] = None) -> bool:
        current = (today or date.today()).year
        return (isinstance(year, int) and not isinstance(year, bool)
                and 1900 <= year <= current)

    @staticmethod
    def match_district(text: str) -> str:
        """Return the official spelling of a district, or raise an error."""
        wanted = str(text).strip().lower()
        for name in DISTRICTS:
            if name.lower() == wanted:
                return name
        raise ValueError("Unknown district '{}'. Choose one of: {}.".format(
            text, ", ".join(DISTRICTS)))

    # ----- class methods --------------------------------------------------
    @classmethod
    def create(cls, year_of_birth: int, district: str,
               today: Optional[date] = None) -> "Patient":
        """Factory: issue the next patient code and build the Patient."""
        patient = cls("PT-{:04d}".format(cls._counter + 1),
                      year_of_birth, district, today)
        cls._counter += 1  # only after validation succeeds
        return patient

    @classmethod
    def set_counter(cls, value: int) -> None:
        """Keep new codes unique after data is loaded from a file."""
        cls._counter = value

    @classmethod
    def from_dict(cls, data: Dict) -> "Patient":
        patient = cls(data["patient_code"], data["year_of_birth"],
                      data["district"])
        for code, item in data["records"].items():
            patient.records[code] = VaccinationRecord.from_dict(item)
        return patient

    # ----- instance methods -----------------------------------------------
    def approximate_age(self, today: Optional[date] = None) -> int:
        return (today or date.today()).year - self.year_of_birth

    def receive_vaccine(self, vaccine: Vaccine, dose_date: date,
                        today: Optional[date] = None) -> VaccinationRecord:
        """Give one dose: the Patient and Vaccine objects work together."""
        if dose_date.year < self.year_of_birth:
            raise ValueError("A dose cannot be dated before the year of birth.")
        is_new = vaccine.code not in self.records
        record = self.records.get(vaccine.code) or VaccinationRecord(vaccine.code)
        record.add_dose(vaccine, dose_date, today)  # raises before we store
        if is_new:
            self.records[vaccine.code] = record
        return record

    def overdue_records(self, today: date) -> Dict[str, VaccinationRecord]:
        """Return only the records whose next dose is overdue."""
        overdue: Dict[str, VaccinationRecord] = {}
        for code, record in self.records.items():
            if record.days_overdue(today) > 0:
                overdue[code] = record
        return overdue

    def display_info(self, vaccines: Dict[str, Vaccine],
                     today: Optional[date] = None) -> str:
        """Return a printable vaccination card."""
        today = today or date.today()
        text = "Patient card: {}\n".format(self.patient_code)
        age = self.approximate_age(today)
        if age < 1:
            age_text = "under 1 year old"
        elif age == 1:
            age_text = "about 1 year old"
        else:
            age_text = "about {} years old".format(age)
        text += "  Year of birth : {} ({})\n".format(self.year_of_birth, age_text)
        text += "  District      : {}\n".format(self.district)
        text += "  Vaccinations  :\n"
        if not self.records:
            return text + "    No doses recorded yet.\n"
        for code, record in self.records.items():
            vaccine = vaccines.get(code)
            if vaccine is None:
                text += "    {} (not in the vaccine list)\n".format(code)
                continue
            text += "    {:<6} {:<28} {}/{} doses  {:<12}  last {}".format(
                code, vaccine.name, record.doses_received,
                vaccine.doses_required, record.status(vaccine),
                _iso(record.last_dose_date))
            if record.next_due_date:
                text += ", next due {}".format(_iso(record.next_due_date))
                late = record.days_overdue(today)
                if late:
                    text += " (OVERDUE by {} days)".format(late)
            text += "\n"
        return text

    def to_dict(self) -> Dict:
        records: Dict[str, Dict] = {}
        for code, record in self.records.items():
            records[code] = record.to_dict()
        return {"patient_code": self.patient_code,
                "year_of_birth": self.year_of_birth,
                "district": self.district,
                "records": records}
