all: clean setup base-image image
setup: requirements.txt
	mkdir -p logs
	pip3 install -r requirements.txt
dev:
	ENV=dev python3 app/server.py
prod:
	ENV=production python3 app/server.py
image:
	docker build -t pebri86/verify-pdf:latest .
base-image:
	docker build -t pyinstaller-signadapter:3.9-slim base-installer-image
clean:
	rm -rf build
	rm -rf dist
	rm -rf app/__pycache__
	rm -f server.spec
