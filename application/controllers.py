from flask import render_template, request, redirect, session, flash
from flask import current_app as app
from application.models import db, User, Trek, Booking
from datetime import date


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        current_user = User.query.filter_by(username=username).first()
        if current_user is None or current_user.password != password:
            flash("Invalid username or password.", "danger")
            return redirect("/login")
        elif current_user.is_blacklisted:
            flash("Your account has been blacklisted by the admin.", "danger")
            return redirect("/login")
        elif current_user.role == 'staff' and current_user.is_approved == False:
            flash("Your staff account is still waiting for admin approval.", "warning")
            return redirect("/login")
        session["user_id"] = current_user.id
        session["username"] = current_user.username
        session["role"] = current_user.role
        if current_user.role == 'admin':
            return redirect("/admin")
        elif current_user.role == 'staff':
            return redirect("/staff")
        else:
            return redirect("/user")
    return render_template("login.html")


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        contact_number = request.form.get("contact_number", "").strip()
        role = request.form.get("role")

        if username == "" or email == "" or password == "":
            flash("Please fill in all the fields.", "danger")
            return redirect("/signup")
        if not (3 <= len(username) <= 16):
            flash("Username must be between 3 and 16 characters long.", "danger")
            return redirect("/signup")
        if not (8 < len(password) < 16):
            flash("Password must be more than 8 and less than 16 characters long.", "danger")
            return redirect("/signup")
        if username.lower() == password.lower():
            flash("Your password cannot be the same as your username.", "danger")
            return redirect("/signup")
        if User.query.filter_by(username=username).first():
            flash("This username is already taken.", "danger")
            return redirect("/signup")
        if User.query.filter_by(email=email).first():
            flash("This email is already registered.", "danger")
            return redirect("/signup")
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/admin")
def admin_dashboard():
    if session.get("role") != 'admin':
        return redirect("/login")
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff', is_approved=False).count()
    recent_bookings = Booking.query.order_by(Booking.id.desc()).limit(5).all()
    return render_template("admin_dashboard.html", total_treks=total_treks,
                           total_users=total_users, total_staff=total_staff,
                           total_bookings=total_bookings, pending_staff=pending_staff,
                           recent_bookings=recent_bookings)


@app.route("/admin/treks")
def admin_treks():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_treks = Trek.query.all()
    return render_template("admin_treks.html", all_treks=all_treks)


@app.route("/admin/trek/add", methods=['GET', 'POST'])
def add_trek():
    if session.get("role") != 'admin':
        return redirect("/login")
    staff_list = User.query.filter_by(role='staff', is_approved=True).all()
    if request.method == 'POST':
        duration_days = request.form.get("duration_days")
        available_slots = request.form.get("available_slots")
        if not duration_days or not available_slots or not duration_days.isdigit() or not available_slots.isdigit():
            flash("Duration and slots must be numbers.", "danger")
            return redirect("/admin/trek/add")
        staff_id = request.form.get("staff_id")
        if staff_id == "":
            staff_id = None
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
    return render_template("trek_form.html", trek=None, staff_list=staff_list)


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
        if not duration_days or not available_slots or not duration_days.isdigit() or not available_slots.isdigit():
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


@app.route("/admin/staff")
def admin_staff():
    if session.get("role") != 'admin':
        return redirect("/login")
    staff_members = User.query.filter_by(role='staff').all()
    return render_template("admin_staff.html", staff_members=staff_members)


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


@app.route("/admin/users")
def admin_users():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_users = User.query.filter_by(role='user').all()
    return render_template("admin_users.html", all_users=all_users)


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


@app.route("/admin/bookings")
def admin_bookings():
    if session.get("role") != 'admin':
        return redirect("/login")
    all_bookings = Booking.query.order_by(Booking.id.desc()).all()
    return render_template("admin_bookings.html", all_bookings=all_bookings)


@app.route("/admin/search")
def admin_search():
    if session.get("role") != 'admin':
        return redirect("/login")
    query = request.args.get("query", "")
    category = request.args.get("category", "treks")
    # if the search box holds a number, use it as the id to look for;
    # otherwise use -1 (an id no row ever has) so only the name/email search applies
    search_id = int(query) if query.isdigit() else -1
    results = []
    if query != "":
        if category == "treks":
            results = Trek.query.filter(db.or_(Trek.name.contains(query),
                                               Trek.location.contains(query),
                                               Trek.id == search_id)).all()
        elif category == "staff":
            results = User.query.filter_by(role='staff').filter(
                db.or_(User.username.contains(query), User.email.contains(query),
                       User.id == search_id)).all()
        else:
            results = User.query.filter_by(role='user').filter(
                db.or_(User.username.contains(query), User.email.contains(query),
                       User.id == search_id)).all()
    return render_template("admin_search.html", results=results, query=query, category=category)


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


@app.route("/staff/trek/<int:trek_id>")
def staff_trek(trek_id):
    if session.get("role") != 'staff':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None or trek.staff_id != session.get("user_id"):
        flash("You can only manage treks assigned to you.", "danger")
        return redirect("/staff")
    participants = []
    for booking in trek.bookings:
        if booking.status == 'Booked':
            participants.append(booking)
    return render_template("staff_trek.html", trek=trek, participants=participants)


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


@app.route("/profile", methods=['GET', 'POST'])
def profile():
    if session.get("role") != 'staff' and session.get("role") != 'user':
        return redirect("/login")
    current_user = User.query.get(session.get("user_id"))
    if request.method == 'POST':
        # change username, but only if the new one is not already taken by someone else
        new_username = request.form.get("username")
        taken = User.query.filter_by(username=new_username).first()
        if taken and taken.id != current_user.id:
            flash("That username is already taken.", "danger")
            return redirect("/profile")
        current_user.username = new_username
        session["username"] = new_username   # keep the navbar "Hi, ..." in sync
        current_user.contact_number = request.form.get("contact_number")
        new_password = request.form.get("new_password")
        if new_password != "":
            current_user.password = new_password
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect("/profile")
    return render_template("profile.html", current_user=current_user)


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


@app.route("/trek/<int:trek_id>/book", methods=['POST'])
def book_trek(trek_id):
    if session.get("role") != 'user':
        return redirect("/login")
    trek = Trek.query.get(trek_id)
    if trek is None:
        flash("Trek not found.", "danger")
        return redirect("/user")
    if trek.status != 'Open' or trek.available_slots < 1:
        flash("This trek is not open for booking right now.", "danger")
        return redirect("/trek/" + str(trek_id))
    already_booked = Booking.query.filter_by(user_id=session.get("user_id"),
                                             trek_id=trek.id, status='Booked').first()
    if already_booked:
        flash("You have already booked this trek.", "warning")
        return redirect("/trek/" + str(trek_id))
    new_booking = Booking(user_id=session.get("user_id"), trek_id=trek.id,
                          booking_date=date.today().strftime("%Y-%m-%d"), status='Booked')
    trek.available_slots = trek.available_slots - 1
    db.session.add(new_booking)
    db.session.commit()
    flash("Trek booked successfully!", "success")
    return redirect("/user/bookings")


@app.route("/user/bookings")
def user_bookings():
    if session.get("role") != 'user':
        return redirect("/login")
    my_bookings = Booking.query.filter_by(user_id=session.get("user_id"), status='Booked').all()
    return render_template("user_bookings.html", my_bookings=my_bookings)


@app.route("/user/bookings/cancel/<int:booking_id>", methods=['POST'])
def cancel_booking(booking_id):
    if session.get("role") != 'user':
        return redirect("/login")
    booking = Booking.query.get(booking_id)
    if booking is None or booking.user_id != session.get("user_id"):
        flash("Booking not found.", "danger")
        return redirect("/user/bookings")
    if booking.status == 'Booked':
        booking.status = 'Cancelled'
        booking.trek.available_slots = booking.trek.available_slots + 1
        db.session.commit()
        flash("Booking cancelled.", "success")
    return redirect("/user/bookings")


@app.route("/user/history")
def user_history():
    if session.get("role") != 'user':
        return redirect("/login")
    my_history = Booking.query.filter_by(user_id=session.get("user_id")).order_by(Booking.id.desc()).all()
    return render_template("user_history.html", my_history=my_history)
