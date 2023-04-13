
# Installation Manual
## Signing Adapter Docker Image
## version 1.0

## Pre-requisite
- Server or VM Server minimum requirements

|Specification    |Minimum requirement    |
|----|----|
|Core Processor|2 Core|
|RAM|4 GB|
|Storage|20 GB|
|Operating System|Any Linux|

## Installation of docker engine
This manual using docker on Ubuntu Linux Operating System,
for other linux distro or operating system refer to this official docker installation documentation https://docs.docker.com/engine/install/

### uninstall old version if any
Older versions of Docker went by the names of docker, docker.io, or docker-engine, you might also have installations of containerd or runc. Uninstall any such older versions before attempting to install a new version:
```bash
$ sudo apt-get remove docker docker-engine docker.io containerd runc
```

### Install using the apt repository
Before you install Docker Engine for the first time on a new host machine, you need to set up the Docker repository. Afterward, you can install and update Docker from the repository.

#### Set up the repository
1. Update the apt package index and install packages to allow apt to use a repository over HTTPS:

 ```bash
 $ sudo apt-get update
 $ sudo apt-get install \
    ca-certificates \
    curl \
    gnupg
 ```
2. Add Docker’s official GPG key:

 ```bash
 $ sudo install -m 0755 -d /etc/apt/keyrings
 $ curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg \
    --dearmor -o /etc/apt/keyrings/docker.gpg
 $ sudo chmod a+r /etc/apt/keyrings/docker.gpg
 ```
3. Use the following command to set up the repository:

 ```bash
 $ echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings /docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
 ```
 
#### Install Docker Engine

1. Update the apt package index:

 ```bash
 $ sudo apt-get update
 ```
2. Install Docker Engine, containerd, and Docker Compose.
 
 To install the latest version, run:
 ```bash
 $ sudo apt-get install \
    docker-ce docker-ce-cli \
    containerd.io docker-buildx-plugin \
    docker-compose-plugin
 ```
3. Verify that the Docker Engine installation is successful by running the hello-world image:
 ```bash
 $ sudo docker run hello-world
 ```
 
## Installation of signing adapter docker image

### prerequisite

1. Create directory for document storage 
 ```bash
 $ sudo mkdir -p /root/logs
 $ sudo mkdir -p /root/sharefolder
 $ sudo mkdir -p /root/sharefolder/SIGNED 
 $ sudo mkdir -p /root/sharefolder/UNSIGNED 
 $ sudo mkdir -p /root/sharefolder/SPECIMEN
 ```
 ** note: on production these folder maybe located in NFS storage or similar
 
2. Create folder for project file on your home folder and change directory to created directory
 ```bash
 $ cd $HOME
 $ mkdir -p signadapter
 $ cd signadapter
 ```
 
3. Create docker-compose.yml configuration file to running container using docker compose
 ```bash
 $ touch docker-compose.yml
 ```
 edit using your favorite text editor
 ```bash
 $ nano docker-compose.yml
 ```
 write this configuration and save file
 ```yaml
 version: '3.1'
    services:
        adapter:
            container_name: perisai-adapter
            image: registry.perurica.co.id:443/keysign/signadapter:latest
            restart: always
            privileged: true
            ports: 
            - "9044:7777"
            environment:
                HASH_URL: https://apgdev.peruri.co.id:9044/gateway/digitalCertificateHashSign/1.0/signingHash/v1
                CERTIFICATE_CHAIN_URL: https://apgdev.peruri.co.id:9044/gateway/digitalCertificateHashSign/1.0/getCertificateChain/v1
                TSA_URL: http://timestamp.peruri.co.id/signserver/tsa?workerName=TimeStampSigner1101
                TZ: Asia/Jakarta
                UNSIGNED_FOLDER: /sharefolder/UNSIGNED
                SIGNED_FOLDER: /sharefolder/SIGNED
                SPC_FOLDER: /sharefolder/SPECIMEN
                KEYSTORE: /certs
                WORKER: 4
                TIMEOUT: 240
                GRACEFUL_TIMEOUT: 320
                KEEP_ALIVE: 30
            volumes:
                - /root/logs:/logs
                - /root/sharefolder:/sharefolder
 ```
4. Run the container

 Run the docker container using docker compose
 ```bash
 $ sudo docker-compose up -d
 ```
 verify the running docker container
 ```bash
 $ sudo docker ps
 ```
 here the sample output
 ```bash
 CONTAINER ID   IMAGE                                                      COMMAND                CREATED        STATUS                       PORTS                              NAMES
8ba281c25a23   registry.perurica.co.id:443/keysign/signadapter:latest     "/bin/app"             3 hours ago    Up About an hour             0.0.0.0:9044->7777/tcp             perisai-adapter
 ```
 
5. Verify using browser and access documentation
 
 Type at the address bar of browser http://vm-or-server-ip-address:9044 you will welcome by json message
 ```json
 {
    message: "Welcome to Signing Adapter 0.0.5-a",
    docUrl: "/documentation",
    redocUrl: "/redoc"
}
 ```
 the documentation could be accessed at /documentation endpoint for swagger-ui interface or /redoc endpoint for redoc interface