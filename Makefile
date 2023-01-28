apply_migrations:
	docker-compose exec -ti booking_api alembic upgrade head

down:
	docker-compose down
