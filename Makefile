.PHONY: install start test docker-build docker-up docker-down

install:
	pip install -r requirements.txt

start:
	bash start.sh

test:
	pytest -v tests/

docker-build:
	docker build -t judge0-arm64:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

clean:
	rm -rf /tmp/judge0_sandbox/* __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache
