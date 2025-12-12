FROM python:3.10-slim

WORKDIR /app


COPY . /app/

COPY templates/ /app/templates/
COPY static/ /app/static/

ENV PYTHONPATH="/app"

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py"]
