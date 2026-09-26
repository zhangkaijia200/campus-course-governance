.PHONY: up down logs test loadtest

up:
	docker compose up --build

down:
	docker compose down -v

logs:
	docker compose logs -f backend worker

test:
	docker compose run --rm backend pytest -q

loadtest:
	docker compose --profile loadtest run --rm locust -f /mnt/locust/locustfile.py --headless -u 200 -r 20 -t 60s
