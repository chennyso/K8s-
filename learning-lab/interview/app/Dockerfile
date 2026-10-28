FROM 192.168.204.1:15000/learning/python:3.13-slim-bookworm
WORKDIR /app
COPY requirements.txt .
COPY wheels/ /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt
COPY app.py index.html ./
USER 1000:1000
EXPOSE 8080
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
