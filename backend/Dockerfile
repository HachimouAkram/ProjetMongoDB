FROM python:3.10-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Environment variable for the database URL
ENV MONGO_URL=mongodb+srv://hachimouakram_db_user:Akram2026@cluster0.cozgyvx.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0

EXPOSE 8000

# Script to seed the database and then start the server
# On utilise ; pour que uvicorn se lance même si le seed a fini son travail
CMD ["sh", "-c", "python backend/seed_db.py ; uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
