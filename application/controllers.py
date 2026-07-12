# controllers.py - all the routes (pages) of Alpitude live here.
# Every protected route follows the same 3 steps:
#   1) check the role saved in session   2) talk to the database   3) show a template

from flask import render_template, request, redirect, session, flash
from flask import current_app as app
from application.models import db, User, Trek, Booking
from datetime import date


# ---------------- landing + auth ----------------

# landing page with Login / Sign Up buttons
@app.route("/")
def index():
    return render_template("index.html")


# login: one page for all three roles
@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        current_user = User.query.filter_by(username=username).first()
        # user not found, or password does not match
        if current_user is None or current_user.password != password:
            flash("Invalid username or password.", "danger")
            return redirect("/login")
        # blocked accounts cannot enter
        if current_user.is_blacklisted:
            flash("Your account has been blacklisted by the admin.", "danger")
            return redirect("/login")
        # staff can login only after admin approves them
        if current_user.role == 'staff' and current_user.is_approved == False:
            flash("Your staff account is still waiting for admin approval.", "warning")
            return redirect("/login")
        # login successful: remember who this is inside the session cookie
        session["user_id"] = current_user.id
        session["username"] = current_user.username
        session["role"] = current_user.role
        # send each role to its own dashboard
        if current_user.role == 'admin':
            return redirect("/admin")
        elif current_user.role == 'staff':
            return redirect("/staff")
        else:
            return redirect("/user")
    return render_template("login.html")


# signup: trekkers and trek staff register here (admin never registers)
@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        contact_number = request.form.get("contact_number")
        role = request.form.get("role")   # 'user' (trekker) or 'staff'
        # usernames and emails must be unique
        if User.query.filter_by(username=username).first():
            flash("This username is already taken.", "danger")
            return redirect("/signup")
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
            return redirect("/signup")
        # staff start unapproved, trekkers are approved straight away
        if role == 'staff':
            new_user = User(username=username, email=email, password=password,
                            contact_number=contact_number, role='staff', is_approved=False)
            flash("Account created. You can login once the admin approves you.", "warning")
        else:
            new_user = User(username=username, email=email, password=password,
                            contact_number=contact_number, role='user', is_approved=True)
            flash("Account created. Please login.", "success")
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("signup.html")


# logout: forget the session and go back to the landing page
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ---------------- admin: dashboard ----------------

# admin dashboard: counts + recent bookings
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != 'admin':
        return redirect("/login")
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff', is_approved=False).count()
    # newest 5 bookings (highest id = newest)
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    return render_template("admin_dashboard.html", total_treks=total_treks,
                           total_users=total_users, total_staff=total_staff,
                           total_bookings=total_bookings, pending_staff=pending_staff,
                           recent_bookings=recent_bookings)


# ---------------- admin: manage treks ----------------

# admin: table of all treks
@app.route("/admin/treks")
def admin_treks():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_treks = Trek.query.all()
    return render_template("admin_treks.html", all_treks=all_treks)


# admin: create a new trek
@app.route("/admin/trek/add", methods=['GET', 'POST'])
def add_trek():
    if session.get("role") != 'admin':
        return redirect("/login")
    # approved staff shown in the "assign staff" dropdown
    staff_list = User.query.filter_by(role='staff', is_approved=True).all()
    if request.method == 'POST':
        duration_days = request.form.get("duration_days")
        available_slots = request.form.get("available_slots")
        # isdigit() = the text contains only numbers
        if not duration_days.isdigit() or not available_slots.isdigit():
            flash("Duration and slots must be numbers.", "danger")
            return redirect("/admin/trek/add")
        staff_id = request.form.get("staff_id")
        if staff_id == "":
            staff_id = None      # trek can be created without a staff assigned
        new_trek = Trek(name=request.form.get("name"),
                        location=request.form.get("location"),
                        difficulty=request.form.get("difficulty"),
                        duration_days=int(duration_days),
                        available_slots=int(available_slots),
                        status=request.form.get("status"),
                        start_date=request.form.get("start_date"),
                        end_date=request.form.get("end_date"),
                        description=request.form.get("description"),
                        staff_id=staff_id)
        db.session.add(new_trek)
        db.session.commit()
        flash("Trek created.", "success")
        return redirect("/admin/treks")
    # trek=None tells the form template this is "add" mode, not "edit" mode
    return render_template("trek_form.html", trek=None, staff_list=staff_list)


# admin: edit an existing trek (same form template as add)
@app.route("/admin/trek/edit/<int:trek_id>", methods=['GET', 'POST'])
def edit_trek(trek_id):
    if session.get("role") != 'admin':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect("/admin/treks")
    staff_list = User.query.filter_by(role='staff', is_approved=True).all()
    if request.method == 'POST':
        duration_days = request.form.get("duration_days")
        available_slots = request.form.get("available_slots")
        if not duration_days.isdigit() or not available_slots.isdigit():
            flash("Duration and slots must be numbers.", "danger")
            return redirect("/admin/trek/edit/" + str(trek_id))
        trek.name = request.form.get("name")
        trek.location = request.form.get("location")
        trek.difficulty = request.form.get("difficulty")
        trek.duration_days = int(duration_days)
        trek.available_slots = int(available_slots)
        trek.status = request.form.get("status")
        trek.start_date = request.form.get("start_date")
        trek.end_date = request.form.get("end_date")
        trek.description = request.form.get("description")
        if request.form.get("staff_id") == "":
            trek.staff_id = None
        else:
            trek.staff_id = request.form.get("staff_id")
        db.session.commit()
        flash("Trek updated.", "success")
        return redirect("/admin/treks")
    return render_template("trek_form.html", trek=trek, staff_list=staff_list)


# admin: delete a trek (delete its bookings first, then the trek)
@app.route("/admin/trek/delete/<int:trek_id>", methods=['POST'])
def delete_trek(trek_id):
    if session.get("role") != 'admin':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek:
        for booking in trek.bookings:
            db.session.delete(booking)
        db.session.delete(trek)
        db.session.commit()
        flash("Trek deleted.", "success")
    return redirect("/admin/treks")


# ---------------- admin: manage staff and users ----------------

# admin: list all staff with approve / blacklist buttons
@app.route("/admin/staff")
def admin_staff():
    if session.get("role") != 'admin':
        return redirect("/login")
    staff_members = User.query.filter_by(role='staff').all()
    return render_template("admin_staff.html", staff_members=staff_members)


# admin: approve a staff registration request
@app.route("/admin/staff/approve/<int:staff_id>", methods=['POST'])
def approve_staff(staff_id):
    if session.get("role") != 'admin':
        return redirect("/login")
    staff_member = User.query.get(staff_id)
    if staff_member and staff_member.role == 'staff':
        staff_member.is_approved = True
        db.session.commit()
        flash("Staff member approved. They can login now.", "success")
    return redirect("/admin/staff")


# admin: blacklist or un-blacklist a staff member
@app.route("/admin/staff/toggle/<int:staff_id>", methods=['POST'])
def toggle_staff(staff_id):
    if session.get("role") != 'admin':
        return redirect("/login")
    staff_member = User.query.get(staff_id)
    if staff_member and staff_member.role == 'staff':
        if staff_member.is_blacklisted:
            staff_member.is_blacklisted = False
        else:
            staff_member.is_blacklisted = True
        db.session.commit()
        flash("Staff status updated.", "success")
    return redirect("/admin/staff")


# admin: list all trekkers with blacklist buttons
@app.route("/admin/users")
def admin_users():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_users = User.query.filter_by(role='user').all()
    return render_template("admin_users.html", all_users=all_users)


# admin: blacklist or un-blacklist a trekker
@app.route("/admin/users/toggle/<int:user_id>", methods=['POST'])
def toggle_user(user_id):
    if session.get("role") != 'admin':
        return redirect("/login")
    person = User.query.get(user_id)
    if person and person.role == 'user':
        if person.is_blacklisted:
            person.is_blacklisted = False
        else:
            person.is_blacklisted = True
        db.session.commit()
        flash("User status updated.", "success")
    return redirect("/admin/users")


# ---------------- admin: bookings + search ----------------

# admin: every booking in the system (full history)
@app.route("/admin/bookings")
def admin_bookings():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin_bookings.html", all_bookings=all_bookings)


# admin: search treks / users / staff by name (GET form, values arrive in the URL)
@app.route("/admin/search")
def admin_search():
    if session.get("role") != 'admin':
        return redirect("/login")
    query = request.args.get("query", "")
    category = request.args.get("category", "treks")
    results = []
    if query != "":
        if category == "treks":
            # contains() works like SQL LIKE: matches anywhere in the text
            results = Trek.query.filter(db.or_(Trek.name.contains(query),
                                               Trek.location.contains(query))).all()
        elif category == "staff":
            results = User.query.filter_by(role='staff').filter(
                db.or_(User.username.contains(query), User.email.contains(query))).all()
        else:
            results = User.query.filter_by(role='user').filter(
                db.or_(User.username.contains(query), User.email.contains(query))).all()
    return render_template("admin_search.html", results=results, query=query, category=category)


# ---------------- staff module ----------------

# staff dashboard: only the treks assigned to me
@app.route("/staff")
def staff_dashboard():
    if session.get("role") != 'staff':
        return redirect("/login")
    my_treks = Trek.query.filter_by(staff_id=session.get("user_id")).all()
    total_participants = 0
    open_treks = 0
    for trek in my_treks:
        for booking in trek.bookings:
            if booking.status == 'Booked':
                total_participants = total_participants + 1
        if trek.status == 'Open':
            open_treks = open_treks + 1
    return render_template("staff_dashboard.html", my_treks=my_treks,
                           total_participants=total_participants, open_treks=open_treks)


# staff: manage one trek (only if it is assigned to me)
@app.route("/staff/trek/<int:trek_id>")
def staff_trek(trek_id):
    if session.get("role") != 'staff':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    # ownership check: staff can only open their own treks
    if trek is None or trek.staff_id != session.get("user_id"):
        flash("You can only manage treks assigned to you.", "danger")
        return redirect("/staff")
    participants = []
    for booking in trek.bookings:
        if booking.status == 'Booked':
            participants.append(booking)
    return render_template("staff_trek.html", trek=trek, participants=participants)


# staff: update available slots and open/close the trek
@app.route("/staff/trek/<int:trek_id>/update", methods=['POST'])
def update_trek(trek_id):
    if session.get("role") != 'staff':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None or trek.staff_id != session.get("user_id"):
        flash("You can only manage treks assigned to you.", "danger")
        return redirect("/staff")
    available_slots = request.form.get("available_slots")
    if not available_slots.isdigit():
        flash("Slots must be a number.", "danger")
        return redirect("/staff/trek/" + str(trek_id))
    trek.available_slots = int(available_slots)
    trek.status = request.form.get("status")
    db.session.commit()
    flash("Trek updated.", "success")
    return redirect("/staff/trek/" + str(trek_id))


# staff: mark the trek completed (and all its active bookings too)
@app.route("/staff/trek/<int:trek_id>/complete", methods=['POST'])
def complete_trek(trek_id):
    if session.get("role") != 'staff':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None or trek.staff_id != session.get("user_id"):
        flash("You can only manage treks assigned to you.", "danger")
        return redirect("/staff")
    trek.status = 'Completed'
    for booking in trek.bookings:
        if booking.status == 'Booked':
            booking.status = 'Completed'
    db.session.commit()
    flash("Trek marked as completed.", "success")
    return redirect("/staff/trek/" + str(trek_id))


# profile page shared by staff and trekkers: update contact or password
@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if session.get("role") != 'staff' and session.get("role") != 'user':
        return redirect("/login")
    current_user = User.query.get(session.get("user_id"))
    if request.method == 'POST':
        current_user.contact_number = request.form.get("contact_number")
        new_password = request.form.get("new_password")
        if new_password != "":          # empty box = keep the old password
            current_user.password = new_password
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect("/profile")
    return render_template("profile.html", current_user=current_user)


# ---------------- user (trekker) module ----------------

# user dashboard: open treks (with a search box) + my active bookings
@app.route("/user")
def user_dashboard():
    if session.get("role") != 'user':
        return redirect("/login")
    search = request.args.get("search", "")
    if search != "":
        open_treks = Trek.query.filter(Trek.status == 'Open').filter(
            db.or_(Trek.name.contains(search), Trek.location.contains(search))).all()
    else:
        open_treks = Trek.query.filter_by(status='Open').all()
    my_bookings = Booking.query.filter_by(user_id=session.get("user_id"), status='Booked').all()
    return render_template("user_dashboard.html", open_treks=open_treks,
                           my_bookings=my_bookings, search=search)


# full details of one trek, with the Book Now button
@app.route("/trek/<int:trek_id>")
def trek_detail(trek_id):
    if session.get("role") != 'user':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect("/user")
    already_booked = Booking.query.filter_by(user_id=session.get("user_id"),
                                             trek_id=trek.id, status='Booked').first()
    return render_template("trek_detail.html", trek=trek, already_booked=already_booked)


# book a trek: the three booking rules live here
@app.route("/trek/<int:trek_id>/book", methods=['POST'])
def book_trek(trek_id):
    if session.get("role") != 'user':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect("/user")
    # rule 1: trek must be Open and have free slots
    if trek.status != 'Open' or trek.available_slots < 1:
        flash("This trek is not open for booking right now.", "danger")
        return redirect("/trek/" + str(trek_id))
    # rule 2: the same user cannot book the same trek twice
    already_booked = Booking.query.filter_by(user_id=session.get("user_id"),
                                             trek_id=trek.id, status='Booked').first()
    if already_booked:
        flash("You have already booked this trek.", "warning")
        return redirect("/trek/" + str(trek_id))
    # rule 3: save the booking and take one slot
    new_booking = Booking(user_id=session.get("user_id"), trek_id=trek.id,
                          booking_date=date.today().strftime("%Y-%m-%d"), status='Booked')
    trek.available_slots = trek.available_slots - 1
    db.session.add(new_booking)
    db.session.commit()
    flash("Trek booked successfully!", "success")
    return redirect("/user/bookings")


# my active bookings, each with a cancel button
@app.route("/user/bookings")
def user_bookings():
    if session.get("role") != 'user':
        return redirect("/login")
    my_bookings = Booking.query.filter_by(user_id=session.get("user_id"), status='Booked').all()
    return render_template("user_bookings.html", my_bookings=my_bookings)


# cancel a booking and give the slot back to the trek
@app.route("/user/bookings/cancel/<int:booking_id>", methods=['POST'])
def cancel_booking(booking_id):
    if session.get("role") != 'user':
        return redirect("/login")
    booking = Booking.query.get(booking_id)
    # users can only cancel their own bookings
    if booking is None or booking.user_id != session.get("user_id"):
        flash("Booking not found.", "danger")
        return redirect("/user/bookings")
    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots = booking.trek.available_slots + 1
        db.session.commit()
        flash("Booking cancelled.", "success")
    return redirect("/user/bookings")


# my complete trekking history (Booked, Cancelled and Completed)
@app.route("/user/history")
def user_history():
    if session.get("role") != 'user':
        return redirect("/login")
    my_history = Booking.query.filter_by(user_id=session.get("user_id")).order_by(Booking.id.desc()).all()
    return render_template("user_history.html", my_history=my_history)
