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
