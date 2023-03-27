# FROM python:slim-bullseye
# RUN apt update && apt upgrade -y
# RUN apt install -y ffmpeg

# WORKDIR /musicbot
# COPY requirements.txt requirements.txt
# RUN pip3 install -r requirements.txt

# COPY . .
# CMD ["python", "main.py"]

############### Using ubuntu as a base because there are currently errors when running with the python base ###############

FROM ubuntu
RUN apt update && apt upgrade -y
RUN apt install python3.11 -y
RUN apt install python3-pip -y
RUN apt install ffmpeg -y

WORKDIR /musicbot
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .
CMD ["python3", "main.py"]
