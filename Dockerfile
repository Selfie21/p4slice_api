#FROM python:3.10-slim
FROM python:3.10
ENV SDE="/home/p4/mysde/bf-sde-9.13.3/"
ENV SDE_INSTALL="/home/p4/mysde/bf-sde-9.13.3/install"

WORKDIR /app
COPY main.py config.json requirements.txt /app/
COPY  /core /app/core
COPY /internal /app/internal
COPY /routers /app/routers
COPY /bfrt_packages /bfrt_packages

#RUN pip install --no-cache-dir -r requirements.txt
RUN apt install curl
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
