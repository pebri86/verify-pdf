all: clean setup base-image image
setup: requirements.txt
	mkdir -p sharefolder
	mkdir -p sharefolder/UNSIGNED
	mkdir -p sharefolder/SIGNED
	mkdir -p sharefolder/SPECIMEN
	mkdir -p logs
	pip3 install -r requirements.txt
dev:
	ENV=dev python3 app/server.py
prod:
	ENV=production python3 app/server.py
image:
	docker build -t registry.perurica.co.id:443/keysign/signadapter:latest .
base-image:
	docker build -t pyinstaller-signadapter:3.9-slim base-installer-image
clean:
	rm -rf build
	rm -rf dist
	rm -rf app/__pycache__
	rm server.spec
