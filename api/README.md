# papad-api
We are developing a tool called Participatory Listening and Sense-Making of Archives (PLASMA), previously known as Papad, a decentralised hypermedia annotation tool designed for use in regions with low internet connectivity and low-literate populations. PLASMA enables the creation and sharing of audio/video-based knowledge, making it accessible to those with lower literacy levels. It empowers communities to voice their perspectives on topics like art, culture, education, and technology, preserving knowledge for future generations. Our project focuses on web accessibility tailored to India's cultural, literacy, and socio-economic contexts. PLASMA allows users to upload audio, tag fragments, and create audio-visual stories, serving as a publishing platform without the barriers of literacy.

[Click here](https://open.janastu.org/projects/papad) to know more about this project.

[![Build Status](https://travis-ci.org/janastu/papad-api.svg?branch=master)](https://travis-ci.org/janastu/papad-api)
[![Built with](https://img.shields.io/badge/Built_with-Cookiecutter_Django_Rest-F7B633.svg)](https://github.com/agconti/cookiecutter-django-rest)

Papad Backend API. Check out the project's [documentation](http://janastu.github.io/papad-api/).

# Prerequisites

- [Docker](https://docs.docker.com/docker-for-mac/install/)

# Local Development

Start the dev server for local development:
```bash
docker-compose up
```

Run a command inside the docker container:

```bash
docker-compose run --rm web [command]
```



Integrations to consider later
1. Healthcheck ? https://github.com/mwarkentin/django-watchman/
2. Thumbnail images ? https://easy-thumbnails.readthedocs.io/en/latest/index.html
3. Migrate from DRF to Ninja ? https://django-ninja.rest-framework.com/ (Question is do we need such a powerful framework when we just need a simple API system ?)
4. Organizations / Groups : https://github.com/bennylope/django-organizations/ if so then also https://github.com/soynatan/django-easy-audit
5. Input sanitization ? https://github.com/mozilla/bleach
6. Statistics :https://goaccess.io/ and https://monitoror.com/documentation/


Known Limitations :

1. Everytime you bring a app up, you will need to manually login to minio, and change the access mode to public.
