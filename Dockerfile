FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY rentacar/ /app/

# collectstatic needs Django settings; runtime env comes from docker-compose.
RUN DEBUG=1 SECRET_KEY=collectstatic-build-only python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "rentacar.wsgi:application"]
