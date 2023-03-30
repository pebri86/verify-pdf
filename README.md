# PERISAI SIGNADAPTER
Adapter service for hash sign ( perisai on premise service )

## How to build
### prerequisite
- install docker and docker-compose
- install python3 and python3-pip, example on ubuntu
```sh
# sudo apt update && sudo apt install python3 python3-pip
```
- install virtualenv and install dependencies
```sh
# pip3 install virtualenv
# python3 -m virtualenv venv
# source venv/bin/activate
# pip3 install -r requirements.txt
```

### test run locally
```sh
# cp .env.example .env
# source 
# make setup
# make dev
```

### build binary and docker image
- run make
```sh
# make base-image -> this only need run once
# make image
```

- confirm created image, there's should be image registry.perurica.co.id:443/keysign/signadapter with tag latest
```sh
# docker images
```

- run docker image and verify it's running
```sh
# cd docker-compose
# docker-compose up -d --scale stampadapter=3
# docker ps
```
