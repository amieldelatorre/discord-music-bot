FROM python:slim-bullseye
RUN apt update && apt upgrade -y
RUN apt install -y ffmpeg

WORKDIR /musicbot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
CMD ["python", "main.py"]