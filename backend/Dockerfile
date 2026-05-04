FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variable for the database URL
ENV MONGO_URL=mongodb://mongo:27017

EXPOSE 8000

# Script to seed the database and then start the server
CMD ["sh", "-c", "python backend/seed_db.py && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
