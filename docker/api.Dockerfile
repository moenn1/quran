FROM python:3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY docker/api/bootstrap-api.py /app/bootstrap-api.py

EXPOSE 8000

CMD ["python", "/app/bootstrap-api.py"]
