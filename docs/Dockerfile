FROM python:3.8
ENV PYTHONUNBUFFERED 1

# Allows docker to cache installed dependencies between builds
COPY . /app/
RUN pip install -r /app/requirements.txt


WORKDIR /app/
EXPOSE 8001

RUN mkdocs build
# Run the production server
CMD cd /app/ && mkdocs serve
