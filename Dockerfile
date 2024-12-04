FROM python:3.10-slim
ENV SDE="/home/p4/mysde/bf-sde-9.13.3/"
ENV SDE_INSTALL="/home/p4/mysde/bf-sde-9.13.3/install"

WORKDIR /app
COPY main.py database.py dependencies.py models.py /app/
COPY config.json requirements.txt /app/
COPY /internal/ /app/internal
COPY /routers/ /app/routers
COPY /bfrt_packages/ /bfrt_packages/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080
CMD ["python", "main.py"]
