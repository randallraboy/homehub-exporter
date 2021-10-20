FROM python:3.9

RUN pip install pipenv

WORKDIR /app

COPY src/python/ /app
COPY Pipfile /app

RUN pipenv install

CMD pipenv run python main.py