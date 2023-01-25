apply_migrations:
	docker-compose exec -ti organization_api alembic upgrade head

down:
	docker-compose down
