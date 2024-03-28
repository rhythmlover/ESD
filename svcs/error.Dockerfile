FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./error.py ./amqp_connection.py ./
COPY ./esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json .
CMD [ "python", "./error.py" ]