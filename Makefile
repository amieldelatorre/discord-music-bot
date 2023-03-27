name := musicbot

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