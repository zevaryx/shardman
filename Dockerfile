FROM python:3.11-slim-buster

WORKDIR /app

RUN python -m pip install poetry

COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --only main --no-root

COPY . .

CMD [ "./server" ]
