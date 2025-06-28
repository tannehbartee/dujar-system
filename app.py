from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from datetime import datetime, date, timedelta
import os
from functools import wraps
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dujar-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///dujar.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Fix for Railway PostgreSQL URL
if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
    app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# Import models and routes
from models import *
from routes import *

def create_tables():
    """Create database tables and insert initial data"""
    with app.app_context():
        db.create_all()
        
        # Check if data already exists
        if User.query.first() is None:
            # Create default admin user
            admin_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin = User(
                username='admin',
                password_hash=admin_password,
                role='admin',
                full_name='System Administrator',
                email='admin@dujar.com'
            )
            db.session.add(admin)
            
            # Create facilities
            facilities_data = [
                {'name': 'Auditorium', 'type': 'Event Hall', 'capacity': 500, 'usd_fee': 1500.00, 'description': 'Large auditorium for major events'},
                {'name': 'Conference Room', 'type': 'Meeting Room', 'capacity': 50, 'usd_fee': 300.00, 'description': 'Professional conference room'},
                {'name': 'Cafeteria', 'type': 'Dining Hall', 'capacity': 200, 'usd_fee': 500.00, 'description': 'Cafeteria for catering services'},
                {'name': 'Classroom', 'type': 'Educational', 'capacity': 30, 'usd_fee': 150.00, 'description': 'Standard classroom for educational activities'},
                {'name': 'Office', 'type': 'Workspace', 'capacity': 10, 'usd_fee': 200.00, 'description': 'Private office space'}
            ]
            
            for facility_data in facilities_data:
                facility = Facility(**facility_data)
                db.session.add(facility)
            
            # Create events
            events_data = [
                {'name': 'Wedding', 'description': 'Wedding reception ceremony', 'allowed_facilities': [1, 2]},
                {'name': 'Party', 'description': 'Private party or celebration', 'allowed_facilities': [1, 2]},
                {'name': 'Rally', 'description': 'Public rally or gathering', 'allowed_facilities': [1, 2]},
                {'name': 'Catering Service', 'description': 'Food service and catering', 'allowed_facilities': [3]},
                {'name': 'Schooling', 'description': 'Educational activities', 'allowed_facilities': [4, 5]},
                {'name': 'Office Work', 'description': 'Business and office activities', 'allowed_facilities': [5]}
            ]
            
            for event_data in events_data:
                event = Event(**event_data)
                db.session.add(event)
            
            # Create system settings
            settings_data = [
                {'setting_key': 'usd_to_lrd_rate', 'setting_value': '190.00', 'description': 'Exchange rate from USD to LRD'},
                {'setting_key': 'company_name', 'setting_value': 'DUJAR Facility Management', 'description': 'Company name for reports'},
                {'setting_key': 'company_address', 'setting_value': 'Monrovia, Liberia', 'description': 'Company address'},
                {'setting_key': 'advance_payment_percentage', 'setting_value': '50', 'description': 'Minimum advance payment percentage required'}
            ]
            
            for setting_data in settings_data:
                setting = SystemSetting(**setting_data)
                db.session.add(setting)
            
            db.session.commit()
            print("Database initialized with default data")

if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
