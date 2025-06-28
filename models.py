from app import db
from datetime import datetime
import json

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, staff, manager
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

class Facility(db.Model):
    __tablename__ = 'facilities'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    capacity = db.Column(db.Integer)
    usd_fee = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='active')
    availability_status = db.Column(db.String(20), default='available')
    description = db.Column(db.Text)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='facility', lazy=True)

class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    allowed_facilities = db.Column(db.JSON, nullable=False)  # List of facility IDs
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='event', lazy=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='customer', lazy=True)

class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    total_fee_usd = db.Column(db.Numeric(10, 2), nullable=False)
    advance_paid_usd = db.Column(db.Numeric(10, 2), default=0)
    advance_paid_lrd = db.Column(db.Numeric(15, 2), default=0)
    payment_status = db.Column(db.String(20), default='pending')  # pending, partial, complete
    booking_status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    revenue_entries = db.relationship('Revenue', backref='booking', lazy=True)
    expenses = db.relationship('Expense', backref='booking', lazy=True)
    
    @property
    def balance_due_usd(self):
        return float(self.total_fee_usd) - float(self.advance_paid_usd)

class Revenue(db.Model):
    __tablename__ = 'revenue'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    payment_date = db.Column(db.Date, nullable=False)
    amount_usd = db.Column(db.Numeric(10, 2), default=0)
    amount_lrd = db.Column(db.Numeric(15, 2), default=0)
    currency_type = db.Column(db.String(3), nullable=False)  # USD or LRD
    payment_method = db.Column(db.String(50), default='cash')
    payment_status = db.Column(db.String(20), default='complete')
    receipt_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class Expense(db.Model):
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'))
    facility_id = db.Column(db.Integer, db.ForeignKey('facilities.id'))
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'))
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    expense_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    amount_usd = db.Column(db.Numeric(10, 2), default=0)
    amount_lrd = db.Column(db.Numeric(15, 2), default=0)
    currency_type = db.Column(db.String(3), nullable=False)
    payment_method = db.Column(db.String(50), default='cash')
    receipt_number = db.Column(db.String(50))
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CashManagement(db.Model):
    __tablename__ = 'cash_management'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_date = db.Column(db.Date, nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # deposit, withdrawal, transfer
    amount_usd = db.Column(db.Numeric(10, 2), default=0)
    amount_lrd = db.Column(db.Numeric(15, 2), default=0)
    currency_type = db.Column(db.String(3), nullable=False)
    location = db.Column(db.String(20), nullable=False)  # vault, bank
    from_location = db.Column(db.String(20))
    to_location = db.Column(db.String(20))
    description = db.Column(db.Text)
    reference_type = db.Column(db.String(20))  # revenue, expense, transfer
    reference_id = db.Column(db.Integer)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
