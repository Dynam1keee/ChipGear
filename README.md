# ChipGear

ChipGear is an online store for computer hardware and accessories, built with Django.

**Live Demo:** [Visit ChipGear](http://92.5.126.107/)
**Note:** The website is currently accessible via HTTP only. Use `http://` instead of `https://`.

The project provides a platform for browsing computer components, searching and filtering products, managing a shopping cart, and placing orders.

## Features

- Product catalog with categories.
- Product search.
- Product filtering, including price filtering.
- Product details with images and specifications.
- Shopping cart management.
- User registration and authentication.
- Order creation and management.
- Django administration panel.

## Technologies

- Python 3.12
- Django 4.2
- SQLite
- HTML, CSS, JavaScript
- Pillow
- django-debug-toolbar
- django-nested-admin
- django-polymorphic

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Dynam1keee/ChipGear.git
cd ChipGear
```

### 2. Check Python version

**Python 3.12 is required to run this project.**

Check your Python version:

```bash
python --version
```

Make sure the output indicates Python 3.12.x before proceeding.

### 3. Create a virtual environment

**Windows:**

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS:**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file in the project root directory.

Generate a Django secret key by running:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key and add the following variables to your `.env` file:

```env
DJANGO_SECRET_KEY=your-generated-secret-key
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
```

Replace `your-generated-secret-key` with the key generated in the previous step.

`DJANGO_SECRET_KEY` is required. `DJANGO_DEBUG` enables development mode, and `DJANGO_ALLOWED_HOSTS` specifies the allowed host names.

**Note:** `DJANGO_DEBUG=True` is intended for local development only. Do not enable it in a production environment.

The `.env` file should not be committed to the repository.

### 6. Apply database migrations

The repository includes an SQLite database (`db.sqlite3`) with the initial product catalog data. You do not need to create or import the database manually.

Run:

```bash
python manage.py migrate
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open the application in your browser:

http://127.0.0.1:8000/

## Administration

To create an administrator account, run:

```bash
python manage.py createsuperuser
```

Then start the development server and open:

http://127.0.0.1:8000/admin/

## Static and Media Files

The repository includes the project's static and media files.

During local development, Django serves these files when `DJANGO_DEBUG=True`.

To collect static files into the configured `STATIC_ROOT` directory, run:

```bash
python manage.py collectstatic --noinput
```

This command is generally used when preparing the application for deployment.

## Project Structure

```text
ChipGear/
│
├── carts/              # Shopping cart application
├── goods/              # Product catalog and categories
├── main/               # Main pages
├── orders/             # Order management
├── users/              # User authentication and accounts
├── site_app/           # Project configuration and settings
│
├── fixtures/           # Project fixtures
├── media/              # Uploaded media files
├── static/             # Static files (CSS, JavaScript, images)
├── templates/          # HTML templates
│
├── db.sqlite3          # SQLite database
├── manage.py
├── requirements.txt
└── .env                # Environment variables (not included in repository)