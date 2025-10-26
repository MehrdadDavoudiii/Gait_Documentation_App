from __future__ import annotations

import os
import shutil  
import sys
import sqlite3
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import calendar
from datetime import datetime, timedelta
from pathlib import Path
import time
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class DateEntry(ttk.Frame):
    def __init__(
        self,
        parent: tk.Widget,
        textvariable: tk.StringVar | None = None,
        min_year: int = 1900,
        max_year: int | None = 2100,
        **kwargs,
    ) -> None:
        super().__init__(parent, **kwargs)
        if textvariable is None:
            textvariable = tk.StringVar()
        self.var = textvariable
        if max_year is None:
            max_year = datetime.today().year
        self.min_year = min_year
        self.max_year = max_year
        # Year, month, day variables
        self.year_var = tk.StringVar()
        self.month_var = tk.StringVar()
        self.day_var = tk.StringVar()
        # Create Comboboxes
        years = [str(y) for y in range(self.min_year, self.max_year + 1)]
        # Increase the widths of the date dropdowns so two‑digit days and months are clearly visible.
        # The year field uses 6 characters, while month and day use 3 characters each to comfortably fit
        # two digits. Without adequate width the numbers can appear truncated or difficult to read.
        # Adjust the widths of the date dropdowns.  The year field uses a width of 5
        # characters (e.g., "2025"), the month field 3 characters (e.g., "10"), and
        # the day field 5 characters.  This makes the two‑digit day values clearly
        # visible while reducing the overall footprint of the widget.  Without
        # sufficient width the day can appear truncated or hard to read, especially
        # when the UI is scaled down.
        self.year_combo = ttk.Combobox(
            self,
            values=years,
            textvariable=self.year_var,
            state="readonly",
            width=5,
            font=("Segoe UI", 9),
        )
        self.year_combo.pack(side=tk.LEFT, padx=(0, 2))
        months = ["%02d" % m for m in range(1, 13)]
        self.month_combo = ttk.Combobox(
            self,
            values=months,
            textvariable=self.month_var,
            state="readonly",
            width=3,
            font=("Segoe UI", 9),
        )
        self.month_combo.pack(side=tk.LEFT, padx=(0, 2))
        self.day_combo = ttk.Combobox(
            self,
            values=[],
            textvariable=self.day_var,
            state="readonly",
            width=5,
            font=("Segoe UI", 9),
        )
        self.day_combo.pack(side=tk.LEFT, padx=(0, 2))
        # Bind changes
        self.year_combo.bind("<<ComboboxSelected>>", self._on_change)
        self.month_combo.bind("<<ComboboxSelected>>", self._on_change)
        self.day_combo.bind("<<ComboboxSelected>>", self._on_change)
        # Initialize with current date or provided value
        initial = self.var.get().strip()
        if initial:
            try:
                dt = datetime.strptime(initial, "%Y-%m-%d")
                y, m, d = dt.year, dt.month, dt.day
            except Exception:
                dt = datetime.today()
                y, m, d = dt.year, dt.month, dt.day
        else:
            dt = datetime.today()
            y, m, d = dt.year, dt.month, dt.day
        # Set combos
        self.year_var.set(str(y))
        self.month_var.set(f"{m:02d}")
        # Fill days and set day
        self._update_day_options()
        # Ensure initial day is valid before setting
        day_str = f"{d:02d}"
        if day_str in self.day_combo['values']:
             self.day_var.set(day_str)
        elif self.day_combo['values']: # Fallback to first valid day
             self.day_var.set(self.day_combo['values'][0])
        else: # Should not happen if month/year are valid
             self.day_var.set("")
        # Update variable string
        self._update_var()

    def _update_day_options(self) -> None:
        """Populate the day combobox based on selected year and month."""
        try:
            year = int(self.year_var.get())
            month = int(self.month_var.get())
            _, num_days = calendar.monthrange(year, month)
        except Exception:
            num_days = 31 # Fallback
        days = [f"{d:02d}" for d in range(1, num_days + 1)]
        current_day = self.day_var.get()
        self.day_combo.config(values=days)
        # Reset day if out of range, ensuring days list is not empty
        if current_day not in days:
            self.day_var.set(days[0] if days else "")


    def _on_change(self, event: tk.Event | None = None) -> None:
        # When year or month changes, update day list first
        if event and event.widget in {self.year_combo, self.month_combo}:
            current_day_str = self.day_var.get() # Store current day
            self._update_day_options()
            # Try to keep the same day if valid, otherwise reset
            if current_day_str in self.day_combo['values']:
                self.day_var.set(current_day_str)
            elif self.day_combo['values']:
                self.day_var.set(self.day_combo['values'][0])
            else:
                self.day_var.set("")
        # Update variable string based on current combo values
        self._update_var()

    def _update_var(self) -> None:
        y = self.year_var.get()
        m = self.month_var.get()
        d = self.day_var.get()
        if y and m and d:
            try: # Validate date before setting
                datetime(int(y), int(m), int(d))
                self.var.set(f"{int(y):04d}-{int(m):02d}-{int(d):02d}")
            except ValueError: self.var.set("") # Clear if invalid date
        else: self.var.set("") # Clear if any part is missing


    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        """Set the date from a YYYY-MM-DD string."""
        try:
            dt = datetime.strptime(value, "%Y-%m-%d")
            self.year_var.set(str(dt.year))
            self.month_var.set(f"{dt.month:02d}")
            self._update_day_options() # Update days *before* setting day
            day_str = f"{dt.day:02d}"
            if day_str in self.day_combo['values']:
                 self.day_var.set(day_str)
            elif self.day_combo['values']: # Fallback if day became invalid
                 self.day_var.set(self.day_combo['values'][0])
            else:
                 self.day_var.set("")
        except Exception: # Clear on parse error
            self.year_var.set(""); self.month_var.set(""); self.day_var.set(""); self.day_combo.config(values=[])
        finally:
             self._update_var() # Ensure var reflects combo state



class Database:
    """Manage database operations for patients, exams, interventions and attachments."""
    # --- Database methods (Unchanged from previous correct version) ---
    def __init__(self, db_path: str = "health_records.db") -> None:
        self.conn = sqlite3.connect(db_path); self.conn.execute("PRAGMA foreign_keys = ON")
        self.db_path = db_path; self.create_tables(); self.schedule_daily_backup()
    def create_tables(self) -> None:
        self.conn.executescript( """ CREATE TABLE IF NOT EXISTS patients ( patient_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_code TEXT UNIQUE, first_name TEXT NOT NULL, last_name TEXT NOT NULL, birth_date TEXT NOT NULL, diagnosis TEXT, gender TEXT, height REAL, assistive_device TEXT, address TEXT, post_number TEXT, city TEXT, country TEXT, phone TEXT, mobile TEXT, email TEXT ); CREATE TABLE IF NOT EXISTS exams ( exam_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL, exam_type TEXT NOT NULL, exam_date TEXT NOT NULL, notes TEXT, height_cm REAL, weight_kg REAL, assistive_device TEXT, bmi REAL, examiner TEXT, FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE ); CREATE TABLE IF NOT EXISTS exam_attachments ( file_id INTEGER PRIMARY KEY AUTOINCREMENT, exam_id INTEGER NOT NULL, file_path TEXT NOT NULL, description TEXT, FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE ); CREATE TABLE IF NOT EXISTS interventions ( intervention_id INTEGER PRIMARY KEY AUTOINCREMENT, patient_id INTEGER NOT NULL, intervention_type TEXT NOT NULL, intervention_date TEXT NOT NULL, notes TEXT, height_cm REAL, weight_kg REAL, assistive_device TEXT, bmi REAL, operator TEXT, FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE ); CREATE TABLE IF NOT EXISTS intervention_attachments ( file_id INTEGER PRIMARY KEY AUTOINCREMENT, intervention_id INTEGER NOT NULL, file_path TEXT NOT NULL, description TEXT, FOREIGN KEY (intervention_id) REFERENCES interventions(intervention_id) ON DELETE CASCADE ); """ )
        self.conn.commit(); cur = self.conn.cursor()
        patient_cols = [("gender", "TEXT"), ("height", "REAL"), ("assistive_device", "TEXT"), ("address", "TEXT"), ("post_number", "TEXT"), ("city", "TEXT"), ("country", "TEXT"), ("phone", "TEXT"), ("mobile", "TEXT"), ("email", "TEXT")]
        exam_cols = [("height_cm", "REAL"), ("weight_kg", "REAL"), ("assistive_device", "TEXT"), ("bmi", "REAL"), ("examiner", "TEXT")]
        interv_cols = [("height_cm", "REAL"), ("weight_kg", "REAL"), ("assistive_device", "TEXT"), ("bmi", "REAL"), ("operator", "TEXT")]
        for table, cols in [("patients", patient_cols), ("exams", exam_cols), ("interventions", interv_cols)]:
            for col, ctype in cols:
                try: cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}")
                except sqlite3.OperationalError: pass
        self.conn.commit()
    def add_patient( self, first_name: str, last_name: str, birth_date: str, diagnosis: str | None, gender: str | None = None, height: float | None = None, assistive_device: str | None = None, patient_code: str | None = None, address: str | None = None, post_number: str | None = None, city: str | None = None, country: str | None = None, phone: str | None = None, mobile: str | None = None, email: str | None = None ) -> int: cur = self.conn.cursor(); cur.execute( """INSERT INTO patients ( patient_code, first_name, last_name, birth_date, diagnosis, gender, height, assistive_device, address, post_number, city, country, phone, mobile, email ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (patient_code, first_name, last_name, birth_date, diagnosis, gender, height, assistive_device, address, post_number, city, country, phone, mobile, email) ); self.conn.commit(); return cur.lastrowid
    def search_patients(self, filter_text: str = "", field: str = "last_name"):
        """Return all patient records filtered by a search string and optional birth-date range.

        The ``field`` parameter determines which column is searched for the ``filter_text``.
        Acceptable values are ``last_name``, ``diagnosis``, ``patient_code`` and ``post_number``.
        A birth date range may be stored on the instance via :meth:`set_birth_range` and
        will be applied automatically when querying.
        """
        cur = self.conn.cursor()
        base_query = "SELECT * FROM patients"
        conditions: list[str] = []
        params: list[object] = []
        # Apply textual filter on the chosen field
        if filter_text:
            if field not in {"last_name", "diagnosis", "patient_code", "post_number"}:
                field = "last_name"
            conditions.append(f"{field} LIKE ?")
            params.append(f"%{filter_text}%")
        # Apply stored birth date range filter, if any
        birth_range = getattr(self, "_birth_range", None)
        if birth_range:
            start, end = birth_range
            if start:
                conditions.append("birth_date >= ?")
                params.append(start)
            if end:
                conditions.append("birth_date <= ?")
                params.append(end)
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        base_query += " ORDER BY last_name"
        cur.execute(base_query, params)
        return cur.fetchall()
    def set_birth_range(self, start: str | None, end: str | None) -> None: self._birth_range = (start, end)
    def backup_database(self, backup_dir: str = "backups") -> None:
        """Create a dated backup copy of the database.

        A subdirectory named ``backup_dir`` will be created if it does not already
        exist. The backup filename is derived from the name of the primary
        database (e.g. ``health_records_backup_YYYYMMDD.db``). The method uses
        SQLite's built‑in ``backup`` function to safely copy all tables and
        data to the new file. Any exception is caught and logged to stderr.
        """
        try:
            # Ensure the backup directory exists
            Path(backup_dir).mkdir(parents=True, exist_ok=True)
            # Derive a base name from the database path without extension
            base = os.path.splitext(os.path.basename(self.db_path))[0]
            date_str = datetime.now().strftime("%Y%m%d")
            backup_name = f"{base}_backup_{date_str}.db"
            dest_path = Path(backup_dir) / backup_name
            # Use SQLite's backup API to copy to the new file
            with sqlite3.connect(dest_path) as bkp_conn:
                self.conn.backup(bkp_conn)
        except Exception as e:
            # Print errors to the console; in a real app you could log this
            print(f"Backup Error: {e}")

    def schedule_daily_backup(self, backup_dir: str = "backups") -> None:
        """Start a daemon thread to perform a database backup once per day.

        The thread sleeps until the next midnight (00:00) and then calls
        :meth:`backup_database`. It then repeats the process. Because the
        thread is marked as daemon, it will not prevent the program from
        exiting when the main application closes.
        """
        def backup_loop() -> None:
            while True:
                now = datetime.now()
                # Compute next midnight by advancing one day and resetting the
                # time components.
                next_midnight = (now + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                wait_seconds = (next_midnight - now).total_seconds()
                time.sleep(max(1, wait_seconds))
                self.backup_database(backup_dir)

        # Launch the backup loop as a daemon thread
        t = threading.Thread(target=backup_loop, daemon=True)
        t.start()
    def add_exam(
        self,
        patient_id: int,
        exam_type: str,
        exam_date: str,
        notes: str | None,
        height_cm: float | None = None,
        weight_kg: float | None = None,
        assistive_device: str | None = None,
        examiner: str | None = None,
    ) -> int:
        """Insert a new examination record and compute BMI when possible.

        Returns the ``exam_id`` of the newly inserted row.
        """
        # Compute BMI if both height and weight are provided and height > 0
        bmi: float | None = None
        if height_cm and weight_kg and height_cm > 0:
            try:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            except Exception:
                bmi = None
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO exams (patient_id, exam_type, exam_date, notes, height_cm, weight_kg, assistive_device, bmi, examiner) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                patient_id,
                exam_type,
                exam_date,
                notes,
                height_cm,
                weight_kg,
                assistive_device,
                bmi,
                examiner,
            ),
        )
        self.conn.commit()
        return cur.lastrowid
    def get_exams(self, patient_id: int):
        """Return all examinations for the given patient ordered by exam_date descending."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM exams WHERE patient_id = ? ORDER BY exam_date DESC",
            (patient_id,),
        )
        return cur.fetchall()
    def delete_exam(self, exam_id: int) -> None:
        """Delete an examination and its attachments by primary key."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM exams WHERE exam_id = ?", (exam_id,))
        self.conn.commit()
    def add_exam_attachment(self, exam_id: int, file_path: str, description: str) -> int:
        """Insert a new attachment for an examination and return its file_id."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO exam_attachments (exam_id, file_path, description) VALUES (?, ?, ?)",
            (exam_id, file_path, description),
        )
        self.conn.commit()
        return cur.lastrowid
    def get_exam_attachments(self, exam_id: int):
        """Return a list of (file_id, file_path, description) for attachments of an exam."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT file_id, file_path, description FROM exam_attachments WHERE exam_id = ? ORDER BY file_id",
            (exam_id,),
        )
        return cur.fetchall()
    def delete_exam_attachment(self, file_id: int) -> None:
        """Delete an exam attachment by its file_id."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM exam_attachments WHERE file_id = ?", (file_id,))
        self.conn.commit()
    def add_intervention(
        self,
        patient_id: int,
        intervention_type: str,
        intervention_date: str,
        notes: str | None,
        height_cm: float | None = None,
        weight_kg: float | None = None,
        assistive_device: str | None = None,
        operator: str | None = None,
    ) -> int:
        """Insert a new intervention record and compute BMI when possible."""
        bmi: float | None = None
        if height_cm and weight_kg and height_cm > 0:
            try:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            except Exception:
                bmi = None
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO interventions (patient_id, intervention_type, intervention_date, notes, height_cm, weight_kg, assistive_device, bmi, operator) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                patient_id,
                intervention_type,
                intervention_date,
                notes,
                height_cm,
                weight_kg,
                assistive_device,
                bmi,
                operator,
            ),
        )
        self.conn.commit()
        return cur.lastrowid
    def get_interventions(self, patient_id: int):
        """Return all interventions for the given patient ordered by intervention_date descending."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT * FROM interventions WHERE patient_id = ? ORDER BY intervention_date DESC",
            (patient_id,),
        )
        return cur.fetchall()
    def delete_intervention(self, intervention_id: int) -> None:
        """Delete an intervention record by primary key."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM interventions WHERE intervention_id = ?", (intervention_id,))
        self.conn.commit()
    def add_intervention_attachment(self, intervention_id: int, file_path: str, description: str) -> int:
        """Insert a new attachment for an intervention and return its file_id."""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO intervention_attachments (intervention_id, file_path, description) VALUES (?, ?, ?)",
            (intervention_id, file_path, description),
        )
        self.conn.commit()
        return cur.lastrowid
    def get_intervention_attachments(self, intervention_id: int):
        """Return a list of (file_id, file_path, description) for attachments of an intervention."""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT file_id, file_path, description FROM intervention_attachments WHERE intervention_id = ? ORDER BY file_id",
            (intervention_id,),
        )
        return cur.fetchall()
    def delete_intervention_attachment(self, file_id: int) -> None:
        """Delete an intervention attachment by its file_id."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM intervention_attachments WHERE file_id = ?", (file_id,))
        self.conn.commit()
    def close(self) -> None:
        """Close the database connection if it is open."""
        if self.conn:
            self.conn.close()
    def delete_patient(self, patient_id: int) -> None:
        """Delete a patient record (and cascade to related rows) by primary key."""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM patients WHERE patient_id = ?", (patient_id,))
        self.conn.commit()
    def update_patient(
        self,
        patient_id: int,
        first_name: str,
        last_name: str,
        birth_date: str,
        diagnosis: str | None,
        gender: str | None = None,
        patient_code: str | None = None,
        address: str | None = None,
        post_number: str | None = None,
        city: str | None = None,
        country: str | None = None,
        phone: str | None = None,
        mobile: str | None = None,
        email: str | None = None,
    ) -> None:
        """Update a patient's demographic record in the database."""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE patients SET first_name=?, last_name=?, birth_date=?, diagnosis=?, gender=?, patient_code=?, address=?, post_number=?, city=?, country=?, phone=?, mobile=?, email=? WHERE patient_id = ?",
            (
                first_name,
                last_name,
                birth_date,
                diagnosis,
                gender,
                patient_code,
                address,
                post_number,
                city,
                country,
                phone,
                mobile,
                email,
                patient_id,
            ),
        )
        self.conn.commit()
    def update_exam(
        self,
        exam_id: int,
        exam_type: str,
        exam_date: str,
        notes: str | None,
        height_cm: float | None,
        weight_kg: float | None,
        assistive_device: str | None,
        examiner: str | None,
    ) -> None:
        """Update an examination record and recompute BMI if necessary."""
        bmi: float | None = None
        if height_cm and weight_kg and height_cm > 0:
            try:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            except Exception:
                bmi = None
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE exams SET exam_type=?, exam_date=?, notes=?, height_cm=?, weight_kg=?, assistive_device=?, bmi=?, examiner=? WHERE exam_id = ?",
            (
                exam_type,
                exam_date,
                notes,
                height_cm,
                weight_kg,
                assistive_device,
                bmi,
                examiner,
                exam_id,
            ),
        )
        self.conn.commit()
    def update_intervention(
        self,
        intervention_id: int,
        intervention_type: str,
        intervention_date: str,
        notes: str | None,
        height_cm: float | None,
        weight_kg: float | None,
        assistive_device: str | None,
        operator: str | None,
    ) -> None:
        """Update an intervention record and recompute BMI if necessary."""
        bmi: float | None = None
        if height_cm and weight_kg and height_cm > 0:
            try:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            except Exception:
                bmi = None
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE interventions SET intervention_type=?, intervention_date=?, notes=?, height_cm=?, weight_kg=?, assistive_device=?, bmi=?, operator=? WHERE intervention_id = ?",
            (
                intervention_type,
                intervention_date,
                notes,
                height_cm,
                weight_kg,
                assistive_device,
                bmi,
                operator,
                intervention_id,
            ),
        )
        self.conn.commit()
    def get_patient(self, patient_id: int):
        """Return a single patient record by primary key."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
        return cur.fetchone()
    def get_exam(self, exam_id: int):
        """Return a single examination record by primary key."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM exams WHERE exam_id = ?", (exam_id,))
        return cur.fetchone()
    def get_intervention(self, intervention_id: int):
        """Return a single intervention record by primary key."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM interventions WHERE intervention_id = ?", (intervention_id,))
        return cur.fetchone()


# --- NEW: AddPatientWindow Class ---
class AddPatientWindow(tk.Toplevel):
    """Toplevel window for adding a new patient."""
    def __init__(self, parent: tk.Widget, db: Database, refresh_callback) -> None:
        super().__init__(parent)
        self.db = db
        self.refresh_callback = refresh_callback
        self.title("Add New Patient")
        self.geometry("550x520") # Adjusted size
        self.resizable(False, False) # Prevent resizing this simple form

        # Make modal - important!
        self.grab_set() # Redirect all input to this window
        self.transient(parent) # Keep window on top of parent
        self.protocol("WM_DELETE_WINDOW", self.destroy) # Ensure grab is released on close

        # --- Form Layout (Moved from PatientApp) ---
        entry_frame = ttk.Frame(self, padding=(20, 15))
        entry_frame.pack(fill=tk.BOTH, expand=True)
        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(3, weight=1)

        # Use a dict to store entry widgets for easy access later
        self.entries = {}

        # Row 0: Names
        ttk.Label(entry_frame, text="First Name:*").grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['first_name'] = ttk.Entry(entry_frame)
        self.entries['first_name'].grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
        ttk.Label(entry_frame, text="Last Name:*").grid(row=0, column=2, sticky=tk.W, padx=5, pady=6)
        self.entries['last_name'] = ttk.Entry(entry_frame)
        self.entries['last_name'].grid(row=0, column=3, sticky=tk.EW, padx=5, pady=6)

        # Row 1: Birth Date & Gender
        ttk.Label(entry_frame, text="Birth Date:*").grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        # Use a StringVar for DateEntry
        self.entries['birth_date_var'] = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.entries['birth_date'] = DateEntry(entry_frame, textvariable=self.entries['birth_date_var'])
        self.entries['birth_date'].grid(row=1, column=1, sticky=tk.W, padx=5, pady=6)
        ttk.Label(entry_frame, text="Gender:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=6)
        # Use a StringVar for Combobox
        self.entries['gender_var'] = tk.StringVar(value="")
        self.entries['gender'] = ttk.Combobox(entry_frame, textvariable=self.entries['gender_var'], values=["", "Female", "Male", "Other"], state="readonly", width=18)
        self.entries['gender'].grid(row=1, column=3, sticky=tk.W, padx=5, pady=6)

        # Row 2: Diagnosis & Patient ID
        ttk.Label(entry_frame, text="Diagnosis:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['diagnosis'] = ttk.Entry(entry_frame)
        self.entries['diagnosis'].grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
        ttk.Label(entry_frame, text="Patient ID:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=6)
        self.entries['patient_code'] = ttk.Entry(entry_frame)
        self.entries['patient_code'].grid(row=2, column=3, sticky=tk.EW, padx=5, pady=6)

        # Row 3: Address
        ttk.Label(entry_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['address'] = ttk.Entry(entry_frame)
        self.entries['address'].grid(row=3, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=6)

        # Row 4: Zip Code & City.  The term "Zip Code" replaces the former
        # "Post Number" label for clarity and international comprehension.  The
        # underlying database column remains named post_number.
        ttk.Label(entry_frame, text="Zip Code:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['post_number'] = ttk.Entry(entry_frame)
        self.entries['post_number'].grid(row=4, column=1, sticky=tk.EW, padx=5, pady=6)
        ttk.Label(entry_frame, text="City:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=6)
        self.entries['city'] = ttk.Entry(entry_frame)
        self.entries['city'].grid(row=4, column=3, sticky=tk.EW, padx=5, pady=6)

        # Row 5: Country & Phone
        ttk.Label(entry_frame, text="Country:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['country'] = ttk.Entry(entry_frame)
        self.entries['country'].grid(row=5, column=1, sticky=tk.EW, padx=5, pady=6)
        ttk.Label(entry_frame, text="Phone:").grid(row=5, column=2, sticky=tk.W, padx=5, pady=6)
        self.entries['phone'] = ttk.Entry(entry_frame)
        self.entries['phone'].grid(row=5, column=3, sticky=tk.EW, padx=5, pady=6)

        # Row 6: Mobile & Email
        ttk.Label(entry_frame, text="Mobile:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=6)
        self.entries['mobile'] = ttk.Entry(entry_frame)
        self.entries['mobile'].grid(row=6, column=1, sticky=tk.EW, padx=5, pady=6)
        ttk.Label(entry_frame, text="Email:").grid(row=6, column=2, sticky=tk.W, padx=5, pady=6)
        self.entries['email'] = ttk.Entry(entry_frame)
        self.entries['email'].grid(row=6, column=3, sticky=tk.EW, padx=5, pady=6)

        # Separator and Info Label
        ttk.Separator(entry_frame, orient=tk.HORIZONTAL).grid(row=7, column=0, columnspan=4, sticky='ew', pady=10)
        ttk.Label(entry_frame, text="* Required fields", font=("Segoe UI", 9, "italic")).grid(row=8, column=0, columnspan=4, sticky=tk.W, padx=5)


        # Button Bar
        btn_bar = ttk.Frame(entry_frame)
        btn_bar.grid(row=9, column=0, columnspan=4, pady=(15, 0), sticky="E")
        add_btn = ttk.Button(btn_bar, text="Add Patient", command=self.add_patient)
        add_btn.pack(side=tk.RIGHT, padx=0)
        cancel_btn = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))

        self.entries['first_name'].focus_set() # Focus first field
        self.bind('<Return>', self.add_patient) # Allow Enter key to submit
        self.bind('<Escape>', lambda e: self.destroy()) # Allow Escape key to cancel

    def add_patient(self, event=None) -> None: # Added event=None for binding
        # Helper to get value or None
        def get_val(key):
            widget = self.entries.get(key)
            if isinstance(widget, tk.StringVar): return widget.get().strip() or None
            # Need to handle DateEntry specifically if its var is stored
            if key == 'birth_date_var': return widget.get().strip() or None
            if isinstance(widget, (ttk.Entry, ttk.Combobox)): return widget.get().strip() or None
            return None # Should not happen for others

        fname = get_val("first_name")
        lname = get_val("last_name")
        birth = get_val("birth_date_var") # Get from StringVar

        if not (fname and lname and birth):
            messagebox.showwarning("Missing Required Data", "First Name, Last Name, and Birth Date are required.", parent=self) # Specify parent
            return

        # Fetch optional fields using get_val
        diag = get_val('diagnosis')
        patient_id_code = get_val('patient_code')
        gender = get_val('gender_var') # Get from StringVar
        address = get_val('address')
        post_number = get_val('post_number')
        city = get_val('city')
        country = get_val('country')
        phone = get_val('phone')
        mobile = get_val('mobile')
        email = get_val('email')

        try:
            self.db.add_patient(
                first_name=fname, last_name=lname, birth_date=birth, diagnosis=diag, gender=gender,
                patient_code=patient_id_code, address=address, post_number=post_number, city=city,
                country=country, phone=phone, mobile=mobile, email=email
                # height and assistive_device are None as they aren't on this form
            )
            self.refresh_callback() # Refresh the main list
            # messagebox.showinfo("Success", "Patient added successfully.", parent=self) # Maybe skip for faster entry
            self.destroy() # Close window on success
        except sqlite3.IntegrityError:
             messagebox.showerror("Save Error", f"A patient with the Patient ID '{patient_id_code}' already exists. Please use a unique ID.", parent=self) # Specify parent
        except Exception as e:
             messagebox.showerror("Error", f"Could not add patient: {e}", parent=self) # Specify parent


# --- Main Application Class ---
class PatientApp:
    """Main application window for managing patients."""

    def __init__(self, root: tk.Tk, db: Database) -> None:
        self.root = root
        self.db = db
        self.root.title("Gait Documentation System")
        # Set initial size, allow resizing down to a minimum
        self.root.geometry("900x650") # Start a bit smaller seems okay now
        self.root.minsize(700, 500) # Minimum allowed size

        # --- Style Configuration (Copied from previous version) ---
        style = ttk.Style(self.root)
        try: style.theme_use("clam")
        except tk.TclError: print("Clam theme not available, using default.")
        BG_COLOR="#f0f0f0"; FG_COLOR="#333333"; HEADER_COLOR="#2a579a"; BUTTON_COLOR="#3a70d1"; BUTTON_ACTIVE="#2a579a"; ENTRY_BG="#ffffff"; TREE_HEADING_BG="#d9d9d9"
        self.root.configure(bg=BG_COLOR)
        style.configure(".", background=BG_COLOR, foreground=FG_COLOR, fieldbackground=ENTRY_BG, font=("Segoe UI", 10))
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background=BUTTON_COLOR, bordercolor=BUTTON_COLOR, lightcolor=BUTTON_COLOR, darkcolor=BUTTON_COLOR, padding=6)
        style.map("TButton", background=[("active", BUTTON_ACTIVE)])
        style.configure("TEntry", borderwidth=1, padding=5); style.map("TEntry", bordercolor=[("focus", HEADER_COLOR)])
        style.configure("TCombobox", padding=5); style.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)], bordercolor=[("focus", HEADER_COLOR)])
        style.configure("TLabelFrame", background=BG_COLOR, borderwidth=1, relief="solid", padding=10)
        style.configure("TLabelFrame.Label", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 11, "bold"))
        style.configure("TNotebook", background=BG_COLOR, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=(10, 5), background="#d9d9d9", foreground="#555555"); style.map("TNotebook.Tab", background=[("selected", BG_COLOR)], foreground=[("selected", HEADER_COLOR)])
        style.configure("Treeview", rowheight=28, fieldbackground=ENTRY_BG, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background=TREE_HEADING_BG, foreground=FG_COLOR, relief="flat"); style.map("Treeview.Heading", background=[("active", "#c0c0c0")])
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground=HEADER_COLOR, background=BG_COLOR)
        style.configure("Author.TLabel", font=("Segoe UI", 9, "bold"), foreground="#333333", background=BG_COLOR)

        # --- Load Icon & Image (Simplified) ---
        try: self._icon = tk.PhotoImage(file=os.path.join(BASE_DIR, "user_photo.png")); self.root.iconphoto(False, self._icon)
        except Exception: self._icon = None
        try: img = tk.PhotoImage(file=os.path.join(BASE_DIR, "user_photo.png")); self.header_img = img.subsample(2, 2)
        except Exception: self.header_img = None

        # --- Menubar ---
        menubar = tk.Menu(self.root)
        # Help menu for usage instructions
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Usage Help", command=self.show_help)
        menubar.add_cascade(label="Help", menu=help_menu)
        # About menu for license and acknowledgments
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="View License", command=self.show_license)
        about_menu.add_command(label="Acknowledgments", command=self.show_acknowledgments)
        menubar.add_cascade(label="About", menu=about_menu)
        self.root.config(menu=menubar)

        self.create_widgets() # Call the updated method

    def create_widgets(self) -> None:
        # Configure root grid to allow list frame to expand
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Main frame holds Header and List Frame vertically
        main_frame = ttk.Frame(self.root, padding=(10, 10))
        main_frame.grid(row=0, column=0, sticky="NSEW")  # Use grid instead of pack
        # Configure the internal rows of main_frame:
        # row 0: header (fixed height)
        # row 1: patients list (expands vertically)
        # row 2: bottom button bar (fixed height)
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=0)
        main_frame.columnconfigure(0, weight=1)

        # --- Header (Stays at top) ---
        header = ttk.Frame(main_frame)
        header.grid(row=0, column=0, sticky="NSEW", pady=(0, 10))
        if self.header_img:
            img_label = ttk.Label(header, image=self.header_img) # Removed background override
            img_label.pack(side=tk.LEFT, padx=(0, 20))

        text_frame = ttk.Frame(header)
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor="w")
        title_label = ttk.Label(text_frame, text="Gait Documentation", style="Header.TLabel")
        title_label.pack(anchor="w")
        desc_text = ("Mehrdad Davoudi\n"
                     "PhD student, Clinic for Orthopaedics, Heidelberg University Hospital, Heidelberg, Germany.\n"
                     "Email: Mehrdad.Davoudi@med.uni-heidelberg.de")
        desc_label = ttk.Label(text_frame, text=desc_text, justify=tk.LEFT, style="Author.TLabel")
        desc_label.pack(anchor="w", pady=(5, 0))

        # --- Patients List Frame (Expands) ---
        list_frame = ttk.LabelFrame(main_frame, text="Patients", padding=(15, 10))
        list_frame.grid(row=1, column=0, sticky="NSEW", pady=10)
        # Configure grid inside list_frame for proper expansion and button placement
        list_frame.rowconfigure(1, weight=1) # Tree frame row expands
        list_frame.columnconfigure(0, weight=1) # Tree frame column expands

        # --- Toolbar (Top of List Frame) ---
        # The toolbar hosts search controls only; the "Add New Patient" button has been moved
        # to the bottom button bar so that it remains clearly visible at all times.
        toolbar_frame = ttk.Frame(list_frame)
        toolbar_frame.grid(row=0, column=0, sticky="NSEW", pady=(0, 10))
        # Search elements...
        ttk.Label(toolbar_frame, text="Search by:").pack(side=tk.LEFT, padx=(0, 5))
        # Map display names to database column names for patient searches.  The
        # "Zip Code" option replaces the older "Post Number" terminology to
        # better reflect international naming conventions.  The mapping values
        # remain the same so the underlying database column continues to be
        # "post_number".
        self.search_field_mapping = {
            "Last Name": "last_name",
            "Patient ID": "patient_code",
            "Diagnosis": "diagnosis",
            "Zip Code": "post_number",
        }
        self.search_field_var = tk.StringVar(value="Last Name")
        self.search_field_combo = ttk.Combobox(
            toolbar_frame,
            textvariable=self.search_field_var,
            values=list(self.search_field_mapping.keys()),
            state="readonly",
            width=12,
        )
        self.search_field_combo.pack(side=tk.LEFT, padx=5)
        self.search_field_combo.bind("<<ComboboxSelected>>", self.refresh_patient_list)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        search_entry.bind("<KeyRelease>", self.refresh_patient_list)
        # Birth date filters...
        ttk.Label(toolbar_frame, text="Birth from:").pack(side=tk.LEFT, padx=(10, 2))
        self.birth_from_var = tk.StringVar(value="1900-01-01")  # Default start
        self.birth_from_entry = DateEntry(toolbar_frame, textvariable=self.birth_from_var)
        self.birth_from_entry.pack(side=tk.LEFT)
        ttk.Label(toolbar_frame, text="to:").pack(side=tk.LEFT, padx=(5, 2))
        self.birth_to_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))  # Default end
        self.birth_to_entry = DateEntry(toolbar_frame, textvariable=self.birth_to_var)
        self.birth_to_entry.pack(side=tk.LEFT)
        # Trigger patient list refresh when date filters change
        self.birth_from_var.trace_add("write", lambda *_: self.refresh_patient_list())
        self.birth_to_var.trace_add("write", lambda *_: self.refresh_patient_list())


        # --- Treeview Frame (Middle, Expands) ---
        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=1, column=0, sticky="NSEW", pady=5) # Use grid, spans column 0
        tree_frame.rowconfigure(0, weight=1) # Treeview expands vertically
        tree_frame.columnconfigure(0, weight=1) # Treeview expands horizontally

        cols = ("id", "name", "dob", "diag", "post_num", "city")
        self.patient_tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.patient_tree.heading("id", text="Patient ID", anchor=tk.W)
        self.patient_tree.heading("name", text="Name", anchor=tk.W)
        self.patient_tree.heading("dob", text="Birth Date", anchor=tk.W)
        self.patient_tree.heading("diag", text="Diagnosis", anchor=tk.W)
        # Display the postal code column as "Zip Code" for clarity
        self.patient_tree.heading("post_num", text="Zip Code", anchor=tk.W)
        self.patient_tree.heading("city", text="City", anchor=tk.W)
        self.patient_tree.column("id", width=100, stretch=False, anchor=tk.W)
        self.patient_tree.column("name", width=200, stretch=True, anchor=tk.W)
        self.patient_tree.column("dob", width=100, stretch=False, anchor=tk.W)
        self.patient_tree.column("diag", width=200, stretch=True, anchor=tk.W)
        self.patient_tree.column("post_num", width=100, stretch=False, anchor=tk.W)
        self.patient_tree.column("city", width=150, stretch=True, anchor=tk.W)

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.patient_tree.yview)
        self.patient_tree.configure(yscrollcommand=scrollbar.set)
        # Use grid for treeview and scrollbar
        self.patient_tree.grid(row=0, column=0, sticky="NSEW")
        scrollbar.grid(row=0, column=1, sticky="NS")

        self.patient_tree.bind("<Double-Button-1>", self.on_patient_double_click)

        # --- Button Bar (Bottom of List Frame, Always Visible) ---
        btn_bar = ttk.Frame(list_frame)
        # Place the button bar below the treeview frame
        btn_bar.grid(row=2, column=0, sticky="NSEW", pady=(10, 0))
        # "Add New Patient" button is placed first on the bar so it is easily discoverable.
        add_btn = ttk.Button(btn_bar, text="Add New Patient", command=self.open_add_patient_window)
        add_btn.pack(side=tk.LEFT, padx=(0, 10))
        edit_btn = ttk.Button(btn_bar, text="Edit Selected Patient", command=self.edit_patient)
        edit_btn.pack(side=tk.LEFT, padx=(0, 10))
        del_btn = ttk.Button(btn_bar, text="Delete Selected Patient", command=self.delete_patient)
        del_btn.pack(side=tk.LEFT, padx=0)

        self.refresh_patient_list() # Initial load

    # *** NEW Method to open the popup ***
    def open_add_patient_window(self) -> None:
        """Opens the Toplevel window for adding a new patient."""
        # This creates the popup. It handles its own logic via the AddPatientWindow class.
        # We pass self.db and self.refresh_patient_list so the popup can interact.
        AddPatientWindow(self.root, self.db, refresh_callback=self.refresh_patient_list)

    # --- Other PatientApp methods remain largely the same ---
    # refresh_patient_list needs to populate the treeview now
    def refresh_patient_list(self, event: tk.Event | None = None) -> None:
        filter_text = self.search_var.get().strip()
        field_display = self.search_field_var.get()
        field = self.search_field_mapping.get(field_display, "last_name")
        start = self.birth_from_var.get().strip()
        end = self.birth_to_var.get().strip()
        self.db.set_birth_range(start if start else None, end if end else None)
        patients = self.db.search_patients(filter_text, field)

        # Clear existing tree items efficiently
        self.patient_tree.delete(*self.patient_tree.get_children())

        # Add new data
        for patient in patients:
            # Unpack based on SELECT * order in database class
            (pid, code, fname, lname, birth, diag, gender, height, device,
             address, post_number, city, country, phone, mobile, email) = patient
            id_display = code if code else f"DB-{pid}"
            name_display = f"{lname}, {fname}"
            # Populate the treeview row, using pid as the item identifier (iid)
            self.patient_tree.insert("", tk.END, iid=pid, values=(
                id_display, name_display, birth, diag or "", post_number or "", city or ""
            ))

    def on_patient_double_click(self, event: tk.Event) -> None:
        selection = self.patient_tree.selection()
        if not selection: return
        patient_id = int(selection[0]) # iid is patient_id
        row_values = self.patient_tree.item(patient_id, "values")
        patient_name = row_values[1] # "Name" column
        PatientDetailWindow(self.root, self.db, patient_id, patient_name)

    def get_selected_patient_id(self) -> int | None:
        selection = self.patient_tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Please select a patient from the list first.")
            return None
        return int(selection[0])

    def edit_patient(self) -> None:
        pid = self.get_selected_patient_id()
        if pid: EditPatientWindow(self.root, self.db, pid, refresh_callback=self.refresh_patient_list)

    def delete_patient(self) -> None:
        pid = self.get_selected_patient_id()
        if not pid: return
        patient_name = self.patient_tree.item(pid, "values")[1]
        if not messagebox.askyesno("Delete Patient", f"Delete {patient_name}?\nALL data will be removed."): return
        try: self.db.delete_patient(pid); self.refresh_patient_list(); messagebox.showinfo("Deleted", f"Patient {patient_name} deleted.")
        except Exception as e: messagebox.showerror("Error", f"Could not delete: {e}")

    def show_help(self) -> None:
        """Display a detailed help guide for using the application.

        The help text provides a brief overview of the major features of the
        program, including adding and editing patients, recording examinations
        and interventions, attaching files, and navigating the timeline.  The
        text is displayed in a scrollable window for easy reading.
        """
        help_win = tk.Toplevel(self.root)
        help_win.title("Help")
        help_win.geometry("650x500")
        help_frame = ttk.Frame(help_win, padding=10)
        help_frame.pack(fill=tk.BOTH, expand=True)
        # Compose a comprehensive help message.  Use blank lines to separate
        # sections and bullets to make key actions stand out.  You can adjust
        # this text to better suit your workflow or translate it into another
        # language as needed.
        help_text = (
            "Gait Documentation System - Help Guide\n\n"
            "This application lets you record and manage patient information,\n"
            "examinations, interventions, and associated files in an organised,\n"
            "centralised database.  The main window lists all patients and\n"
            "provides quick access to common tasks.\n\n"
            "Adding a new patient:\n"
            " • Click the \"Add New Patient\" button at the bottom of the main window to\n"
            "   open a form where you can enter the patient's demographic details.\n"
            "   Fields marked with an asterisk are required.  Optional information\n"
            "   such as address and contact details can be recorded as well.\n\n"
            "Searching for patients:\n"
            " • Use the drop‑down box at the top of the patient list to choose a search\n"
            "   field (last name, diagnosis, patient ID or zip code).  Type into\n"
            "   the adjacent search box to filter the patient list dynamically.\n"
            " • You can also restrict the birth date range using the date pickers.\n\n"
            "Editing or deleting a patient:\n"
            " • Select a patient in the list and click \"Edit Selected Patient\" to open a\n"
            "   form where you can modify their details.  The Save and Cancel buttons\n"
            "   appear at the bottom of the form.\n"
            " • Click \"Delete Selected Patient\" to remove a patient and all associated\n"
            "   examinations, interventions and attachments.  You will be asked to\n"
            "   confirm before the record is permanently deleted.\n\n"
            "Recording examinations and interventions:\n"
            " • Double‑click a patient in the list to open their detail window.  This\n"
            "   window contains tabs for examinations, interventions and a combined\n"
            "   timeline.\n"
            " • In the examinations tab, fill in the form at the top and click\n"
            "   \"Add Exam\" to record a new entry.  The date pickers allow you to\n"
            "   specify the exam date; height and weight (if provided) will be used\n"
            "   to calculate BMI automatically.\n"
            " • The interventions tab works similarly, with a separate form and\n"
            "   \"Add Intervention\" button.\n\n"
            "Working with attachments:\n"
            " • Each exam or intervention can have files attached (for example\n"
            "   reports, images or videos).  Double‑click an entry in the list to\n"
            "   open the attachments manager.\n"
            " • Use the \"Add Attachment...\" button to browse for a file.  A copy of\n"
            "   the selected file will be stored in the application’s local\n"
            "   attachments folder so that it remains accessible even if the original\n"
            "   file is moved or deleted.\n"
            " • Double‑click a file in the attachments list to open it with the\n"
            "   default application on your system.\n\n"
            "Timeline view:\n"
            " • The timeline tab displays both examinations and interventions\n"
            "   chronologically, along with the patient's age at each event.  This\n"
            "   view helps you see the sequence of care over time.\n\n"
            "Backup and data storage:\n"
            " • The application uses a local SQLite database (\"health_records.db\")\n"
            "   stored Users\...\AppData\Local\GaitDocumentationSystem. Your attachments are\n"
            "   saved in a subfolder named \"attachments\" next to the database.\n"
            "For further assistance or to report issues, please contact the developer."
        )
        text = tk.Text(
            help_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            relief="flat",
            bg="#fdfdfd",
        )
        text.pack(fill=tk.BOTH, expand=True)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
        # Add a vertical scrollbar linked to the text widget
        scrollbar = ttk.Scrollbar(text.master, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_license(self) -> None:
        """Display the contents of LICENSE.txt in a pop‑up window.

        This method reads the LICENSE file located in the same directory as
        this script and shows its text in a scrollable window. If the file
        cannot be found, an error message is displayed to the user.
        """
        # Determine the path to the license file
        license_path = os.path.join(BASE_DIR, "LICENSE.txt")
        if not os.path.exists(license_path):
            messagebox.showerror("License Not Found", "The LICENSE.txt file could not be located.")
            return
        # Read the license text
        try:
            with open(license_path, "r", encoding="utf-8") as f:
                license_text = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the license file:\n{e}")
            return
        # Create a new window to display the license
        win = tk.Toplevel(self.root)
        win.title("License")
        win.geometry("600x450")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        # Use a Text widget for scrollable display
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Segoe UI", 10), relief="flat", bg="#fdfdfd")
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, license_text)
        text_widget.config(state=tk.DISABLED)
        # Attach a vertical scrollbar
        scrollbar = ttk.Scrollbar(text_widget.master, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def show_acknowledgments(self) -> None:
        """Display the contents of the acknowledgment file in a pop‑up window.

        This method reads the acknowledgment file (acknowledgment_gdf_donation.txt)
        located in the same directory as this script and shows its text in a
        scrollable window. If the file cannot be found, an error message is
        displayed to the user.
        """
        ack_path = os.path.join(BASE_DIR, "acknowledgment_gdf_donation.txt")
        if not os.path.exists(ack_path):
            messagebox.showerror("Acknowledgments Not Found", "The acknowledgment file could not be located.")
            return
        try:
            with open(ack_path, "r", encoding="utf-8") as f:
                ack_text = f.read()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read the acknowledgment file:\n{e}")
            return
        win = tk.Toplevel(self.root)
        win.title("Acknowledgments")
        win.geometry("600x450")
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        text_widget = tk.Text(frame, wrap=tk.WORD, font=("Segoe UI", 10), relief="flat", bg="#fdfdfd")
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, ack_text)
        text_widget.config(state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(text_widget.master, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# --- Other Classes (PatientDetailWindow, AttachmentWindows, EditWindows) ---
# These remain the same as the previous correct version (v7 / Gait_Documentation.py)
# Make sure their layouts also use grid configure for expansion and button placement if needed.
# (Assuming PatientDetailWindow, AttachmentWindowBase, EditPatientWindow,
#  EditEventWindowBase and subclasses are defined as in the v7 script provided previously,
#  ensuring they use grid row/column configure where appropriate for resizing and
#  that messageboxes specify parent=self)

class PatientDetailWindow(tk.Toplevel):
    """Window to display and manage examinations and interventions for a single patient.

    This window provides three tabs: one for recording examinations, one for recording
    interventions and a combined timeline.  Double‑clicking an examination or
    intervention opens an attachment manager where files can be added or removed.

    The layout has been adjusted to use grid geometry for the list sections so that
    the treeviews expand to fill the available space while the button bars remain
    anchored to the bottom of each list frame.  Attachments are copied into a
    dedicated directory under the application's data folder, ensuring they remain
    accessible even if the source file is moved on the user's machine.
    """

    def __init__(self, parent: tk.Tk | tk.Toplevel, db: Database, patient_id: int, patient_name: str) -> None:
        super().__init__(parent)
        self.db = db
        self.patient_id = patient_id
        self.title(f"Patient Details: {patient_name}")
        # Provide a sensible default size and allow resizing
        self.geometry("950x700")
        self.minsize(800, 600)

        # Fetch the patient's birth date to compute age at events
        patient_data = self.db.get_patient(patient_id)
        self.patient_birth_date = patient_data[4] if patient_data else None

        # Build the UI
        self.create_widgets()

    def create_widgets(self) -> None:
        """Construct the notebook tabs and associated widgets."""
        notebook = ttk.Notebook(self, padding=10)
        notebook.pack(fill=tk.BOTH, expand=True)

        # Exams tab
        exam_frame = ttk.Frame(notebook, padding=(0, 10))
        notebook.add(exam_frame, text="Examinations")
        self.build_exam_tab(exam_frame)

        # Interventions tab
        interv_frame = ttk.Frame(notebook, padding=(0, 10))
        notebook.add(interv_frame, text="Interventions")
        self.build_intervention_tab(interv_frame)

        # Timeline tab
        timeline_frame = ttk.Frame(notebook, padding=(0, 10))
        notebook.add(timeline_frame, text="Timeline")
        self.build_timeline_tab(timeline_frame)

    # --- Helper to compute age at a given event date ---
    def _calculate_age_at_event(self, event_date_str: str) -> str:
        """Return an age string like "5y, 3m" for a given event date."""
        if not self.patient_birth_date or not event_date_str:
            return ""
        try:
            bd = datetime.strptime(self.patient_birth_date, "%Y-%m-%d")
            ed = datetime.strptime(event_date_str, "%Y-%m-%d")
            age_days = (ed - bd).days
            age_years = int(age_days // 365.25)
            age_months = int((age_days % 365.25) // 30.44)
            return f"{age_years}y, {age_months}m"
        except Exception:
            return ""

    # --- Exams Tab ---
    def build_exam_tab(self, frame: ttk.Frame) -> None:
        """Create widgets for adding and listing examinations."""
        # Section to add a new exam
        add_frame = ttk.LabelFrame(frame, text="Add Examination", padding=(15, 10))
        add_frame.pack(fill=tk.X, pady=(0, 10))
        # Grid configuration for add_frame
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        add_frame.columnconfigure(5, weight=1)

        # Row 0: exam type and date
        ttk.Label(add_frame, text="Exam Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.exam_type_entry = ttk.Entry(add_frame, width=30)
        self.exam_type_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(add_frame, text="Exam Date:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.exam_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.exam_date_entry = DateEntry(add_frame, textvariable=self.exam_date_var)
        self.exam_date_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 1: height and weight
        ttk.Label(add_frame, text="Height (cm):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.exam_height_entry = ttk.Entry(add_frame, width=10)
        self.exam_height_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(add_frame, text="Weight (kg):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.exam_weight_entry = ttk.Entry(add_frame, width=10)
        self.exam_weight_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 2: assistive device and BMI
        ttk.Label(add_frame, text="Assistive Device:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.exam_device_entry = ttk.Entry(add_frame)
        self.exam_device_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(add_frame, text="BMI:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.exam_bmi_var = tk.StringVar(value="--")
        self.exam_bmi_label = ttk.Label(add_frame, textvariable=self.exam_bmi_var, font=("Segoe UI", 10, "bold"))
        self.exam_bmi_label.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 0 (col 4-5): examiner
        ttk.Label(add_frame, text="Examiner:").grid(row=0, column=4, sticky="NW", padx=5, pady=5)
        self.exam_examiner_entry = ttk.Entry(add_frame, width=40)
        self.exam_examiner_entry.grid(row=0, column=5, sticky="NSEW", padx=5, pady=5)
        # Row 1-2 (col 4-5): notes
        ttk.Label(add_frame, text="Notes:").grid(row=1, column=4, sticky="NW", padx=5, pady=5)
        self.exam_notes_entry = tk.Text(add_frame, height=3, width=40, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.exam_notes_entry.grid(row=1, column=5, rowspan=2, sticky="NSEW", padx=5, pady=5)

        # Calculate BMI when height or weight changes
        self.exam_height_entry.bind("<KeyRelease>", self.update_exam_bmi)
        self.exam_weight_entry.bind("<KeyRelease>", self.update_exam_bmi)

        # Add exam button
        add_exam_btn = ttk.Button(add_frame, text="Add Exam", command=self.add_exam)
        add_exam_btn.grid(row=3, column=0, columnspan=6, pady=(10, 5), sticky="E")

        # --- Recorded exams list ---
        list_frame = ttk.LabelFrame(frame, text="Recorded Examinations (Double-click to manage attachments)", padding=(15, 10))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Configure grid inside list_frame: row 0 for tree, row 1 for buttons
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=0, column=0, sticky="NSEW")
        # Treeview for exams
        exam_cols = ("date", "age", "type", "examiner", "bmi", "notes")
        self.exam_tree = ttk.Treeview(tree_frame, columns=exam_cols, show="headings")
        self.exam_tree.heading("date", text="Date")
        self.exam_tree.heading("age", text="Age")
        self.exam_tree.heading("type", text="Exam Type")
        self.exam_tree.heading("examiner", text="Examiner")
        self.exam_tree.heading("bmi", text="BMI")
        self.exam_tree.heading("notes", text="Notes")
        # Column widths
        self.exam_tree.column("date", width=100, stretch=False, anchor=tk.W)
        self.exam_tree.column("age", width=80, stretch=False, anchor=tk.W)
        self.exam_tree.column("type", width=200, stretch=True, anchor=tk.W)
        self.exam_tree.column("examiner", width=150, stretch=True, anchor=tk.W)
        self.exam_tree.column("bmi", width=70, stretch=False, anchor=tk.W)
        self.exam_tree.column("notes", width=300, stretch=True, anchor=tk.W)
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.exam_tree.yview)
        self.exam_tree.configure(yscrollcommand=scrollbar.set)
        self.exam_tree.grid(row=0, column=0, sticky="NSEW")
        scrollbar.grid(row=0, column=1, sticky="NS")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        # Bind double click to open attachments
        self.exam_tree.bind("<Double-Button-1>", self.on_exam_double_click)

        # Button bar at bottom of list_frame
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="W", pady=(10, 0))
        edit_exam_btn = ttk.Button(btn_frame, text="Edit Selected", command=self.edit_exam)
        edit_exam_btn.pack(side=tk.LEFT, padx=0)
        del_exam_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_exam)
        del_exam_btn.pack(side=tk.LEFT, padx=5)

        # Load data
        self.refresh_exams()

    def refresh_exams(self) -> None:
        """Refresh the examinations treeview."""
        # Clear existing
        for item in self.exam_tree.get_children():
            self.exam_tree.delete(item)
        # Fetch from database
        exams = self.db.get_exams(self.patient_id)
        # Each row from the database returns 10 columns: (exam_id, patient_id, exam_type,
        # exam_date, notes, height_cm, weight_kg, assistive_device, bmi, examiner).
        # We include patient_id in unpacking to correctly align subsequent values.
        for exam in exams:
            (
                exam_id,
                _patient_id,
                exam_type,
                exam_date,
                notes,
                height_cm,
                weight_kg,
                device,
                bmi,
                examiner,
            ) = exam
            age_str = self._calculate_age_at_event(exam_date)
            bmi_str = f"{bmi:.1f}" if bmi else "--"
            notes_preview = (notes.split("\n")[0] if notes else "")[:50] + (
                "..." if notes and len(notes) > 50 else ""
            )
            self.exam_tree.insert(
                "",
                tk.END,
                iid=exam_id,
                values=(
                    exam_date,
                    age_str,
                    exam_type,
                    examiner if examiner else "",
                    bmi_str,
                    notes_preview,
                ),
            )

    def add_exam(self) -> None:
        """Add a new examination using form values."""
        exam_type = self.exam_type_entry.get().strip()
        exam_date = self.exam_date_var.get().strip()
        notes = self.exam_notes_entry.get("1.0", tk.END).strip()
        examiner = self.exam_examiner_entry.get().strip() or None
        if not (exam_type and exam_date):
            messagebox.showwarning("Missing data", "Exam type and date are required.")
            return
        # Validate height and weight
        height = None; weight = None
        h_text = self.exam_height_entry.get().strip()
        w_text = self.exam_weight_entry.get().strip()
        try:
            height = float(h_text) if h_text else None
        except Exception:
            messagebox.showwarning("Invalid height", "Height must be a number.")
            return
        try:
            weight = float(w_text) if w_text else None
        except Exception:
            messagebox.showwarning("Invalid weight", "Weight must be a number.")
            return
        device = self.exam_device_entry.get().strip() or None
        # Insert into DB
        self.db.add_exam(self.patient_id, exam_type, exam_date, notes, height, weight, device, examiner)
        # Clear form
        self.exam_type_entry.delete(0, tk.END)
        self.exam_date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self.exam_height_entry.delete(0, tk.END)
        self.exam_weight_entry.delete(0, tk.END)
        self.exam_device_entry.delete(0, tk.END)
        self.exam_notes_entry.delete("1.0", tk.END)
        self.exam_examiner_entry.delete(0, tk.END)
        self.exam_bmi_var.set("--")
        # Refresh list
        self.refresh_exams()
        self.refresh_timeline()

    def update_exam_bmi(self, event: tk.Event | None = None) -> None:
        """Compute BMI for exam fields and update the label."""
        h_text = self.exam_height_entry.get().strip()
        w_text = self.exam_weight_entry.get().strip()
        try:
            height = float(h_text) if h_text else None
            weight = float(w_text) if w_text else None
            bmi = None
            if height and weight and height > 0:
                bmi = weight / ((height / 100.0) ** 2)
            self.exam_bmi_var.set(f"{bmi:.1f}" if bmi else "--")
        except Exception:
            self.exam_bmi_var.set("--")

    def get_selected_exam_id(self) -> int | None:
        selection = self.exam_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an examination from the list first.")
            return None
        return int(selection[0])

    def on_exam_double_click(self, event: tk.Event) -> None:
        exam_id = self.get_selected_exam_id()
        if exam_id:
            ExamAttachmentWindow(self, self.db, exam_id)

    def edit_exam(self) -> None:
        exam_id = self.get_selected_exam_id()
        if exam_id:
            EditExamWindow(self, self.db, exam_id, refresh_callback=lambda: [self.refresh_exams(), self.refresh_timeline()])

    def delete_exam(self) -> None:
        exam_id = self.get_selected_exam_id()
        if not exam_id:
            return
        # Ask for confirmation
        if not messagebox.askyesno("Delete Examination", "Are you sure you want to delete this examination?"):
            return
        try:
            self.db.delete_exam(exam_id)
            self.refresh_exams()
            self.refresh_timeline()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete examination: {e}")

    # --- Interventions Tab ---
    def build_intervention_tab(self, frame: ttk.Frame) -> None:
        """Create widgets for adding and listing interventions."""
        add_frame = ttk.LabelFrame(frame, text="Add Intervention", padding=(15, 10))
        add_frame.pack(fill=tk.X, pady=(0, 10))
        add_frame.columnconfigure(1, weight=1)
        add_frame.columnconfigure(3, weight=1)
        add_frame.columnconfigure(5, weight=1)

        # Row 0: type and date
        ttk.Label(add_frame, text="Intervention Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.intervention_type_entry = ttk.Entry(add_frame, width=30)
        self.intervention_type_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(add_frame, text="Date:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.intervention_date_var = tk.StringVar(value=datetime.today().strftime("%Y-%m-%d"))
        self.intervention_date_entry = DateEntry(add_frame, textvariable=self.intervention_date_var)
        self.intervention_date_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 1: height and weight
        ttk.Label(add_frame, text="Height (cm):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.intervention_height_entry = ttk.Entry(add_frame, width=10)
        self.intervention_height_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(add_frame, text="Weight (kg):").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        self.intervention_weight_entry = ttk.Entry(add_frame, width=10)
        self.intervention_weight_entry.grid(row=1, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 2: assistive device and BMI
        ttk.Label(add_frame, text="Assistive Device:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.intervention_device_entry = ttk.Entry(add_frame)
        self.intervention_device_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=5)
        ttk.Label(add_frame, text="BMI:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        self.intervention_bmi_var = tk.StringVar(value="--")
        self.intervention_bmi_label = ttk.Label(add_frame, textvariable=self.intervention_bmi_var, font=("Segoe UI", 10, "bold"))
        self.intervention_bmi_label.grid(row=2, column=3, sticky=tk.W, padx=5, pady=5)

        # Row 0 (col 4-5): operator
        ttk.Label(add_frame, text="Treatment By:").grid(row=0, column=4, sticky="NW", padx=5, pady=5)
        self.intervention_operator_entry = ttk.Entry(add_frame, width=40)
        self.intervention_operator_entry.grid(row=0, column=5, sticky="NSEW", padx=5, pady=5)
        # Row 1-2 (col 4-5): notes
        ttk.Label(add_frame, text="Notes:").grid(row=1, column=4, sticky="NW", padx=5, pady=5)
        self.intervention_notes_entry = tk.Text(add_frame, height=3, width=40, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.intervention_notes_entry.grid(row=1, column=5, rowspan=2, sticky="NSEW", padx=5, pady=5)

        # Bind BMI update
        self.intervention_height_entry.bind("<KeyRelease>", self.update_intervention_bmi)
        self.intervention_weight_entry.bind("<KeyRelease>", self.update_intervention_bmi)

        # Add intervention button
        add_interv_btn = ttk.Button(add_frame, text="Add Intervention", command=self.add_intervention)
        add_interv_btn.grid(row=3, column=0, columnspan=6, pady=(10, 5), sticky="E")

        # Recorded interventions list
        list_frame = ttk.LabelFrame(frame, text="Recorded Interventions (Double-click to manage attachments)", padding=(15, 10))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)

        tree_frame = ttk.Frame(list_frame)
        tree_frame.grid(row=0, column=0, sticky="NSEW")
        interv_cols = ("date", "age", "type", "operator", "bmi", "notes")
        self.interv_tree = ttk.Treeview(tree_frame, columns=interv_cols, show="headings")
        self.interv_tree.heading("date", text="Date")
        self.interv_tree.heading("age", text="Age")
        self.interv_tree.heading("type", text="Type")
        self.interv_tree.heading("operator", text="Treatment By")
        self.interv_tree.heading("bmi", text="BMI")
        self.interv_tree.heading("notes", text="Notes")
        self.interv_tree.column("date", width=100, stretch=False, anchor=tk.W)
        self.interv_tree.column("age", width=80, stretch=False, anchor=tk.W)
        self.interv_tree.column("type", width=200, stretch=True, anchor=tk.W)
        self.interv_tree.column("operator", width=150, stretch=True, anchor=tk.W)
        self.interv_tree.column("bmi", width=70, stretch=False, anchor=tk.W)
        self.interv_tree.column("notes", width=300, stretch=True, anchor=tk.W)
        interv_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.interv_tree.yview)
        self.interv_tree.configure(yscrollcommand=interv_scroll.set)
        self.interv_tree.grid(row=0, column=0, sticky="NSEW")
        interv_scroll.grid(row=0, column=1, sticky="NS")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        # Double click event
        self.interv_tree.bind("<Double-Button-1>", self.on_intervention_double_click)

        # Button bar
        btn_frame = ttk.Frame(list_frame)
        btn_frame.grid(row=1, column=0, columnspan=2, sticky="W", pady=(10, 0))
        edit_btn = ttk.Button(btn_frame, text="Edit Selected", command=self.edit_intervention)
        edit_btn.pack(side=tk.LEFT, padx=0)
        del_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_intervention)
        del_btn.pack(side=tk.LEFT, padx=5)

        # Load data
        self.refresh_interventions()

    def refresh_interventions(self) -> None:
        for item in self.interv_tree.get_children():
            self.interv_tree.delete(item)
        interventions = self.db.get_interventions(self.patient_id)
        for interv in interventions:
            # Interventions have 10 columns: (intervention_id, patient_id, intervention_type,
            # intervention_date, notes, height_cm, weight_kg, assistive_device, bmi, operator)
            (
                interv_id,
                _patient_id,
                interv_type,
                interv_date,
                notes,
                height_cm,
                weight_kg,
                device,
                bmi,
                operator,
            ) = interv
            age_str = self._calculate_age_at_event(interv_date)
            bmi_str = f"{bmi:.1f}" if bmi else "--"
            notes_preview = (notes.split("\n")[0] if notes else "")[:50] + (
                "..." if notes and len(notes) > 50 else ""
            )
            self.interv_tree.insert(
                "",
                tk.END,
                iid=interv_id,
                values=(
                    interv_date,
                    age_str,
                    interv_type,
                    operator if operator else "",
                    bmi_str,
                    notes_preview,
                ),
            )

    def add_intervention(self) -> None:
        interv_type = self.intervention_type_entry.get().strip()
        interv_date = self.intervention_date_var.get().strip()
        notes = self.intervention_notes_entry.get("1.0", tk.END).strip()
        operator = self.intervention_operator_entry.get().strip() or None
        if not (interv_type and interv_date):
            messagebox.showwarning("Missing data", "Intervention type and date are required.")
            return
        # Validate height/weight
        height = None; weight = None
        h_text = self.intervention_height_entry.get().strip()
        w_text = self.intervention_weight_entry.get().strip()
        try:
            height = float(h_text) if h_text else None
        except Exception:
            messagebox.showwarning("Invalid height", "Height must be a number.")
            return
        try:
            weight = float(w_text) if w_text else None
        except Exception:
            messagebox.showwarning("Invalid weight", "Weight must be a number.")
            return
        device = self.intervention_device_entry.get().strip() or None
        self.db.add_intervention(self.patient_id, interv_type, interv_date, notes, height, weight, device, operator)
        # Clear form
        self.intervention_type_entry.delete(0, tk.END)
        self.intervention_date_var.set(datetime.today().strftime("%Y-%m-%d"))
        self.intervention_height_entry.delete(0, tk.END)
        self.intervention_weight_entry.delete(0, tk.END)
        self.intervention_device_entry.delete(0, tk.END)
        self.intervention_notes_entry.delete("1.0", tk.END)
        self.intervention_operator_entry.delete(0, tk.END)
        self.intervention_bmi_var.set("--")
        # Refresh lists
        self.refresh_interventions()
        self.refresh_timeline()

    def update_intervention_bmi(self, event: tk.Event | None = None) -> None:
        h_text = self.intervention_height_entry.get().strip()
        w_text = self.intervention_weight_entry.get().strip()
        try:
            height = float(h_text) if h_text else None
            weight = float(w_text) if w_text else None
            bmi = None
            if height and weight and height > 0:
                bmi = weight / ((height / 100.0) ** 2)
            self.intervention_bmi_var.set(f"{bmi:.1f}" if bmi else "--")
        except Exception:
            self.intervention_bmi_var.set("--")

    def get_selected_intervention_id(self) -> int | None:
        selection = self.interv_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an intervention from the list first.")
            return None
        return int(selection[0])

    def on_intervention_double_click(self, event: tk.Event) -> None:
        interv_id = self.get_selected_intervention_id()
        if interv_id:
            InterventionAttachmentWindow(self, self.db, interv_id)

    def edit_intervention(self) -> None:
        interv_id = self.get_selected_intervention_id()
        if interv_id:
            EditInterventionWindow(self, self.db, interv_id, refresh_callback=lambda: [self.refresh_interventions(), self.refresh_timeline()])

    def delete_intervention(self) -> None:
        interv_id = self.get_selected_intervention_id()
        if not interv_id:
            return
        if not messagebox.askyesno("Delete Intervention", "Are you sure you want to delete this intervention?"):
            return
        try:
            self.db.delete_intervention(interv_id)
            self.refresh_interventions()
            self.refresh_timeline()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete intervention: {e}")

    # --- Timeline Tab ---
    def build_timeline_tab(self, frame: ttk.Frame) -> None:
        """Create the combined timeline treeview."""
        list_frame = ttk.LabelFrame(frame, text="Combined Patient Timeline", padding=(15, 10))
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        lbl = ttk.Label(list_frame, text="Combined chronological list of all examinations and interventions. Double-click an item to view its attachments.")
        lbl.pack(pady=(0,10), anchor=tk.W)
        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        timeline_cols = ("date", "age", "event_type", "description", "person", "notes")
        self.timeline_tree = ttk.Treeview(tree_frame, columns=timeline_cols, show="headings")
        self.timeline_tree.heading("date", text="Date")
        self.timeline_tree.heading("age", text="Age")
        self.timeline_tree.heading("event_type", text="Event Type")
        self.timeline_tree.heading("description", text="Description")
        self.timeline_tree.heading("person", text="Examiner/Operator")
        self.timeline_tree.heading("notes", text="Notes")
        self.timeline_tree.column("date", width=100, stretch=False, anchor=tk.W)
        self.timeline_tree.column("age", width=80, stretch=False, anchor=tk.W)
        self.timeline_tree.column("event_type", width=110, stretch=False, anchor=tk.W)
        self.timeline_tree.column("description", width=250, stretch=True, anchor=tk.W)
        self.timeline_tree.column("person", width=150, stretch=True, anchor=tk.W)
        self.timeline_tree.column("notes", width=300, stretch=True, anchor=tk.W)
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.timeline_tree.yview)
        self.timeline_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.timeline_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.timeline_tree.bind("<Double-Button-1>", self.on_timeline_double_click)
        # Tag colors
        self.timeline_tree.tag_configure("Exam", foreground="#00529B", background="#E6F0F7")
        self.timeline_tree.tag_configure("Intervention", foreground="#9F3A00", background="#F7EDE6")
        # Populate
        self.refresh_timeline()

    def refresh_timeline(self) -> None:
        """Refresh the combined timeline with both exams and interventions."""
        for item in self.timeline_tree.get_children():
            self.timeline_tree.delete(item)
        events: list[tuple[str, str, int, str, str, str]] = []  # date, label, id, description, notes, person
        # Exams
        for exam in self.db.get_exams(self.patient_id):
            # Unpack 10 columns: (exam_id, patient_id, exam_type, exam_date, notes,
            # height_cm, weight_kg, assistive_device, bmi, examiner)
            (
                exam_id,
                _patient_id,
                exam_type,
                exam_date,
                notes,
                _height_cm,
                _weight_kg,
                _device,
                _bmi,
                examiner,
            ) = exam
            events.append(
                (
                    exam_date,
                    "Exam",
                    exam_id,
                    exam_type,
                    notes if notes else "",
                    examiner if examiner else "",
                )
            )
        # Interventions
        for interv in self.db.get_interventions(self.patient_id):
            (
                interv_id,
                _patient_id,
                interv_type,
                interv_date,
                notes,
                _height_cm,
                _weight_kg,
                _device,
                _bmi,
                operator,
            ) = interv
            events.append(
                (
                    interv_date,
                    "Intervention",
                    interv_id,
                    interv_type,
                    notes if notes else "",
                    operator if operator else "",
                )
            )
        events.sort(key=lambda x: x[0], reverse=True)
        self.timeline_event_map = {}
        for (date, event_label, event_id, description, notes, person) in events:
            age_str = self._calculate_age_at_event(date)
            notes_preview = (notes.split("\n")[0])[:50] + ("..." if len(notes) > 50 else "")
            iid = f"{event_label}_{event_id}"
            tag = event_label
            self.timeline_tree.insert("", tk.END, iid=iid, values=(
                date, age_str, event_label, description, person, notes_preview
            ), tags=(tag,))
            self.timeline_event_map[iid] = (event_label, event_id)

    def on_timeline_double_click(self, event: tk.Event) -> None:
        selection = self.timeline_tree.selection()
        if not selection:
            return
        iid = selection[0]
        if iid not in self.timeline_event_map:
            return
        event_type, event_id = self.timeline_event_map[iid]
        if event_type == "Exam":
            ExamAttachmentWindow(self, self.db, event_id)
        elif event_type == "Intervention":
            InterventionAttachmentWindow(self, self.db, event_id)


class AttachmentWindowBase(tk.Toplevel):
    """Base window for viewing and managing attachments for an exam or intervention."""

    def __init__(self, parent: tk.Toplevel | tk.Tk, db: Database, event_id: int, event_type: str) -> None:
        super().__init__(parent)
        self.db = db
        self.event_id = event_id
        # event_type is either "Exam" or "Intervention"
        self.event_type = event_type
        # Use a more generic title without the numeric identifier.  The ID is still
        # stored on the instance for database operations, but the user does not
        # need to see it in the window title.
        self.title(f"Attachments for {event_type}")
        self.geometry("650x380")
        self.minsize(500, 300)
        # Make modal
        self.grab_set()
        self.transient(parent)
        frame = ttk.Frame(self, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        # Grid config: row 1 grows, row 2 for buttons
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        # Descriptive label for attachments; omit the numeric event identifier.  The
        # wording explains that files are attached to the current exam or
        # intervention and provides instructions for opening them.
        lbl_text = (
            f"Files attached to this {self.event_type.lower()}. Double-click to open."
        )
        lbl = ttk.Label(frame, text=lbl_text)
        lbl.grid(row=0, column=0, sticky=tk.W, pady=(0, 10))
        # Tree frame and treeview
        tree_frame = ttk.Frame(frame)
        tree_frame.grid(row=1, column=0, sticky="NSEW")
        attach_cols = ("description", "path")
        self.attach_tree = ttk.Treeview(
            tree_frame, columns=attach_cols, show="headings", selectmode="browse"
        )
        # Show headers for both columns: description and full file path.  This allows
        # users to verify the location of the stored attachment.  The path column
        # can be resized by the user because stretch is enabled.
        self.attach_tree.heading("description", text="Description")
        self.attach_tree.heading("path", text="File Path")
        # Configure columns.  The description column has a modest fixed width,
        # while the path column takes up the remaining space and stretches.  Both
        # columns align their text to the left.
        self.attach_tree.column(
            "description",
            width=200,
            stretch=False,
            anchor=tk.W,
        )
        self.attach_tree.column(
            "path",
            width=350,
            stretch=True,
            anchor=tk.W,
        )
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.attach_tree.yview)
        self.attach_tree.configure(yscrollcommand=scrollbar.set)
        self.attach_tree.grid(row=0, column=0, sticky="NSEW")
        scrollbar.grid(row=0, column=1, sticky="NS")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        # Bind double click to open file
        self.attach_tree.bind("<Double-Button-1>", self.on_double_click)
        # Button bar
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        add_btn = ttk.Button(btn_frame, text="Add Attachment...", command=self.add_attachment)
        add_btn.pack(side=tk.LEFT, padx=0)
        del_btn = ttk.Button(btn_frame, text="Delete Selected", command=self.delete_attachment)
        del_btn.pack(side=tk.LEFT, padx=5)
        # Populate
        self.refresh_attachments()

    def refresh_attachments(self) -> None:
        """Load attachments from the database into the treeview."""
        for item in self.attach_tree.get_children():
            self.attach_tree.delete(item)
        if self.event_type == "Exam":
            attachments = self.db.get_exam_attachments(self.event_id)
        else:
            attachments = self.db.get_intervention_attachments(self.event_id)
        for (fid, path, desc) in attachments:
            self.attach_tree.insert("", tk.END, iid=fid, values=(desc, path))

    def add_attachment(self) -> None:
        """Prompt the user to select a file and attach it to this event.

        The selected file is copied into a local attachments folder under the
        application's data directory (alongside the database).  This ensures
        that the attachment remains available even if the original file is
        moved or deleted on the user's system.
        """
        file_path = filedialog.askopenfilename(
            title=f"Select a file to attach to this {self.event_type.lower()}",
            filetypes=[
                ("All files", "*.*"),
                ("PDF", "*.pdf"),
                ("Images", "*.png;*.jpg;*.jpeg;*.gif"),
                ("Videos", "*.mp4;*.avi;*.mov;*.mkv"),
            ],
        )
        if not file_path:
            return
        # Description defaults to the original filename
        desc = os.path.basename(file_path)
        try:
            # Determine the base directory for attachments: use the directory
            # containing this script rather than the user's application data or
            # working directory.  This ensures attachments live alongside the
            # program code (and eventual executable) and are kept together when
            # the application folder is moved.  See the BASE_DIR constant at
            # the top of the file for its definition.
            base_dir = Path(BASE_DIR)
            sub = "exams" if self.event_type == "Exam" else "interventions"
            # Build a meaningful folder hierarchy for attachments.  Include
            # the patient identifier (patient_code if available, otherwise the
            # numeric patient_id) and the date of the exam or intervention.
            # This makes it easier to navigate attachments on disk and trace
            # them back to a specific patient and event.
            # Retrieve the event record to extract patient_id and date
            if self.event_type == "Exam":
                rec = self.db.get_exam(self.event_id)
                # rec is (exam_id, patient_id, exam_type, exam_date, notes, ...)
                if rec:
                    _eid, pid, _etype, event_date, *_rest = rec
                else:
                    pid, event_date = None, None
            else:
                rec = self.db.get_intervention(self.event_id)
                # rec is (intervention_id, patient_id, intervention_type, intervention_date, notes, ...)
                if rec:
                    _iid, pid, _itype, event_date, *_rest = rec
                else:
                    pid, event_date = None, None
            # Get the patient's code (a human‑readable ID) if available
            patient_code = None
            if pid is not None:
                pat = self.db.get_patient(pid)
                if pat:
                    # pat is (patient_id, patient_code, first_name, last_name, ...)
                    _pid, pcode, *_ = pat
                    patient_code = pcode if pcode else str(pid)
                else:
                    patient_code = str(pid)
            else:
                patient_code = "unknown"
            # Use the event date (YYYY‑MM‑DD) or a placeholder if unavailable
            date_part = event_date if event_date else "unknown_date"
            attachments_dir = base_dir / "attachments" / sub / patient_code / date_part
            attachments_dir.mkdir(parents=True, exist_ok=True)
            dest_path = attachments_dir / os.path.basename(file_path)
            # Ensure unique filename to avoid overwriting existing files
            if dest_path.exists():
                stem = dest_path.stem
                ext = dest_path.suffix
                counter = 1
                while dest_path.exists():
                    dest_path = attachments_dir / f"{stem}_{counter}{ext}"
                    counter += 1
            shutil.copy2(file_path, dest_path)
            # Insert into DB using the copied path
            if self.event_type == "Exam":
                self.db.add_exam_attachment(self.event_id, str(dest_path), desc)
            else:
                self.db.add_intervention_attachment(self.event_id, str(dest_path), desc)
            messagebox.showinfo("Attached", f"File attached: {desc}")
            self.refresh_attachments()
        except Exception as e:
            messagebox.showerror("Error", f"Could not attach file: {e}")

    def delete_attachment(self) -> None:
        """Delete the selected attachment from the database and disk."""
        selection = self.attach_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select an attachment to delete.")
            return
        file_id = int(selection[0])
        values = self.attach_tree.item(file_id, "values")
        desc = values[0]
        path = values[1]
        if not messagebox.askyesno("Delete Attachment", f"Are you sure you want to delete this attachment?\n\n{desc}"):
            return
        try:
            # Remove from DB
            if self.event_type == "Exam":
                self.db.delete_exam_attachment(file_id)
            else:
                self.db.delete_intervention_attachment(file_id)
            # Remove file from disk if it exists
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    # If removal fails, ignore and continue
                    pass
            self.refresh_attachments()
        except Exception as e:
            messagebox.showerror("Error", f"Could not delete attachment: {e}")

    def on_double_click(self, event: tk.Event) -> None:
        selection = self.attach_tree.selection()
        if not selection:
            return
        item_id = selection[0]
        values = self.attach_tree.item(item_id, "values")
        path = values[1]
        self.open_file(path)

    def open_file(self, path: str) -> None:
        """Open the file at the given path with the default system application."""
        try:
            if not os.path.exists(path):
                messagebox.showerror("File Not Found", f"Could not find file at path:\n{path}")
                return
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.call(["open", path])
            else:
                subprocess.call(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {e}")

class ExamAttachmentWindow(AttachmentWindowBase):
    def __init__(self, parent: tk.Toplevel | tk.Tk, db: Database, exam_id: int) -> None:
        super().__init__(parent, db, exam_id, "Exam")

class InterventionAttachmentWindow(AttachmentWindowBase):
    def __init__(self, parent: tk.Toplevel | tk.Tk, db: Database, intervention_id: int) -> None:
        super().__init__(parent, db, intervention_id, "Intervention")

class EditPatientWindow(tk.Toplevel):
    """Window to edit a patient's demographic information."""
    def __init__(self, parent: tk.Widget, db: Database, patient_id: int, refresh_callback) -> None:
        super().__init__(parent)
        self.db = db
        self.patient_id = patient_id
        self.refresh_callback = refresh_callback
        self.title("Edit Patient")
        # Style and size similar to the AddPatientWindow for a consistent look.
        # Set a fixed size large enough to accommodate all fields without
        # requiring scrolling.  Disallow resizing to keep the layout intact.
        self.geometry("550x600")
        self.resizable(False, False)
        # Make modal
        self.grab_set()
        self.transient(parent)
        # Retrieve the patient's existing data
        data = db.get_patient(patient_id)
        if not data:
            messagebox.showerror("Error", "Patient not found.")
            self.destroy()
            return
        (
            _pid,
            patient_code,
            fname,
            lname,
            birth,
            diag,
            gender,
            height,
            device,
            address,
            post_number,
            city,
            country,
            phone,
            mobile,
            email,
        ) = data
        # Build a form similar to AddPatientWindow with two columns of fields
        entry_frame = ttk.Frame(self, padding=(20, 15))
        entry_frame.pack(fill=tk.BOTH, expand=True)
        entry_frame.columnconfigure(1, weight=1)
        entry_frame.columnconfigure(3, weight=1)
        # Store entry widgets and variables
        self.entries: dict[str, tk.Any] = {}
        # Row 0: First and Last Name
        ttk.Label(entry_frame, text="First Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        first_entry = ttk.Entry(entry_frame)
        if fname:
            first_entry.insert(0, fname)
        first_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
        self.entries["first_name"] = first_entry
        ttk.Label(entry_frame, text="Last Name:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=6)
        last_entry = ttk.Entry(entry_frame)
        if lname:
            last_entry.insert(0, lname)
        last_entry.grid(row=0, column=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["last_name"] = last_entry
        # Row 1: Birth Date and Gender
        ttk.Label(entry_frame, text="Birth Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        self.birth_var = tk.StringVar(value=birth)
        birth_entry = DateEntry(entry_frame, textvariable=self.birth_var)
        birth_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=6)
        self.entries["birth_date_var"] = self.birth_var
        ttk.Label(entry_frame, text="Gender:").grid(row=1, column=2, sticky=tk.W, padx=5, pady=6)
        self.gender_var = tk.StringVar(value=gender if gender else "")
        gender_combo = ttk.Combobox(
            entry_frame,
            textvariable=self.gender_var,
            values=["", "Female", "Male", "Other"],
            state="readonly",
            width=18,
        )
        gender_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=6)
        self.entries["gender_var"] = self.gender_var
        # Row 2: Diagnosis and Patient ID
        ttk.Label(entry_frame, text="Diagnosis:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        diag_entry = ttk.Entry(entry_frame)
        if diag:
            diag_entry.insert(0, diag)
        diag_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
        self.entries["diagnosis"] = diag_entry
        ttk.Label(entry_frame, text="Patient ID:").grid(row=2, column=2, sticky=tk.W, padx=5, pady=6)
        pid_entry = ttk.Entry(entry_frame)
        if patient_code:
            pid_entry.insert(0, patient_code)
        pid_entry.grid(row=2, column=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["patient_code"] = pid_entry
        # Row 3: Address (span columns)
        ttk.Label(entry_frame, text="Address:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=6)
        address_entry = ttk.Entry(entry_frame)
        if address:
            address_entry.insert(0, address)
        address_entry.grid(row=3, column=1, columnspan=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["address"] = address_entry
        # Row 4: Zip Code and City.  Use "Zip Code" in the UI but retain the
        # underlying key 'post_number' for database compatibility.
        ttk.Label(entry_frame, text="Zip Code:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=6)
        post_entry = ttk.Entry(entry_frame)
        if post_number:
            post_entry.insert(0, post_number)
        post_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=6)
        self.entries["post_number"] = post_entry
        ttk.Label(entry_frame, text="City:").grid(row=4, column=2, sticky=tk.W, padx=5, pady=6)
        city_entry = ttk.Entry(entry_frame)
        if city:
            city_entry.insert(0, city)
        city_entry.grid(row=4, column=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["city"] = city_entry
        # Row 5: Country and Phone
        ttk.Label(entry_frame, text="Country:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=6)
        country_entry = ttk.Entry(entry_frame)
        if country:
            country_entry.insert(0, country)
        country_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=6)
        self.entries["country"] = country_entry
        ttk.Label(entry_frame, text="Phone:").grid(row=5, column=2, sticky=tk.W, padx=5, pady=6)
        phone_entry = ttk.Entry(entry_frame)
        if phone:
            phone_entry.insert(0, phone)
        phone_entry.grid(row=5, column=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["phone"] = phone_entry
        # Row 6: Mobile and Email
        ttk.Label(entry_frame, text="Mobile:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=6)
        mobile_entry = ttk.Entry(entry_frame)
        if mobile:
            mobile_entry.insert(0, mobile)
        mobile_entry.grid(row=6, column=1, sticky=tk.EW, padx=5, pady=6)
        self.entries["mobile"] = mobile_entry
        ttk.Label(entry_frame, text="Email:").grid(row=6, column=2, sticky=tk.W, padx=5, pady=6)
        email_entry = ttk.Entry(entry_frame)
        if email:
            email_entry.insert(0, email)
        email_entry.grid(row=6, column=3, sticky=tk.EW, padx=5, pady=6)
        self.entries["email"] = email_entry
        # Bottom button bar inside entry_frame
        btn_bar = ttk.Frame(entry_frame)
        btn_bar.grid(row=7, column=0, columnspan=4, pady=(15, 0), sticky="E")
        save_btn = ttk.Button(btn_bar, text="Save", command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=0)
        cancel_btn = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def save(self) -> None:
        # Helper to fetch value from entries
        def get_val(key: str) -> str | None:
            widget = self.entries[key]
            if isinstance(widget, tk.StringVar):
                return widget.get().strip() or None
            return widget.get().strip() or None
        fname = get_val("first_name")
        lname = get_val("last_name")
        # Birth date is stored in a StringVar under the key 'birth_date_var'
        birth = get_val("birth_date_var")
        if not (fname and lname and birth):
            messagebox.showwarning("Missing data", "First name, last name and birth date are required.")
            return
        try:
            self.db.update_patient(
                self.patient_id,
                fname, lname, birth,
                get_val("diagnosis"),
                get_val("gender_var"),
                get_val("patient_code"),
                get_val("address"),
                get_val("post_number"),
                get_val("city"),
                get_val("country"),
                get_val("phone"),
                get_val("mobile"),
                get_val("email"),
            )
        except sqlite3.IntegrityError:
            # If the chosen patient code already exists, inform the user.  Use the
            # updated key name 'patient_code' when fetching the duplicate value.
            duplicate_code = get_val("patient_code")
            messagebox.showerror(
                "Save Error",
                f"A patient with the Patient ID '{duplicate_code}' already exists. Please use a unique ID.",
            )
            return
        self.refresh_callback()
        messagebox.showinfo("Updated", "Patient information updated.")
        self.destroy()

class EditEventWindowBase(tk.Toplevel):
    """Base window for editing an existing examination or intervention."""
    def __init__(self, parent: tk.Widget, db: Database, event_id: int, event_type: str, refresh_callback) -> None:
        super().__init__(parent)
        self.db = db
        self.event_id = event_id
        self.event_type = event_type  # "Examination" or "Intervention"
        self.refresh_callback = refresh_callback
        self.title(f"Edit {event_type}")
        self.geometry("500x600")
        self.minsize(450, 500)
        # Modal
        self.grab_set()
        self.transient(parent)
        # Fetch existing data
        if event_type == "Examination":
            data = db.get_exam(event_id)
        else:
            data = db.get_intervention(event_id)
        if not data:
            messagebox.showerror("Error", f"{event_type} not found.")
            self.destroy()
            return
        (_, _, type_val, date_val, notes_val, height_val, weight_val, device_val, person_val) = data
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)
        # Type
        ttk.Label(frame, text=f"{event_type} Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        self.type_entry = ttk.Entry(frame)
        self.type_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
        self.type_entry.insert(0, type_val)
        # Date
        ttk.Label(frame, text=f"{event_type} Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        self.date_var = tk.StringVar(value=date_val)
        self.date_entry = DateEntry(frame, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=6)
        # Person (examiner/operator)
        person_label = "Examiner:" if event_type == "Examination" else "Treatment By:"
        ttk.Label(frame, text=person_label).grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        self.person_entry = ttk.Entry(frame)
        self.person_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
        if person_val:
            self.person_entry.insert(0, person_val)
        # Height
        ttk.Label(frame, text="Height (cm):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=6)
        self.height_entry = ttk.Entry(frame)
        self.height_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=6)
        if height_val is not None:
            self.height_entry.insert(0, str(height_val))
        # Weight
        ttk.Label(frame, text="Weight (kg):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=6)
        self.weight_entry = ttk.Entry(frame)
        self.weight_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=6)
        if weight_val is not None:
            self.weight_entry.insert(0, str(weight_val))
        # Device
        ttk.Label(frame, text="Assistive Device:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=6)
        self.device_entry = ttk.Entry(frame)
        self.device_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=6)
        if device_val:
            self.device_entry.insert(0, device_val)
        # BMI display
        ttk.Label(frame, text="BMI:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=6)
        self.bmi_var = tk.StringVar()
        self.bmi_label = ttk.Label(frame, textvariable=self.bmi_var, font=("Segoe UI", 10, "bold"))
        self.bmi_label.grid(row=6, column=1, sticky=tk.W, padx=5, pady=6)
        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="NW", padx=5, pady=6)
        self.notes_entry = tk.Text(frame, height=6, width=40, font=("Segoe UI", 10), relief="solid", borderwidth=1)
        self.notes_entry.grid(row=7, column=1, sticky="NSEW", padx=5, pady=6)
        if notes_val:
            self.notes_entry.insert("1.0", notes_val)
        frame.rowconfigure(7, weight=1)
        # Bind BMI update
        self.height_entry.bind("<KeyRelease>", self.update_bmi)
        self.weight_entry.bind("<KeyRelease>", self.update_bmi)
        self.update_bmi()
        # Buttons
        btn_bar = ttk.Frame(frame)
        btn_bar.grid(row=8, column=0, columnspan=2, pady=(15, 0), sticky="E")
        save_btn = ttk.Button(btn_bar, text="Save", command=self.save)
        save_btn.pack(side=tk.RIGHT, padx=0)
        cancel_btn = ttk.Button(btn_bar, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.RIGHT, padx=(0, 5))

    def update_bmi(self, event: tk.Event | None = None) -> None:
        h = self.height_entry.get().strip()
        w = self.weight_entry.get().strip()
        try:
            height_cm = float(h) if h else None
            weight_kg = float(w) if w else None
            bmi = None
            if height_cm and weight_kg and height_cm > 0:
                bmi = weight_kg / ((height_cm / 100.0) ** 2)
            self.bmi_var.set(f"{bmi:.1f}" if bmi else "--")
        except Exception:
            self.bmi_var.set("--")

    def save(self) -> None:
        new_type = self.type_entry.get().strip()
        new_date = self.date_var.get().strip()
        new_person = self.person_entry.get().strip() or None
        new_notes = self.notes_entry.get("1.0", tk.END).strip()
        new_device = self.device_entry.get().strip() or None
        new_height = None
        new_weight = None
        h = self.height_entry.get().strip()
        w = self.weight_entry.get().strip()
        try:
            new_height = float(h) if h else None
        except Exception:
            messagebox.showwarning("Invalid height", "Height must be a number.")
            return
        try:
            new_weight = float(w) if w else None
        except Exception:
            messagebox.showwarning("Invalid weight", "Weight must be a number.")
            return
        if not (new_type and new_date):
            messagebox.showwarning("Missing data", f"{self.event_type} type and date are required.")
            return
        if self.event_type == "Examination":
            self.db.update_exam(
                self.event_id,
                new_type,
                new_date,
                new_notes,
                new_height,
                new_weight,
                new_device,
                new_person,
            )
        else:
            self.db.update_intervention(
                self.event_id,
                new_type,
                new_date,
                new_notes,
                new_height,
                new_weight,
                new_device,
                new_person,
            )
        self.refresh_callback()
        messagebox.showinfo("Updated", f"{self.event_type} updated.")
        self.destroy()









# class EditExamWindow(EditEventWindowBase):
#     def __init__(self, parent: tk.Widget, db: Database, exam_id: int, refresh_callback) -> None:
#         super().__init__(parent, db, exam_id, "Examination", refresh_callback)

# class EditInterventionWindow(EditEventWindowBase):
#     def __init__(self, parent: tk.Widget, db: Database, intervention_id: int, refresh_callback) -> None:
#         super().__init__(parent, db, intervention_id, "Intervention", refresh_callback)

class EditExamWindow(tk.Toplevel):
    def __init__(self, parent, db, exam_id, refresh_callback):
        super().__init__(parent)
        self.db = db
        self.event_id = exam_id
        self.refresh_callback = refresh_callback
        self.title("Edit Examination")
        self.geometry("500x600"); self.minsize(450, 500)
        self.grab_set(); self.transient(parent)

        # Fetch existing exam data including BMI
        data = db.get_exam(exam_id)
        if not data:
            messagebox.showerror("Error", "Examination not found.", parent=self)
            self.destroy(); return
        (_, _, type_val, date_val, notes_val,
         height_val, weight_val, device_val, bmi_val, person_val) = data

        frame = ttk.Frame(self, padding=20); frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # Examination Type
        ttk.Label(frame, text="Examination Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        self.type_entry = ttk.Entry(frame)
        self.type_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
        self.type_entry.insert(0, type_val or "")

        # Examination Date
        ttk.Label(frame, text="Examination Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        self.date_var = tk.StringVar(value=date_val or "")
        self.date_entry = DateEntry(frame, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=6)

        # Examiner
        ttk.Label(frame, text="Examiner:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        self.person_entry = ttk.Entry(frame)
        self.person_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
        if person_val: 
            self.person_entry.insert(0, person_val)

        # Height
        ttk.Label(frame, text="Height (cm):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=6)
        self.height_entry = ttk.Entry(frame)
        self.height_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=6)
        if height_val is not None: 
            self.height_entry.insert(0, str(height_val))

        # Weight
        ttk.Label(frame, text="Weight (kg):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=6)
        self.weight_entry = ttk.Entry(frame)
        self.weight_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=6)
        if weight_val is not None: 
            self.weight_entry.insert(0, str(weight_val))

        # Assistive Device
        ttk.Label(frame, text="Assistive Device:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=6)
        self.device_entry = ttk.Entry(frame)
        self.device_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=6)
        if device_val: 
            self.device_entry.insert(0, device_val)

        # BMI display
        ttk.Label(frame, text="BMI:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=6)
        self.bmi_var = tk.StringVar(value=f"{bmi_val:.1f}" if bmi_val else "--")
        self.bmi_label = ttk.Label(frame, textvariable=self.bmi_var, font=("Segoe UI", 10, "bold"))
        self.bmi_label.grid(row=6, column=1, sticky=tk.W, padx=5, pady=6)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="NW", padx=5, pady=6)
        self.notes_entry = tk.Text(frame, height=6, width=40, font=("Segoe UI", 10),
                                   relief="solid", borderwidth=1)
        self.notes_entry.grid(row=7, column=1, sticky="NSEW", padx=5, pady=6)
        if notes_val: 
            self.notes_entry.insert("1.0", notes_val)
        frame.rowconfigure(7, weight=1)

        # Bind BMI update on keypress
        self.height_entry.bind("<KeyRelease>", self.update_bmi)
        self.weight_entry.bind("<KeyRelease>", self.update_bmi)
        self.update_bmi()

        # Save / Cancel buttons
        btn_bar = ttk.Frame(frame)
        btn_bar.grid(row=8, column=0, columnspan=2, pady=(15, 0), sticky="E")
        ttk.Button(btn_bar, text="Save", command=self.save).pack(side=tk.RIGHT)
        ttk.Button(btn_bar, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(0,5))

    def update_bmi(self, event=None):
        try:
            h = self.height_entry.get().strip()
            w = self.weight_entry.get().strip()
            height_cm = float(h) if h else None
            weight_kg = float(w) if w else None
            bmi = (weight_kg / ((height_cm/100.0)**2)) if height_cm and weight_kg else None
            self.bmi_var.set(f"{bmi:.1f}" if bmi else "--")
        except:
            self.bmi_var.set("--")

    def save(self):
        new_type = self.type_entry.get().strip()
        new_date = self.date_var.get().strip()
        new_person = self.person_entry.get().strip() or None
        new_notes = self.notes_entry.get("1.0", tk.END).strip()
        new_device = self.device_entry.get().strip() or None
        try:
            new_height = float(self.height_entry.get().strip()) if self.height_entry.get().strip() else None
        except:
            messagebox.showwarning("Invalid height", "Height must be a number.", parent=self)
            return
        try:
            new_weight = float(self.weight_entry.get().strip()) if self.weight_entry.get().strip() else None
        except:
            messagebox.showwarning("Invalid weight", "Weight must be a number.", parent=self)
            return
        if not (new_type and new_date):
            messagebox.showwarning("Missing data", "Examination type and date are required.", parent=self)
            return
        self.db.update_exam(self.event_id, new_type, new_date, new_notes,
                            new_height, new_weight, new_device, new_person)
        self.refresh_callback()
        messagebox.showinfo("Updated", "Examination updated.", parent=self)
        self.destroy()


class EditInterventionWindow(tk.Toplevel):
    def __init__(self, parent, db, intervention_id, refresh_callback):
        super().__init__(parent)
        self.db = db
        self.event_id = intervention_id
        self.refresh_callback = refresh_callback
        self.title("Edit Intervention")
        self.geometry("500x600"); self.minsize(450, 500)
        self.grab_set(); self.transient(parent)

        # Fetch existing intervention data including BMI
        data = db.get_intervention(intervention_id)
        if not data:
            messagebox.showerror("Error", "Intervention not found.", parent=self)
            self.destroy(); return
        (_, _, type_val, date_val, notes_val,
         height_val, weight_val, device_val, bmi_val, person_val) = data

        frame = ttk.Frame(self, padding=20); frame.pack(fill=tk.BOTH, expand=True)
        frame.columnconfigure(1, weight=1)

        # Intervention Type
        ttk.Label(frame, text="Intervention Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=6)
        self.type_entry = ttk.Entry(frame)
        self.type_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=6)
        self.type_entry.insert(0, type_val or "")

        # Intervention Date
        ttk.Label(frame, text="Intervention Date:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=6)
        self.date_var = tk.StringVar(value=date_val or "")
        self.date_entry = DateEntry(frame, textvariable=self.date_var)
        self.date_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=6)

        # Treatment By
        ttk.Label(frame, text="Treatment By:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=6)
        self.person_entry = ttk.Entry(frame)
        self.person_entry.grid(row=2, column=1, sticky=tk.EW, padx=5, pady=6)
        if person_val:
            self.person_entry.insert(0, person_val)

        # Height
        ttk.Label(frame, text="Height (cm):").grid(row=3, column=0, sticky=tk.W, padx=5, pady=6)
        self.height_entry = ttk.Entry(frame)
        self.height_entry.grid(row=3, column=1, sticky=tk.EW, padx=5, pady=6)
        if height_val is not None:
            self.height_entry.insert(0, str(height_val))

        # Weight
        ttk.Label(frame, text="Weight (kg):").grid(row=4, column=0, sticky=tk.W, padx=5, pady=6)
        self.weight_entry = ttk.Entry(frame)
        self.weight_entry.grid(row=4, column=1, sticky=tk.EW, padx=5, pady=6)
        if weight_val is not None:
            self.weight_entry.insert(0, str(weight_val))

        # Assistive Device
        ttk.Label(frame, text="Assistive Device:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=6)
        self.device_entry = ttk.Entry(frame)
        self.device_entry.grid(row=5, column=1, sticky=tk.EW, padx=5, pady=6)
        if device_val:
            self.device_entry.insert(0, device_val)

        # BMI display
        ttk.Label(frame, text="BMI:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=6)
        self.bmi_var = tk.StringVar(value=f"{bmi_val:.1f}" if bmi_val else "--")
        self.bmi_label = ttk.Label(frame, textvariable=self.bmi_var, font=("Segoe UI", 10, "bold"))
        self.bmi_label.grid(row=6, column=1, sticky=tk.W, padx=5, pady=6)

        # Notes
        ttk.Label(frame, text="Notes:").grid(row=7, column=0, sticky="NW", padx=5, pady=6)
        self.notes_entry = tk.Text(frame, height=6, width=40, font=("Segoe UI", 10),
                                   relief="solid", borderwidth=1)
        self.notes_entry.grid(row=7, column=1, sticky="NSEW", padx=5, pady=6)
        if notes_val: 
            self.notes_entry.insert("1.0", notes_val)
        frame.rowconfigure(7, weight=1)

        # Bind BMI update on keypress
        self.height_entry.bind("<KeyRelease>", self.update_bmi)
        self.weight_entry.bind("<KeyRelease>", self.update_bmi)
        self.update_bmi()

        # Save / Cancel buttons
        btn_bar = ttk.Frame(frame)
        btn_bar.grid(row=8, column=0, columnspan=2, pady=(15, 0), sticky="E")
        ttk.Button(btn_bar, text="Save", command=self.save).pack(side=tk.RIGHT)
        ttk.Button(btn_bar, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=(0,5))

    def update_bmi(self, event=None):
        try:
            h = self.height_entry.get().strip()
            w = self.weight_entry.get().strip()
            height_cm = float(h) if h else None
            weight_kg = float(w) if w else None
            bmi = (weight_kg / ((height_cm/100.0)**2)) if height_cm and weight_kg else None
            self.bmi_var.set(f"{bmi:.1f}" if bmi else "--")
        except:
            self.bmi_var.set("--")

    def save(self):
        new_type = self.type_entry.get().strip()
        new_date = self.date_var.get().strip()
        new_person = self.person_entry.get().strip() or None
        new_notes = self.notes_entry.get("1.0", tk.END).strip()
        new_device = self.device_entry.get().strip() or None
        try:
            new_height = float(self.height_entry.get().strip()) if self.height_entry.get().strip() else None
        except:
            messagebox.showwarning("Invalid height", "Height must be a number.", parent=self)
            return
        try:
            new_weight = float(self.weight_entry.get().strip()) if self.weight_entry.get().strip() else None
        except:
            messagebox.showwarning("Invalid weight", "Weight must be a number.", parent=self)
            return
        if not (new_type and new_date):
            messagebox.showwarning("Missing data", "Intervention type and date are required.", parent=self)
            return
        self.db.update_intervention(self.event_id, new_type, new_date, new_notes,
                                    new_height, new_weight, new_device, new_person)
        self.refresh_callback()
        messagebox.showinfo("Updated", "Intervention updated.", parent=self)
        self.destroy()













def main() -> None:
    # --- Database Path Setup (Use AppData) ---
    db = None
    try:
        app_name = "GaitDocumentationSystem"
        if os.name == 'nt': app_data_path = Path(os.environ['LOCALAPPDATA']) / app_name
        elif sys.platform == 'darwin': app_data_path = Path.home()/'Library'/'Application Support'/app_name
        else: app_data_path = Path.home()/'.local'/'share'/app_name
        app_data_path.mkdir(parents=True, exist_ok=True)
        db_path = app_data_path / 'health_records.db'

        db = Database(str(db_path))
        root = tk.Tk()
        app = PatientApp(root, db)
        root.mainloop()
    except Exception as e:
         print(f"CRITICAL ERROR: {e}")
         try: root_err=tk.Tk(); root_err.withdraw(); messagebox.showerror("Critical Error", f"Error:\n{e}"); root_err.destroy()
         except: pass
    finally:
        if db: db.close()

if __name__ == "__main__":
    main()

