# papad-docker

### Introduction

This repository is only meant for deployment. If you are developer wanting to develop explore [papad-api for backend API's](https://gitlab.com/servelots/papad/papad-api) , [papad-ui for the User Interface](https://gitlab.com/servelots/papad/papad-ui) or if you want to contribute to documentation explore [papad-docs](https://gitlab.com/servelots/papad/papad-docs).

### Components

Papad consists of 6 systems.
1. The API which is the interface for the database. This is the system that processes and stores your data, searches in the database for keywords or search strings.
2. The Background process layer ensures all necessary long running background apps are processed. This includes, deletion of media / annotations, email triggers(if any etc)
3. The UI is the layer that ensures that end users have a known style interface to interact with Papad.
4. Documentation currently for user documentation but would eventually also start having the API documentation.
5. A nginx web server to enable and run this system at scale.
6. A local minio for scalable storage.

### Requirements

1. Ports 80,443, 8000, 9000, 9001 are needed for the app to work (Refer to the Advanced section if you want selective ports or if you are running nginx already)
2. Storage of atleast 1GB for data storage


### The 1 liner to setup Papad (Not for pro's )

*Note:

    1. Altough nginx and minio are bundled, they dont come up by default. You need to use the respective docker profiles to bring up the same. 
    2. We will currently only support GNU/Linux based systems on x86_64 architecture and RasPi.
    3. The script does not support upgrades. For upgrades, follow the instructions at[upgrade](upgrade.md).
    4. This is only the first time setup script.
*

For installing in x86_64 architecture servers, please use this script   : ``` curl -Lso- https://gitlab.com/servelots/papad/papad-docker/-/raw/main/papad_run_86_64.sh | bash ```
For installating in RasPi, please use this script : ```To be done. Please track status here: https://gitlab.com/servelots/papad/papad-docker/-/issues/1 ```

### Papad setup for Pro's
1. Install docker and docker-compose
2. Clone this repository
3. Follow Post Install section from here


### Post Install (First time only)

1. copy the service_config.env.sample as service_config.env and edit the values you need to change. Common edit values are minio/s3 settings, secret key, production environment.
2. Post step1 or anytime you change service_config.env , you will need to do ```docker-compose down && docker-compose up```
3. Setup DNS entries for papad.local, docs.papad.local and minio.papad.local to either 172.17.0.1 on your personal computing device or to the network available private IP to be acceessible from the network.
4. Open minio.papad.local and login using the credentials given in service_config.env, Create new Bucket, give the new bucket name as `papad` (or anyname you have set in the respective service_config.env). Go to settings or Manage of the `papad` bucket, and change the visibility to `public`.
5. [IMPORTANT] Clone the UI into the build folder. This is currently not a public activity, as it requies a react build. Since not all of our environments work with internet, you need to download the latest static files from stories server. we are * working on optimising this and should be fixed in the upcoming 2.8 release* .
5. Open papad.local for the UI , docs.papad.local for documentation.

### Upgrades

This step is to be followed for all upgrades after first time step

1. ```docker-compose down ```
2. ``` docker-compose pull ```
3. ``` docker-compose --profile app --profile docs --profile webserver up -d ```

### Customize docker-compose

It is not advised to change the docker-compose file directly. For this reason please override docker-compose.yml with docker-compose-override.yml(feel free to name this file as you wish) and then run the compose as following

```
docker-compose -f docker-compose.yml -f docker-compose-override.yml up -d

```
You can use the override file to modify specific parameters of the defination like ports etc. Please read [this documentation](https://docs.docker.com/compose/extends/#different-environments ) for more understanding and examples.

# Advanced guides
1. We have docker-compose profiles enabled in the app. So if you want to use docker-compose only for apps and dont want to run nginx or docs, do the following 
  ``` docker-compose --profile webserver --profile minio up -d```. this will bring up the app along with nginx and minio and not docs. Feel free to refer to the nginx config's in the nginx folder and write you own.
