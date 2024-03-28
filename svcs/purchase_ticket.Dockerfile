FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./amqp_connection.py .
COPY ./invokes.py .
COPY ./purchase_ticket.py .
COPY ./esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json .
CMD [ "python", "./amqp_connection.py", "./invokes.py", "./purchase_ticket.py" ]