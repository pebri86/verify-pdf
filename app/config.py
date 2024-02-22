import os

# SET ENV dev or production
ENV = os.getenv("ENV", "production")
WORKER = os.getenv("WORKER", 10)
TIMEOUT = os.getenv("TIMEOUT", 240)
GRACEFUL_TIMEOUT = os.getenv("GRACEFUL_TIMEOUT", 240)
KEEP_ALIVE = os.getenv("KEEP_ALIVE", 20)

# Internal configs
LOG_CONFIG = os.getenv("LOG_CONFIG", "/conf/logging.conf")

# Application Name
APP_NAME = "Verify PDF Signature"
# Application Version String
VERSION = "1.0.0"