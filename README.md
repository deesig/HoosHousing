# HoosHousing?

**HoosHousing?** is a subleasing web application built for University of Virginia (UVA) students to easily find, list, and manage off-Grounds housing opportunities.

## 🎯 Purpose

This project was developed as part of **CS 3240: Advanced Software Development** at the University of Virginia. It aims to solve common pain points students face when subleasing apartments, offering features such as:

- Posting available subleases  
- Browsing available listings by region  
- Secure account registration and login  
- Tag-based filtering and search  
- Listing collections and favorites  
- Admin approval and moderation system

## 🛠️ Tech Stack

- **Backend**: Django 5.1, Django REST Framework  
- **Frontend**: Django Templates + Bootstrap 5  
- **Database**: PostgreSQL  
- **Authentication**: dj-rest-auth, django-allauth, SimpleJWT  
- **Cloud Storage**: AWS S3 (via `django-storages` and `boto3`)  
- **Deployment**: Gunicorn + Whitenoise  
- **Misc**: Python Decouple, django-extensions

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/project-a-30.git
   cd hooshousing

Create and activate a virtual environment:

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

Install dependencies:

```
pip install -r requirements.txt
```


Set up your .env file (using python-decouple) with required environment variables (example provided in .env.example).

Apply migrations and run the server:

    python manage.py migrate
    python manage.py runserver

🧪 Development & Testing

Run unit tests:

```
python manage.py test
```

Enable Django Extensions shell:

    python manage.py shell_plus

🧑‍💻 Contributors

    Austin Trinh (@deesig)

    Geethan Sundaram (@gthsun)

    Hyun Lee (@dlwhdgus0810)

    Chris Dai (@chrisdaid)

    Tiger Zhang (@usz7pc)

    Developed by CS 3240 S25 Team A-30

📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
