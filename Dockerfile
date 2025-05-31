FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure staticfiles directory exists
RUN mkdir -p staticfiles

# Run collectstatic with dummy SECRET_KEY
RUN SECRET_KEY=dummy python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "recipe_api.wsgi:application"]