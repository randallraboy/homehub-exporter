.PHONY: all build docker docker_push push

all: build

build: docker

push: docker_push

docker:
	docker build -t homehub-exporter -t rraboy/homehub-exporter -f docker/Dockerfile .

docker_push:
	docker push rraboy/homehub-exporter