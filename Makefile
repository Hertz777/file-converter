up:
	docker compose up --build

down:
	docker compose down

test:
	docker compose run --rm tests

logs:
	docker compose logs -f api worker
