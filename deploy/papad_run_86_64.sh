echo "This script will download and install Papad on your system."

# Verify that we can at least get version output
echo "Checking if docker is installed in the system"
if ! docker --version; then
	echo "Docker not found. Installing now. Installation needs sudo rights to install docker"
	curl -fsSL https://get.docker.com | sudo bash
    echo `docker --version`
else
    echo "Docker found in server"
    echo `docker --version`
fi

echo "Checking if docker-compose is installed in the system"
if ! docker-compose --version; then
	echo "Docker Compose not found. Installing now. Installation needs sudo rights to install docker-compose"
	sudo curl -SL https://github.com/docker/compose/releases/download/v2.5.0/docker-compose-linux-x86_64 -o /usr/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
else
    echo "Docker-Compose found in server"
    echo `docker-compose --version`
fi

echo "Starting the papad installation now."
echo "Installation path is `pwd`"

echo "Downloading config"
wget https://gitlab.com/servelots/papad/papad-docker/-/raw/main/service_config.env.sample?inline=false
mv service_config.env.sample service_config.env
echo "Edit the service config.env file with any changes required."
wget https://gitlab.com/servelots/papad/papad-docker/-/raw/main/docker-compose.yml?inline=false
docker-compose up -d

echo "All systems should be up and running. The application should be running in <server_ip>:80"
echo "Mandatory first time step: Please open <server_ip>:9001 and change the papad bucket permissions from private to public. Credentials are found in service_config.env"