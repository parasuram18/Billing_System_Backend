
# Django Billing Management System

A simple yet structured Billing Management System built using Django and Django REST Framework.

This system allows:

- Product management using Django Admin
- Invoice generation
- Invoice item tracking
- Customer purchase history
- API-based invoice retrieval
- Email invoice sending
- Balance calculation handling using Decimal

---

## Project Setup

# Clone the repository

git clone "https://github.com/parasuram18/Billing_System_Backend.git"
cd <project-folder>

# create a virtual environment

 - python -m venv venv
 - Windows: venv\Scripts\activate

 - pip install -r requirements.txt

# Database creation 
  Use PostgreSQL

  # Create Database : 
        - DB_NAME : billing_system_backend
        - DB_USER : postgres
        - DB_PASSWORD : postgres
        - DB_HOST : localhost
        - DB_PORT : 5432

# Run migrations

 - python manage.py makemigrations
 - python manage.py migrate
 
# Create Superuser
 - python manage.py createsuperuser
 - set user email and password

# Run Server
 - python manage.py runserver

     - Admin Panel : http://127.0.0.1:8000/admin/
        - Add products
        - Edit products
        - Delete products
        - Manage invoices
        - Manage users

     - Billing Page : http://127.0.0.1:8000/api/billing/
        - Generate new invoice
        - Calculate tax
        - Calculate total & balance
        - View previous customer purchases
        - Click invoice to view purchased items