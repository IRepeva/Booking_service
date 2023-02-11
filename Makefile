start-service:
	docker-compose up -d

stop:
	docker-compose down

migration-upgrade:
	cd src/db/migrator && alembic upgrade head

migration-downgrade:
	cd src/db/migrator && alembic downgrade -1

start:
	make start-service && make migration-upgrade

local-start:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d && make migration-upgrade
