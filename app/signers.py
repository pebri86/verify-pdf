import logging
from pyhanko_certvalidator.registry import SimpleCertificateStore
from asn1crypto import x509, algos
from pyhanko.sign import Signer
from base64 import b64decode, b64encode
from requests import post
from config import *

# setup loggers
logging.config.fileConfig(LOG_CONFIG, disable_existing_loggers=False)

# get root logger
logger = logging.getLogger(__name__)

class ExternalSignerError(Exception):
    def __init__(self, code: str, msg: str) -> None:
        self.code = code
        self.msg = msg.lower()
        super().__init__(self.code, self.msg)

class ExternalSigner(Signer):
    def __init__(self,
                 signing_url: str,
                 profile_name: str,
                 system_id: str,
                 hash_algorithm: algos.SignedDigestAlgorithm,
                 jwtoken: str,
                 key_id: str,
                 signing_cert: x509.Certificate,                 
                 terra: bool,
                 other_certs=(),
                 ):
        self.signing_url = signing_url
        self.profile_name = profile_name
        self.system_id = system_id
        self.signature_mechanism = hash_algorithm
        self.jwtoken = jwtoken
        self.key_id = key_id
        self.signing_cert = signing_cert
        self.cert_registry = cr = SimpleCertificateStore()
        self.terra = terra
        cr.register_multiple(other_certs)
        super().__init__()

    async def async_sign_raw(self, data: bytes, digest_algorithm: str, dry_run=False) -> bytes:
        if dry_run:
            return bytes(256)

        # Request to signing server
        header = {
            "Content-Type": "application/json",
            "x-Gateway-APIKey": self.key_id,
            "Authorization": "Bearer {}".format(self.jwtoken)
        }
        signing_type = "SIGNING"
        if self.terra:
            signing_type = "TERRA"
        payloads = {
            "requestSigning": {
                "data": str(b64encode(data), 'UTF-8'),
                "email": self.profile_name,
                "systemId": self.system_id,
                "type": signing_type
            }
        }

        r = post(url=self.signing_url, headers=header, json=payloads)
        if r.status_code == 200:
            resp = r.json()
            if resp["resultCode"] == "0":
                logger.info(f"success with orderId = {resp['data']['orderId']}")
                signature = b64decode(resp["data"]["signedHash"] + '==')
                assert isinstance(signature, bytes)

                return signature
            else:
                logger.error(f"url: {self.signing_url}")
                logger.error(f"payloads: {payloads}")
                logger.error(f"response: {resp}")
                raise ExternalSignerError(
                    code=resp["resultCode"], msg=resp["resultDesc"])
        elif r.status_code == 503:
            logger.error(f'HTTP requests error with code {r.status_code}')
            logger.error(f'URL {r.url}')
            raise ExternalSignerError(
                code=r.status_code, msg="service unavailable")
        elif r.status_code == 504:
            logger.error(f'HTTP requests error with code {r.status_code}')
            logger.error(f'URL {r.url}')
            raise ExternalSignerError(
                code=r.status_code, msg="gateway timed out")
        else:
            logger.error(f'HTTP requests error with code {r.status_code}')
            logger.error(f'URL {r.url}')
            raise ExternalSignerError(code=r.status_code, msg=r.reason)

async def get_certificate_chain(url: str, profile_name: str, system_id: str, key_id: str, jwtoken: str):
    header = {
        "Content-Type": "application/json",
        "x-Gateway-APIKey": key_id,
        "Authorization": "Bearer {}".format(jwtoken)
    }
    payloads = {
        "email": profile_name,
        "systemId": system_id
    }

    r = post(url=url, headers=header, json=payloads)
    if r.status_code == 200:
        resp = r.json()
        if resp["resultCode"] == "0":
            certs = []
            try:
                for cer in resp["data"]["signerCertChain"]:
                    der_bytes = b64decode(cer + "==")
                    certs.append(x509.Certificate.load(der_bytes))
            except Exception as e:
                raise ExternalSignerError(code=r.status_code, msg=f"exception while process certificate chain: {e.args}")

            return certs
        else:
            logger.error(f"url: {url}")
            logger.error(f"payloads: {payloads}")
            logger.error(f"response: {resp}")
            raise ExternalSignerError(
                code=int(resp["resultCode"]), msg=resp["resultDesc"])

    elif r.status_code == 503:
        logger.error(f'HTTP requests error with code {r.status_code}')
        logger.error(f'URL {r.url}')
        raise ExternalSignerError(
            code=r.status_code, msg="service unavailable")
    elif r.status_code == 504:
        logger.error(f'HTTP requests error with code {r.status_code}')
        logger.error(f'URL {r.url}')
        raise ExternalSignerError(
            code=r.status_code, msg="gateway timed out")
    else:
        logger.error(f'HTTP requests error with code {r.status_code}')
        logger.error(f'URL {r.url}')
        raise ExternalSignerError(code=r.status_code, msg=r.reason)
