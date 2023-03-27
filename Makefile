clean:
	docker image rm musicbot

build:
	docker build -t musicbot .

run:
	docker compose up -d 