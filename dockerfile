FROM python:3.12-slim-bookworm
RUN apt update && apt upgrade -y
RUN apt install -y ffmpeg

WORKDIR /musicbot
COPY requirements.txt requirements.txt
# RUN pip3 install -r requirements.txt
RUN pip3 install discord.py[voice] python-dotenv yt-dlp

COPY . .
CMD ["python", "main.py"]
