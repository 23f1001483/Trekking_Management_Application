from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


#Table 1: User (admin, staff and trekkers ALL live in this one table):
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False, default='user')
    is_approved = db.Column(db.Boolean(), nullable=False, default=False)    # staff need admin approval before they can log in
    is_blacklisted = db.Column(db.Boolean(), nullable=False, default=False) # admin can block an account
    contact_number = db.Column(db.String(), nullable=True)                  # phone number (optional)
    bookings = db.relationship('Booking', backref='user')                   # One user (a trekker) can have many bookings. [One to Many]
    assigned_treks = db.relationship('Trek', backref='staff')               #One user (a staff member) can be assigned many treks.[One to Many]

#Table 2: Trek:
class Trek(db.Model):
    __tablename__ = 'trek'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(), nullable=False)                           
    location = db.Column(db.String(), nullable=False)
    difficulty = db.Column(db.String(), nullable=False)                         
    duration_days = db.Column(db.Integer(), nullable=False)                 
    available_slots = db.Column(db.Integer(), nullable=False)               
    status = db.Column(db.String(), nullable=False, default='Pending')          
    start_date = db.Column(db.String(), nullable=False)
    end_date = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=False)
    staff_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True) # nullable=True so a trek can exist before the admin assigns a staff member.
    bookings = db.relationship('Booking', backref='trek')                       # One trek can have many bookings.


#Table 3: Booking (one user booking one trek)
class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer(), primary_key=True)
    payment_status = db.Column(db.Boolean(), nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False) 
    trek_id = db.Column(db.Integer(), db.ForeignKey('trek.id'), nullable=False) 
    booking_date = db.Column(db.String(), nullable=False)                       
    status = db.Column(db.String(), nullable=False, default='Booked')           
