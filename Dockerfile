FROM node:22-bookworm-slim AS frontend
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim-bookworm
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./backend/
COPY question-banks/ ./question-banks/
COPY --from=frontend /build/frontend/dist ./frontend/dist
RUN mv backend/data /app/seed-data && mkdir -p backend/data
COPY deploy/start.py ./deploy/start.py
EXPOSE 8000
CMD ["python", "deploy/start.py"]
