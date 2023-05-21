# Expose HTTP server from Flask directly - host is responsible for SSL termination
FROM python:3.11

COPY pip-requirements.txt /app/pip-requirements.txt
WORKDIR /app
RUN pip3 install -r pip-requirements.txt

COPY ./discordemoji /app/discordemoji

ENTRYPOINT ["python3", "-m", "discordemoji"]
