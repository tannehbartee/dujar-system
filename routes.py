from flask import render_template, request, redirect, url_for, flash, session, jsonify
from app import app, db, bcrypt
from models import *
from datetime import datetime, date, timedelta
from functools import wraps
from sqlalchemy import func, and_, or_

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/init-db')
def init_database():
    """Initialize database tables - run this once"""
    try:
        db.drop_all()  # Clear existing tables
        db.create_all()  # Create fresh tables
        
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
        db.session.commit()
        
        return "Database initialized successfully! <a href='/'>Go to Login</a>"
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get dashboard statistics
    total_bookings = Booking.query.count()
    pending_bookings = Booking.query.filter_by(payment_status='pending').count()
    total_customers = Customer.query.count()
    total_facilities = Facility.query.count()
    
    # Recent bookings
    recent_bookings = Booking.query.order_by(Booking.created_date.desc()).limit(5).all()
    
    # Monthly revenue
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_revenue_usd = db.session.query(func.sum(Revenue.amount_usd)).filter(
        func.extract('month', Revenue.payment_date) == current_month,
        func.extract('year', Revenue.payment_date) == current_year
    ).scalar() or 0
    
    monthly_revenue_lrd = db.session.query(func.sum(Revenue.amount_lrd)).filter(
        func.extract('month', Revenue.payment_date) == current_month,
        func.extract('year', Revenue.payment_date) == current_year
    ).scalar() or 0
    
    return render_template('dashboard.html',
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         total_customers=total_customers,
                         total_facilities=total_facilities,
                         recent_bookings=recent_bookings,
                         monthly_revenue_usd=monthly_revenue_usd,
                         monthly_revenue_lrd=monthly_revenue_lrd)

@app.route('/bookings')
@login_required
def bookings():
    page = request.args.get('page', 1, type=int)
    bookings = Booking.query.order_by(Booking.booking_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('bookings.html', bookings=bookings)

@app.route('/bookings/new', methods=['GET', 'POST'])
@login_required
def new_booking():
    if request.method == 'POST':
        try:
            # Get form data
            customer_id = request.form['customer_id']
            facility_id = request.form['facility_id']
            event_id = request.form['event_id']
            booking_date = datetime.strptime(request.form['booking_date'], '%Y-%m-%d').date()
            advance_amount = float(request.form.get('advance_amount', 0))
            currency_type = request.form['currency_type']
            notes = request.form.get('notes', '')
            
            # Check if date is available
            existing_booking = Booking.query.filter_by(
                facility_id=facility_id, 
                booking_date=booking_date
            ).first()
            
            if existing_booking:
                flash('This facility is already booked for the selected date', 'error')
                return redirect(url_for('new_booking'))
            
            # Get facility fee
            facility = Facility.query.get(facility_id)
            
            # Create booking
            booking = Booking(
                customer_id=customer_id,
                facility_id=facility_id,
                event_id=event_id,
                booking_date=booking_date,
                total_fee_usd=facility.usd_fee,
                notes=notes,
                created_by=session['user_id']
            )
            
            # Set advance payment
            if currency_type == 'USD':
                booking.advance_paid_usd = advance_amount
            else:
                booking.advance_paid_lrd = advance_amount
            
            # Set payment status
            if advance_amount >= float(facility.usd_fee):
                booking.payment_status = 'complete'
                booking.booking_status = 'confirmed'
            elif advance_amount > 0:
                booking.payment_status = 'partial'
                booking.booking_status = 'confirmed'
            
            db.session.add(booking)
            db.session.commit()
            
            # Create revenue entry if advance payment made
            if advance_amount > 0:
                revenue = Revenue(
                    booking_id=booking.id,
                    payment_date=date.today(),
                    currency_type=currency_type,
                    recorded_by=session['user_id']
                )
                
                if currency_type == 'USD':
                    revenue.amount_usd = advance_amount
                else:
                    revenue.amount_lrd = advance_amount
                
                db.session.add(revenue)
                db.session.commit()
            
            flash('Booking created successfully!', 'success')
            return redirect(url_for('bookings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating booking: {str(e)}', 'error')
    
    customers = Customer.query.all()
    facilities = Facility.query.filter_by(status='active').all()
    events = Event.query.all()
    
    return render_template('new_booking.html', 
                         customers=customers, 
                         facilities=facilities, 
                         events=events)

@app.route('/customers')
@login_required
def customers():
    page = request.args.get('page', 1, type=int)
    customers = Customer.query.order_by(Customer.name).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('customers.html', customers=customers)

@app.route('/customers/new', methods=['GET', 'POST'])
@login_required
def new_customer():
    if request.method == 'POST':
        try:
            customer = Customer(
                name=request.form['name'],
                address=request.form.get('address', ''),
                phone=request.form.get('phone', ''),
                email=request.form.get('email', '')
            )
            db.session.add(customer)
            db.session.commit()
            flash('Customer added successfully!', 'success')
            return redirect(url_for('customers'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding customer: {str(e)}', 'error')
    
    return render_template('new_customer.html')

@app.route('/revenue')
@login_required
def revenue():
    page = request.args.get('page', 1, type=int)
    revenue_entries = Revenue.query.order_by(Revenue.payment_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('revenue.html', revenue_entries=revenue_entries)

@app.route('/revenue/new', methods=['GET', 'POST'])
@login_required
def new_revenue():
    if request.method == 'POST':
        try:
            revenue = Revenue(
                booking_id=request.form['booking_id'],
                payment_date=datetime.strptime(request.form['payment_date'], '%Y-%m-%d').date(),
                currency_type=request.form['currency_type'],
                payment_method=request.form.get('payment_method', 'cash'),
                receipt_number=request.form.get('receipt_number', ''),
                notes=request.form.get('notes', ''),
                recorded_by=session['user_id']
            )
            
            amount = float(request.form['amount'])
            if revenue.currency_type == 'USD':
                revenue.amount_usd = amount
            else:
                revenue.amount_lrd = amount
            
            db.session.add(revenue)
            
            # Update booking payment status
            booking = Booking.query.get(revenue.booking_id)
            total_paid_usd = db.session.query(func.sum(Revenue.amount_usd)).filter_by(
                booking_id=booking.id).scalar() or 0
            
            booking.advance_paid_usd = total_paid_usd
            
            if total_paid_usd >= float(booking.total_fee_usd):
                booking.payment_status = 'complete'
            elif total_paid_usd > 0:
                booking.payment_status = 'partial'
            
            db.session.commit()
            flash('Revenue entry added successfully!', 'success')
            return redirect(url_for('revenue'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding revenue: {str(e)}', 'error')
    
    bookings = Booking.query.filter(Booking.payment_status.in_(['pending', 'partial'])).all()
    return render_template('new_revenue.html', bookings=bookings)

@app.route('/expenses')
@login_required
def expenses():
    page = request.args.get('page', 1, type=int)
    expenses = Expense.query.order_by(Expense.expense_date.desc()).paginate(
        page=page, per_page=20, error_out=False)
    return render_template('expenses.html', expenses=expenses)

@app.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    if request.method == 'POST':
        try:
            expense = Expense(
                booking_id=request.form.get('booking_id') or None,
                facility_id=request.form.get('facility_id') or None,
                event_id=request.form.get('event_id') or None,
                customer_id=request.form.get('customer_id') or None,
                expense_date=datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date(),
                category=request.form['category'],
                description=request.form['description'],
                currency_type=request.form['currency_type'],
                payment_method=request.form.get('payment_method', 'cash'),
                receipt_number=request.form.get('receipt_number', ''),
                recorded_by=session['user_id']
            )
            
            amount = float(request.form['amount'])
            if expense.currency_type == 'USD':
                expense.amount_usd = amount
            else:
                expense.amount_lrd = amount
            
            db.session.add(expense)
            db.session.commit()
            flash('Expense entry added successfully!', 'success')
            return redirect(url_for('expenses'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding expense: {str(e)}', 'error')
    
    bookings = Booking.query.all()
    facilities = Facility.query.all()
    events = Event.query.all()
    customers = Customer.query.all()
    
    expense_categories = [
        'Staff Fees', 'Security', 'DJ Fee', 'Cleaning', 
        'Repairs', 'Lighting', 'Sundry Expense'
    ]
    
    return render_template('new_expense.html', 
                         bookings=bookings, 
                         facilities=facilities,
                         events=events,
                         customers=customers,
                         expense_categories=expense_categories)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/reports/income-expense')
@login_required
def income_expense_report():
    # Get date range from query parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date:
        start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = date.today().strftime('%Y-%m-%d')
    
    # Revenue data
    revenue_query = db.session.query(
        Revenue, Booking, Facility, Event, Customer
    ).join(Booking).join(Facility).join(Event).join(Customer).filter(
        Revenue.payment_date.between(start_date, end_date)
    ).order_by(Facility.name, Event.name, Customer.name)
    
    # Expense data
    expense_query = db.session.query(
        Expense, Facility, Event, Customer
    ).outerjoin(Facility).outerjoin(Event).outerjoin(Customer).filter(
        Expense.expense_date.between(start_date, end_date)
    ).order_by(Facility.name, Event.name, Customer.name)
    
    revenue_data = revenue_query.all()
    expense_data = expense_query.all()
    
    return render_template('income_expense_report.html',
                         revenue_data=revenue_data,
                         expense_data=expense_data,
                         start_date=start_date,
                         end_date=end_date)

@app.route('/settings')
@admin_required
def settings():
    settings = SystemSetting.query.all()
    facilities = Facility.query.all()
    users = User.query.all()
    return render_template('settings.html', 
                         settings=settings, 
                         facilities=facilities,
                         users=users)

@app.route('/api/check-availability')
@login_required
def check_availability():
    facility_id = request.args.get('facility_id')
    booking_date = request.args.get('date')
    
    if not facility_id or not booking_date:
        return jsonify({'available': False, 'message': 'Missing parameters'})
    
    try:
        booking_date = datetime.strptime(booking_date, '%Y-%m-%d').date()
        existing_booking = Booking.query.filter_by(
            facility_id=facility_id,
            booking_date=booking_date
        ).first()
        
        if existing_booking:
            return jsonify({
                'available': False, 
                'message': f'Facility already booked by {existing_booking.customer.name}'
            })
        else:
            return jsonify({'available': True, 'message': 'Date available'})
            
    except Exception as e:
        return jsonify({'available': False, 'message': str(e)})

@app.route('/api/facility-events')
@login_required
def facility_events():
    facility_id = request.args.get('facility_id')
    if not facility_id:
        return jsonify([])
    
    # Get events that can be held in this facility
    events = Event.query.all()
    allowed_events = []
    
    for event in events:
        if int(facility_id) in event.allowed_facilities:
            allowed_events.append({
                'id': event.id,
                'name': event.name,
                'description': event.description
            })
    
    return jsonify(allowed_events)
    @app.route('/init-db')
def init_database():
    """Initialize database tables and default data"""
    try:
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        if not User.query.first():
            # ... (rest of the code I provided)
