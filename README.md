# DUJAR Facility Rental Management System

A comprehensive cloud-based facility rental management system built with Flask and PostgreSQL.

## Features

- **Facility Management**: Manage multiple facilities with different capacities and fees
- **Event Management**: Handle various event types with facility restrictions
- **Customer Management**: Track customer information and booking history
- **Booking System**: Calendar-based booking with availability checking
- **Dual Currency Support**: Handle both USD and LRD transactions
- **Financial Tracking**: Revenue and expense management with detailed reporting
- **User Authentication**: Role-based access (Admin, Staff, Manager)
- **Reports**: Income/Expense reports grouped by facility, event, and customer

## Quick Deployment to Railway

1. **Fork this repository** to your GitHub account

2. **Sign up for Railway** at [railway.app](https://railway.app)

3. **Create a new project** and connect your GitHub repository

4. **Add PostgreSQL database**:
   - In Railway dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically set DATABASE_URL

5. **Deploy the application**:
   - Railway will automatically detect the Flask app
   - The app will be available at your Railway URL

6. **Access the system**:
   - Default login: `admin` / `admin123`
   - Change the default password immediately

## Local Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables (copy `.env.example` to `.env`)
4. Run: `python app.py`

## Default Data

The system comes pre-configured with:

### Facilities
- Auditorium ($1,500)
- Conference Room ($300)
- Cafeteria ($500)
- Classroom ($150)
- Office ($200)

### Events
- Wedding (Auditorium, Conference Room)
- Party (Auditorium, Conference Room)
- Rally (Auditorium, Conference Room)
- Catering Service (Cafeteria)
- Schooling (Classroom, Office)
- Office Work (Office)

## User Roles

- **Admin**: Full system access, user management, settings
- **Staff**: Data entry, editing, viewing
- **Manager**: View-only access to all data

## Support

For issues or questions, please create an issue in the GitHub repository.
