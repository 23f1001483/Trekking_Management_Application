from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(), unique=True, nullable=False)
    email = db.Column(db.String(), unique=True, nullable=False)
    password = db.Column(db.String(), nullable=False)
    role = db.Column(db.String(), nullable=False, default='user')
    is_approved = db.Column(db.Boolean(), nullable=False, default=False)
    is_blacklisted = db.Column(db.Boolean(), nullable=False, default=False)
    contact_number = db.Column(db.String(), nullable=True)
    bookings = db.relationship('Booking', backref='user')
    assigned_treks = db.relationship('Trek', backref='staff')

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
    staff_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=True) 
    bookings = db.relationship('Booking', backref='trek')


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer(), primary_key=True)
    payment_status = db.Column(db.Boolean(), nullable=False, default=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False) 
    trek_id = db.Column(db.Integer(), db.ForeignKey('trek.id'), nullable=False) 
    booking_date = db.Column(db.String(), nullable=False)                       
    status = db.Column(db.String(), nullable=False, default='Booked')           
