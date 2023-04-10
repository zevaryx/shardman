FROM python:3.11

RUN apt-get update

WORKDIR /app

COPY . /app
RUN pip install --no-cache-dir .

CMD [ "./server" ]