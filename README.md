# Gait Documentation App (Version 1.1)
## 1) Overview
**Gait Documentation App** is free, open-source software for clinical documentation (GNU GPLv3). It provides an intuitive interface to record **patient information**, **examinations**, **interventions**, and **associated files**. The app is offered in two formats: **an installable version** and **a portable (no‑install) version**.

**Safe Download link**:

Portable:
https://heibox.uni-heidelberg.de/f/94649ebd1b4b4ee39a02/ 

Installable:
https://heibox.uni-heidelberg.de/f/bb2d7a8aa01448d1835d/ 


## 2) Key Features
- **Patient management:** add, search, edit, and delete patients with demographic data.
- **Examination logging:** capture exam dates, height, weight, BMI (auto‑calculated), and notes.
- **Intervention logging:** record treatment/intervention details with dates and notes.
- **Attachments:** link reports, images, videos to each exam or intervention; stored safely in a local attachments folder.
- **Timeline view:** see examinations and interventions chronologically with the patient’s age at each event.
- **Flexible deployment:** choose installer or portable version based on your IT policy.
- **Data export (if enabled in your build):** export data for downstream analysis and reporting.
- **Open source:** GPLv3 license; modify and share under the same terms.

## 3) System Requirements
- Windows 10 or later.
- If applicable to your build, the required runtime (e.g., .NET Desktop Runtime).

## 4) Installation
**A) Installable Version**  
- Download: `Install_File_GaitDocuApp.exe` (or the corresponding ZIP).  
- Run the EXE and follow the on‑screen setup wizard.  
- Launch the app from the Start Menu or desktop shortcut.

**B) Portable Version (No Installation)**  
- Download: `Portable_GaitDocumentationApp.exe` (or the corresponding ZIP).  
- If ZIP, extract to a folder you control (or a USB drive).  
- Run the executable directly from that folder.

## 5) Quick Start
- Launch the app.  
- Click **“Add New Patient”** to create your first patient profile.  
- Double‑click a patient to open details and start recording examinations, interventions, and attachments.

## 6) Help Guide (Using the Application)
**Adding a new patient**  
- Click the **“Add New Patient”** button at the bottom of the main window to open a form where you can enter the patient's demographic details. Fields marked with an asterisk are required. Optional information such as address and contact details can also be recorded.

**Searching for patients**  
- Use the drop‑down box at the top of the patient list to choose a search field (last name, diagnosis, patient ID, or zip code). Type into the adjacent search box to filter the patient list dynamically.  
- You can also restrict the birth date range using the date pickers.

**Editing or deleting a patient**  
- Select a patient in the list and click **“Edit Selected Patient”** to open a form where you can modify their details. The **Save** and **Cancel** buttons appear at the bottom of the form.  
- Click **“Delete Selected Patient”** to remove a patient and all associated examinations, interventions, and attachments. You will be asked to confirm before the record is permanently deleted.

**Recording examinations and interventions**  
- Double‑click a patient in the list to open their detail window. This window contains tabs for examinations, interventions, and a combined timeline.  
- In the examinations tab, fill in the form at the top and click **“Add Exam”** to record a new entry. The date pickers allow you to specify the exam date; height and weight (if provided) will be used to calculate BMI automatically.  
- The interventions tab works similarly, with a separate form and an **“Add Intervention”** button.

**Working with attachments**  
- Each exam or intervention can have files attached (for example, reports, images, or videos). Double‑click an entry in the list to open the attachments manager.  
- Use the **“Add Attachment...”** button to browse for a file. A copy of the selected file will be stored in the application’s local attachments folder so that it remains accessible even if the original file is moved or deleted.  
- Double‑click a file in the attachments list to open it with the default application on your system.

**Timeline view**  
- The timeline tab displays both examinations and interventions chronologically, along with the patient's age at each event. This view helps you see the sequence of care over time.

## 7) Data Storage and Backup
- The application uses a local SQLite database named: `health_records.db`  
- Default location (Windows):  
  `%LOCALAPPDATA%\GaitDocumentationSystem\health_records.db`  
  (For example: `C:\Users\<YourUser>\AppData\Local\GaitDocumentationSystem\health_records.db`)  
- Attachments are saved in a subfolder named **“attachments”** next to the database.  
- **Backup tip:** To back up your data, copy both the database file and the entire **“attachments”** folder while the app is closed.

## 8) Privacy and Security
- Patient data is stored locally on your computer. Ensure your device, user account, and backups are protected according to your institution’s data‑protection policies. Avoid storing sensitive data on shared or public machines. Consider full‑disk encryption where appropriate.

## 9) License
- This software is released under the **GNU General Public License v3.0 (GPLv3)**.  
- You are free to use, modify, and redistribute the software under the GPLv3.  
- This program is provided **“AS IS,”** without warranty of any kind.

## 10) Acknowledgments and Donations
- I gratefully acknowledge the support of the **Gesellschaft der Freunde der Universität Heidelberg e.V. (Society of Friends of Heidelberg University)**.  
- This app is free to use. If it helps your work, please consider a donation to support students and early‑career researchers:  
  **Recipient:** Gesellschaft der Freunde der Universität Heidelberg e.V.  
  **Bank:** Deutsche Bank Heidelberg  
  **IBAN:** `DE22 6727 0003 0049 4005 00`  
  **BIC (SWIFT):** `DEUTDESM672`  
  **Reference (optional):** *Davoudi App Donation*

---

**Thank you for using the Gait Documentation App.**
