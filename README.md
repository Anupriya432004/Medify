# Medify – Online Pharmacy Platform

## About the Project

Medify is a web-based online pharmacy platform developed using Python and Django. It allows users to browse medicines, manage their shopping cart, place orders, and access an AI-powered assistant.

## Features

* User registration and login
* Browse and search medicines
* View medicine details and prices
* Add medicines to the shopping cart
* Place and manage orders
* Razorpay payment integration
* AI assistant powered by Google Gemini API
* Responsive user interface

## Technologies Used

* **Backend:** Python, Django
* **Frontend:** HTML, CSS, JavaScript
* **Database:** Configured through Django settings
* **API:** Django REST Framework (if enabled in the project)
* **AI Integration:** Google Gemini API
* **Payment Gateway:** Razorpay
* **Tools:** VS Code, Git, GitHub

## Project Structure

```text
Medify/
├── ai_assistant/
├── core/
├── medicines/
├── medify_project/
├── orders/
├── users/
├── manage.py
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Medify.git
cd Medify
```

Replace `YOUR-USERNAME` with your GitHub username.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

If your project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

Otherwise, install the packages required by your project.

### 4. Configure Environment Variables

Create a `.env` file in the main project folder and add your own credentials:

```env
GEMINI_API_KEY=your_gemini_api_key
DJANGO_SECRET_KEY=your_django_secret_key
```

Never upload your `.env` file or API keys to GitHub.

### 5. Apply Database Migrations

```bash
python manage.py migrate
```

### 6. Run the Development Server

```bash
python manage.py runserver
```

Open your browser and visit:

http://127.0.0.1:8000/

## Security

* Keep API keys and secret keys in environment variables.
* Never commit passwords or sensitive credentials.
* Use secure payment verification for online transactions.
* Consult a qualified healthcare professional for medical advice; AI-generated information is not a substitute for professional care.

## Future Enhancements

* Medicine availability notifications
* Improved AI assistant features
* Order tracking
* Enhanced user dashboard
* Deployment to a production server

## Author

**Anupriya M.D**

## License
This project is developed for educational and learning purposes.
