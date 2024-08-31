FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/logs && chmod -R 755 /app/logs

COPY . .

# Expose port
EXPOSE 3000

# application start
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
