# Student Result Management System

A complete, production-quality **Student Result Management System** built with
Flask, SQLAlchemy, SQLite, vanilla JavaScript and a modern glassmorphism UI.

## Features

- Secure admin authentication (hashed passwords, session-based login)
- Dashboard with live stats, charts (Chart.js) and recent activity
- Student management: add / edit / delete / search / filter / photo upload
- Subject management: add / edit / delete, assigned by department & semester
- Marks management: internal, mid-term, and final exam marks with **automatic**
  total, percentage, grade and GPA calculation (live preview via AJAX)
- Automatic grading scale (O / A+ / A / B+ / B / C / F) and pass/fail status
- Results module with class ranking and printable, professional report cards
- Analytics: subject-wise averages, grade distribution, top students
- CSV export for students and results; full database backup & restore
- Dark / light mode toggle, responsive sidebar layout, toast notifications,
  animated counters, client-side + server-side search, and form validation

## Tech Stack

| Layer      | Technology                          |
|------------|--------------------------------------|
| Backend    | Python 3, Flask                      |
| Database   | SQLite via SQLAlchemy (Flask-SQLAlchemy) |
| Frontend   | HTML5, vanilla CSS3, vanilla JavaScript |
| Charts     | Chart.js (via CDN)                   |
| Icons      | Font Awesome (via CDN)                |
| Auth       | Flask sessions + Werkzeug password hashing |

No React/Vue/Angular, no Bootstrap/Tailwind, no Django, no Firebase, and no
paid services are used anywhere in this project.

## Project Structure

```
Student-Result-Management-System/
├── app.py                 # Flask application & all routes
├── models.py               # SQLAlchemy models (User, Student, Subject, Marks, Result)
├── config.py                # App configuration
├── requirements.txt
├── README.md
├── database.db              # created automatically on first run
│
├── static/
│   ├── css/style.css        # Glassmorphism UI styling
│   ├── js/script.js         # Theme toggle, validation, search, toasts, counters
│   └── images/               # Default avatar + uploaded student photos
│
└── templates/
    ├── index.html, login.html
    ├── dashboard.html
    ├── students.html, add_student.html, edit_student.html
    ├── subjects.html
    ├── marks.html, add_marks.html
    ├── results.html, report_card.html
    ├── profile.html, settings.html
    └── 404.html
```

## Installation & Setup

1. **Clone / copy the project folder**, then move into it:

   ```bash
   cd Student-Result-Management-System
   ```

2. **(Recommended) Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python app.py
   ```

   On first run, the app automatically creates `database.db` with all
   required tables and a default admin account:

   ```
   Username: admin
   Password: admin123
   ```

   **Change this password immediately** from the Settings page after your
   first login.

5. Open your browser at **http://127.0.0.1:5000**

## Typical Workflow

1. Log in with the default admin account.
2. Go to **Subjects** and add the subjects for each department/semester.
3. Go to **Students** and add your students (photo upload optional).
4. Go to **Marks → Add Marks**, pick a student + subject, and enter
   Internal / Mid / Final scores — total, %, grade and GPA are calculated
   live as you type, and saved automatically on submit.
5. Visit **Results** to see the ranked class list, or open a student's
   **Report Card** to view/print a full, signable statement of marks.
6. Use **Settings** to back up or restore the database, change your
   password, or export students/results to CSV.

## Grading Scale

| Percentage | Grade | GPA  |
|------------|-------|------|
| 90–100     | O     | 10.0 |
| 80–89      | A+    | 9.0  |
| 70–79      | A     | 8.0  |
| 60–69      | B+    | 7.0  |
| 50–59      | B     | 6.0  |
| 40–49      | C     | 5.0  |
| Below 40   | F     | 0.0  |

## Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash`
  (never stored in plain text).
- All routes that modify data are protected by a `@login_required`
  decorator and only accept `POST` for mutating actions.
- SQLAlchemy's ORM (parameterized queries) protects against SQL injection.
- Uploaded files are restricted by extension and size (max 5 MB) and
  saved with `secure_filename`.
- Session cookies are set `HttpOnly` and `SameSite=Lax`.
- For a real deployment, set `SECRET_KEY` via an environment variable,
  run behind HTTPS, and add a proper CSRF token library
  (e.g. `Flask-WTF`) to all forms.

## Notes for Evaluators / College Mini-Project Use

- This project intentionally uses **only** Flask + SQLite + vanilla
  frontend technologies, per the assignment brief — no frontend
  frameworks or paid services.
- The database is a single `database.db` SQLite file; you can inspect it
  with any SQLite browser, or use **Settings → Download Backup** to grab
  a copy at any time.
- To reset the app to a clean state, simply delete `database.db` and
  restart — it will be recreated automatically with a fresh admin user.
