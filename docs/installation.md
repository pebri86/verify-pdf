
# Installation Manual
## PDF Verification Docker Image
## version 1.0

## Prerequisites
- Minimum requirements for server or VM server:

|Specification    |Minimum requirement    |
|----|----|
|Core Processor|2 Core|
|RAM|4 GB|
|Storage|20 GB|
|Operating System|Any Linux|

## Installation of docker engine
This manual uses Docker on Ubuntu Linux Operating System. For other Linux distributions or operating systems, refer to the official Docker installation documentation at https://docs.docker.com/engine/install/

### Uninstall old version (if any)
Older versions of Docker were known as docker, docker.io, or docker-engine, and you might also have installations of containerd or runc. Uninstall any such older versions before attempting to install a new version:
```bash
$ sudo apt-get remove docker docker-engine docker.io containerd runc
```

### Install using the apt repository
Before installing Docker Engine for the first time on a new host machine, you need to set up the Docker repository. Afterward, you can install and update Docker from the repository.

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
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings /docker.gpg] https://download.docker.com/linux/ubuntu \
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
 
## Installing the Signing Adapter Docker Image

### Prerequisites

1. Create directories for document storage

 ```bash
 $ sudo mkdir -p /root/logs
 ```
 ** Note: On production, these directories may be located in NFS storage or similar.
 
2. Create a directory for the project file on your home directory and change directory to the created directory

 ```bash
 $ cd $HOME
 $ mkdir -p verify-pdf
 $ cd verify-pdf
 ```
 
3. Create a docker-compose.yml configuration file to run the container using docker-compose

 ```bash
 $ touch docker-compose.yml
 ```
 edit using your favorite text editor

 ```bash
 $ nano docker-compose.yml
 ```
 write this configuration and save the file

 ```yaml
version: '3.1'
services:
 adapter:
  container_name: pdf-verificator
  image: registry.perurica.co.id/e-meterai/verify-pdf:latest
  restart: always
  privileged: true
  ports: 
   - "9055:7777"
  environment:
   TZ: Asia/Jakarta
   WORKER: 4
   TIMEOUT: 240
   GRACEFUL_TIMEOUT: 320
   KEEP_ALIVE: 30
  volumes:
   - /root/logs:/logs

 ```
4. To run the Docker container:

 Start the Docker container by running the following command with sudo:

 ```bash
 $ sudo docker compose up -d
 ```

 To verify that the container is running, use the following command:

 ```bash
 $ sudo docker ps
 ```

 The output should be similar to this:

 ```bash
 CONTAINER ID   IMAGE                                                      COMMAND                CREATED        STATUS                       PORTS                              NAMES
8ba281c25a23   registry.perurica.co.id/e-meterai/verify-pdf:latest     "/bin/app"             3 hours ago    Up About an hour             0.0.0.0:9055->7777/tcp             pdf-verificator
 ```
 
5. To access the documentation using a browser:
 
 Type the following URL into the address bar of your browser: http://vm-or-server-ip-address:9055. You should see a JSON message that says:

 ```json
 {
    message: "Welcome to PDF Verify 1.0.0-RC1",
    docUrl: "/documentation",
    redocUrl: "/redoc"
}
 ```

 To access the Swagger-UI interface, go to /documentation. To access the Redoc interface, go to /redoc.