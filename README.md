# GymBuddy

A Django project with Tailwind CSS for modern, responsive web development.

## Prerequisites

- Python 3.11+
- Node.js and npm
- Virtual environment (recommended)

## Setup

### 1. Python Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Node.js Dependencies

```bash
# Install Tailwind CSS and dependencies
npm install
```

### 3. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

## Development

### Running the Django Server

```bash
python manage.py runserver
```

The application will be available at `http://127.0.0.1:8000/`

### Tailwind CSS Commands

#### Build CSS (Production)
```bash
npm run build-css
```
This command compiles and minifies the Tailwind CSS from `static/src/input.css` to `static/css/output.css`.

#### Watch CSS (Development)
```bash
npm run watch-css
```
This command watches for changes in your templates and automatically rebuilds the CSS. Keep this running in a separate terminal during development.

### Collect Static Files

```bash
python manage.py collectstatic
```
Run this command to collect all static files (including compiled Tailwind CSS) into the `staticfiles` directory for production deployment.

## Project Structure

```
gymbuddy/
├── core/                    # Main Django app
│   └── templates/           # HTML templates
├── gymbuddy/                # Project settings
│   └── settings.py          # Django settings
├── static/
│   ├── src/
│   │   └── input.css       # Tailwind source file
│   └── css/
│       └── output.css       # Compiled CSS (auto-generated)
├── tailwind.config.js       # Tailwind configuration
├── package.json             # Node.js dependencies
└── requirements.txt         # Python dependencies
```

## Using Tailwind CSS in Templates

In your Django templates, load static files and include the compiled CSS:

```django
{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Page</title>
    <link rel="stylesheet" href="{% static 'css/output.css' %}">
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold text-gray-800">Hello, Tailwind!</h1>
    </div>
</body>
</html>
```

## Development Workflow

1. **Start Django server:**
   ```bash
   python manage.py runserver
   ```

2. **In a separate terminal, start Tailwind watcher:**
   ```bash
   npm run watch-css
   ```

3. Edit your templates and CSS. Tailwind will automatically rebuild when it detects changes.

4. Before deploying, build the production CSS:
   ```bash
   npm run build-css
   ```

## Additional Django Commands

```bash
# Create a new app
python manage.py startapp appname

# Make migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Access Django shell
python manage.py shell

# Run tests
python manage.py test
```

## Technologies

- **Django 5.2** - Web framework
- **Tailwind CSS 3.4.17** - Utility-first CSS framework
- **SQLite** - Database (default)

## License

[Add your license here]

