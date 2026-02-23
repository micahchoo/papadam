FROM python:3.12-alpine
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache gcc musl-dev libffi-dev libc-dev bash git
# Adds our application app to the image
COPY . /app/
WORKDIR /app/
RUN pip install --upgrade pip
RUN pip install -r requirements/requirements-prod.txt
RUN pip install django-configurations@git+https://github.com/jazzband/django-configurations@2.5.1
RUN apk del git
EXPOSE 8000
