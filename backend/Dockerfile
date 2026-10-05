FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py carregar.py ./
EXPOSE 5000
CMD ["gunicorn", "--workers=1", "--threads=8", "--timeout", "15", "-b", "0.0.0.0:5000", "app:app"]
