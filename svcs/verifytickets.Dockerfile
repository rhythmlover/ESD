FROM python:3-slim
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY ./invokes.py .
COPY ./verifytickets.py .
COPY ./esd-ticketing-firebase-adminsdk-dxgtc-363d36e381.json .
CMD [ "python", "invokes.py", "./verifytickets.py" ]