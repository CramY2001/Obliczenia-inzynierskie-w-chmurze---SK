FROM python:latest

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir numpy scipy

CMD ["python", "wspolcynnik_bezpieczenstwa.py"]