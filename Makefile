.PHONY: all build docker

all: build

build: docker

docker:
	docker build -t homehub-exporter -f docker/Dockerfile .