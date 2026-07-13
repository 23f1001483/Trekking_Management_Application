# TrekCrew - Trekking Management Application

A role-based web platform designed to digitise and streamline outdoor adventure coordination. This application replaces fragmented spreadsheet tracking and manual communication with automated booking engines, real-time logistics management, and role-specific dashboards.

## Roles

- **Admin** (pre-created, no registration) - creates/edits/deletes treks, approves staff
  registrations, assigns staff to treks, blacklists users/staff, views every booking,
  and searches treks, users and staff.
- **Trek Staff** (registers, can login only after admin approval) - sees only their
  assigned treks, updates slots and status, views participants, marks treks completed.
- **Trekker / User** (registers) - explores open treks, books a slot, cancels bookings,
  views trekking history, edits profile.

## Tech used

- Flask (routes + session based login)
- Flask-SQLAlchemy with SQLite (3 tables: User, Trek, Booking)
- Jinja2 templates and CSS styling.

## How to run

```
pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000 in your browser.
The database and the default admin account are created automatically on the first run.

## Default admin login

- Username: `admin`
- Password: `1234`
