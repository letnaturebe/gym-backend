# pull official base image
FROM python:3.10.1-slim-buster

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
WORKDIR /app

# new
# install system dependencies
RUN apt-get update \
  && apt-get -y install gcc postgresql \
  && apt-get clean


# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

COPY ./start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

# add app
COPY . .

