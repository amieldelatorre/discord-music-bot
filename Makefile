name := musicbot

bootstrap:
	docker build -t ${name} .
	docker compose up -d

refresh:
	docker container stop ${name}
	docker container rm ${name}
	docker image rm ${name}
	docker build -t ${name} .
	docker compose up -d

clean:
	docker container stop ${name}
	docker container rm ${name}
	docker image rm ${name}

build:
	docker build -t ${name} .

run:
	docker compose up -d 

stop:
	docker stop ${name}

start:
	docker start ${name}