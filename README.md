# Aplika-backend

A Django backend project with Celery integration and a Job Board app that supports multiple data sources.

## Features
- Django 4.x
- Celery for background tasks
- Celery Beat for scheduled tasks (Hirebase task and delete old jobs task)
- Support for multiple job data sources (Hirebase)
- Environment variable configuration via `.env`

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd aplica_backend
```

### 2. Create and activate a virtual environment
```bash
python3 -m venv ../aplika-env
source ../aplika-env/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
- Copy `sample.env` to `.env` and fill in your values:
```bash
cp sample.env .env
```

### 5. Run migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create a superuser (optional, for admin access)
```bash
python manage.py createsuperuser
```

### 7. Start Redis server (required for Celery)
Make sure Redis is running locally. You can install it via your package manager, e.g.:
```bash
sudo apt-get install redis-server
sudo service redis-server start
```

## Running the Project

### Start Django development server
```bash
python manage.py runserver
```

### Start Celery worker
```bash
celery -A aplica_backend worker --loglevel=info --concurrency 8
```

### Start Celery Beat (scheduler)
```bash
celery -A aplica_backend beat --loglevel=info
```

### Run the Hirebase Celery task manually
You can enqueue the Hirebase Celery task using the custom Django command:
```bash
python manage.py run_hirebase_task
```

### Run the delete old jobs Celery task manually
You can enqueue the delete old jobs Celery task using the custom Django command:
```bash
python manage.py delete_old_jobs
```

## Project Structure
- `aplica_backend/` - Django project root
- `job_board/` - Main app for job board features
- `.env` - Your environment variables (not committed)
- `sample.env` - Example environment variables

## Data Sources
The application supports multiple job data sources:
- **Hirebase**: Primary job data source (configured via JOB_API_ENDPOINT and JOB_API_KEY)

Each job record includes a `job_type` field to track its data source.

## Notes
- The Hirebase task, RapidAPI task, and delete old jobs task are scheduled to run every 12 hours automatically by Celery Beat.
- All sensitive/configurable settings are in `.env`.
- Make sure Redis is running before starting Celery.
- Only the following direct dependencies are required (see requirements.txt): Django, celery, redis, python-dotenv, requests.

## Database Configuration for Multiple Workers

When running multiple Celery workers, you may encounter database locking issues with SQLite. To resolve this:

### Option 1: Use PostgreSQL (Recommended for Production)
Update your `.env` file:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
```

### Option 2: Optimize SQLite for Multiple Workers
The current configuration includes SQLite timeout settings to handle concurrent access. For better performance with multiple workers:

1. **Reduce worker concurrency** if using SQLite:
   ```bash
   celery -A aplica_backend worker --loglevel=info --concurrency=2
   ```

2. **Use separate database files** for different workers (advanced setup)

3. **Consider using WAL mode** for SQLite (requires additional configuration)




