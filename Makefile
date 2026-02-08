run:
	python manage.py runserver

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
