run:
	uvicorn diplom.asgi:application --host 0.0.0.0 --port 8000

migrations:
	python manage.py makemigrations $(app) -n '$(name)'

migrate:
	python manage.py migrate $(app)

test:
	python manage.py test

install:
	uv pip install -r pyproject.toml

showmigrate:
	python manage.py showmigrations

ruff:
	ruff format .

pc:
	pre-commit clean && pre-commit install && pre-commit autoupdate && pre-commit migrate-config
