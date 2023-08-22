import os

# SET ENV dev or production
ENV = os.getenv("ENV", "production")

# Environment configurable configs
TOKEN_URL = os.getenv(
    "TOKEN_URL", "https://apg.peruri.co.id:9044/gateway/jwtSandbox/1.0/getJsonWebToken/v1")
SESSION_INIT_URL = os.getenv(
    "SESSION_INIT_URL", "https://apg.peruri.co.id:9044/gateway/digitalSignatureOnPremise/1.0/sessionInitiate/v1")
SESSION_VALIDATE_URL = os.getenv(
    "SESSION_VALIDATE_URL", "https://apg.peruri.co.id:9044/gateway/digitalSignatureOnPremise/1.0/sessionValidation/v1")
HASH_URL = os.getenv(
    "HASH_URL", "https://apg.peruri.co.id:9044/gateway/digitalSignatureOnPremise/1.0/signingHash/v1")
CERTIFICATE_CHAIN_URL = os.getenv(
    "CERTIFICATE_CHAIN_URL", "https://apg.peruri.co.id:9044/gateway/digitalSignatureOnPremise/1.0/getCertificateChain/v1")
TSA_URL = os.getenv(
    "TSA_URL", "http://timestamp.peruri.co.id/signserver/tsa?workerName=TimeStampSigner1101")
KEY_ID = os.getenv("KEY_ID", "6d7a673f-ec98-40cf-a1a1-dc9966992c78")
WORKER = os.getenv("WORKER", 10)
TIMEOUT = os.getenv("TIMEOUT", 240)
GRACEFUL_TIMEOUT = os.getenv("GRACEFUL_TIMEOUT", 240)
KEEP_ALIVE = os.getenv("KEEP_ALIVE", 20)
UNSIGNED_FOLDER = os.getenv("UNSIGNED_FOLDER", "/sharefolder/UNSIGNED")
SIGNED_FOLDER = os.getenv("SIGNED_FOLDER", "/sharefolder/SIGNED")
SPC_FOLDER = os.getenv("SPC_FOLDER", "/sharefolder/SPECIMEN")
KEYSTORE = os.getenv("KEYSTORE", "/certs")

# Internal configs
LOG_CONFIG = os.getenv("LOG_CONFIG", "/conf/logging.conf")
RESOURCES_DIR = os.getenv("RESOURCES_DIR", "/sharefolder/")

# Application Name
APP_NAME = "Perisai SignAdapter"
# Application Version String
VERSION = "0.0.8-b"