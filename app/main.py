import logging
import random
import time
import string
from fastapi import FastAPI, Request, Response, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.diff_analysis import DEFAULT_DIFF_POLICY
from config import *
from errors import *

# setup loggers
logging.config.fileConfig(LOG_CONFIG, disable_existing_loggers=False)

# get root logger
logger = logging.getLogger('root')

description = """
Verify PDF Signatures service

"""

app = FastAPI(
    docs_url="/documentation",
    redoc_url="/redoc",
    title=APP_NAME,
    description=description,
    version=VERSION,
    terms_of_service="https://peruri.co.id/about",
    contact={
        "name": "Perum Percetakan Uang Republik Indonesia",
        "url": "https://www.peruri.co.id/",
        "email": "cs.digital@peruri.co.id",
    },
)

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        err_msg = ""
        if len(e.args) > 1:
            err_msg = e.args[1]
        else:
            err_msg = e.args[0]
        logger.error(f"exception: {e}")
        return JSONResponse({"resultCode": "error", "errorCode": "99", "message": f"{ErrCode.ERR_99}: {err_msg}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"request_id={idem} start request path={request.url.path}")
    start_time = time.time()

    response = await call_next(request)

    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(
        f"request_id={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")

    return response


@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to Signing Adapter {VERSION}", "docUrl": "/documentation", "redocUrl": "/redoc"}

@app.post("/gateway/digitalSignatureValidation/1.0/signatureVerification/v2", status_code=200, tags=['upload pdf'])
async def upload(request: Request, response: Response, file: UploadFile = File(None)):
    try:
        reader = PdfFileReader(file.file, strict=False)
        is_meterai = False
        is_tempered = False
        signer = []
        totalsignature = len(reader.embedded_signatures)
        if totalsignature > 0:
            for signature in reader.embedded_signatures:
                if "Meterai Elektronik" in signature.signer_cert.subject.human_friendly:
                    is_meterai = True
                integrity = True
                if not integrity:
                    is_tempered = True
                certificateInfo = []
                for issuer in signature.other_embedded_certs:
                    certInfo = {
                        "issuer": issuer.issuer.human_friendly,
                        "serialNumber": f"{issuer.serial_number}",
                        "subjectDn": issuer.subject.human_friendly,
                        "notValidAfter": issuer.not_valid_after.strftime("%Y-%m-%d %H:%M:%S"),
                        "notValidBefore": issuer.not_valid_before.strftime("%Y-%m-%d %H:%M:%S"),
                        "algorithm": issuer.hash_algo
                    }
                    certificateInfo.append(certInfo)
                sig = {
                    "issuer": signature.signer_cert.issuer.human_friendly,
                    "issuerInfos": {
                        "certificateInfo": certificateInfo
                    },
                    "serialNumber": f"{signature.signer_cert.serial_number}",
                    "signDate": signature.self_reported_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    #"integrity": integrity,
                    "signatureAlgorithm": signature.md_algorithm,
                    "signatureField": signature.field_name,
                    "subjectDn": signature.signer_cert.subject.human_friendly,
                    "notValidAfter": signature.signer_cert.not_valid_after.strftime("%Y-%m-%d %H:%M:%S"),
                    "notValidBefore": signature.signer_cert.not_valid_before.strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": signature.sig_object.get("/Reason"),
                    "algorithm": signature.signer_cert.hash_algo,
                    "location": signature.sig_object.get("/Location"),
                }
                signer.append(sig)
        
        res = {
            "resultCode": "0",
            "resultDesc": "Success",
            "data": {
                "totalSignature": totalsignature,
                "isMeterai": is_meterai,
                #"isTampered": is_tempered,
                "signer": signer
            }
        }
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.error(e.args)
        return JSONResponse({"resultCode": "03", "resultDesc": f"Error Verification | {e.args[0]}"})
    finally:
        file.file.close

    return JSONResponse(jsonable_encoder(res))

application = app
