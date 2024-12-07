FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8080

COPY /bfrt_packages /bfrt_packages
COPY main.py requirements.txt /app/
COPY  /core /app/core
COPY /internal /app/internal
COPY /routers /app/routers

CMD ["python", "main.py"]
