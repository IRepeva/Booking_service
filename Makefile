local-start:
	docker-compose --env-file=.env.example up -d

start:
	docker-compose up -d

local-stop:
	docker-compose --env-file=.env.example down

stop:
	docker-compose down

migration-upgrade:
	cd src/db/migrator && alembic upgrade head

migration-downgrade:
	cd src/db/migrator && alembic downgrade -1
