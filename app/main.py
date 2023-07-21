import aiohttp
import logging
import uuid
import time
import random
import string
from fastapi import FastAPI, Request, Response, status, UploadFile, security, Depends, File, Form, Header, Query
from fastapi.responses import JSONResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from typing import Union
from sign_pdf import signing_pdf
from signers import ExternalSignerError
from config import *
from errors import ErrCode
from base64 import b64encode
from hashlib import sha1
from os.path import join, exists
from mymodel import SigningRequest, SigningResponse, TokenRequest, UploadResponse, SessionInitRequest, SessionValidateRequest
from requests import post

# version string
VERSION = "0.0.8-b"

# setup loggers
logging.config.fileConfig(LOG_CONFIG, disable_existing_loggers=False)

# get root logger
logger = logging.getLogger('root')

description = """
Signing adapter for perisai hash signing

"""

tags_metadata = [
    {
        "name": "get token",
        "description": "Service for request JWT Token.",
    },
    {
        "name": "session initiate",
        "description": "Service for request session.",
    },
    {
        "name": "session validate",
        "description": "Service for validating session.",
    },
    {
        "name": "upload pdf",
        "description": "Service upload PDF document.",
    },
    {
        "name": "sign",
        "description": "Service operation for signing PDF document.",
    },
    {
        "name": "set specimen",
        "description": "Service to set default user specimen for digital signature.",
    },
    {
        "name": "get specimen",
        "description": "Service to get current saved user specimen.",
    },
    {
        "name": "download signed pdf",
        "description": "Service to get signed pdf document.",
    }
]

app = FastAPI(
    docs_url="/documentation",
    redoc_url="/redoc",
    title="Signing Adapter",
    description=description,
    version=VERSION,
    terms_of_service="https://peruri.co.id/about",
    contact={
        "name": "Perum Percetakan Uang Republik Indonesia",
        "url": "https://www.peruri.co.id/",
        "email": "cs.digital@peruri.co.id",
    },
    openapi_tags=tags_metadata
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

auth_scheme = security.HTTPBearer()

async def get_unique_from_str(string):
    hash_object = sha1(string)
    return hash_object.hexdigest()


@app.middleware("http")
async def catch_exceptions_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except ExternalSignerError as e:
        return JSONResponse({"status": "error", "errorCode": f"{e.code}", "message": f"[remote] internal server error: {e.msg}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        err_msg = ""
        if len(e.args) > 1:
            err_msg = e.args[1]
        else:
            err_msg = e.args[0]
        logger.error(f"exception: {e}")
        return JSONResponse({"status": "error", "errorCode": "99", "message": f"{ErrCode.ERR_99}: {err_msg}"}, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


@app.post("/v1/auth/token", status_code=200, tags=["get token"])
async def get_token(req: TokenRequest, response: Response, x_gateway_apikey: Union[str, None] = Header(default=None)):
    header = {
        "Content-Type": "application/json",
        "x-Gateway-APIKey": x_gateway_apikey
    }
    payloads = jsonable_encoder(req)

    r = post(url=TOKEN_URL, headers=header, json=payloads)
    if r.status_code == 200:
        resp = r.json()
        if resp["resultCode"] == "0":
            return JSONResponse({"status": "success", "errorCode": "0", "jwt": resp["data"]["jwt"]})
        else:
            logger.error(f"url: {TOKEN_URL}")
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
    
@app.post("/v1/auth/session/init", status_code=200, tags=["session initiate"])
async def get_token(request: Request, req: SessionInitRequest, response: Response, x_gateway_apikey: Union[str, None] = Header(default=None), token: security.HTTPBearer = Depends(auth_scheme)):
    header = {
        "Content-Type": "application/json",
        "x-Gateway-APIKey": x_gateway_apikey,
        "Authorization": f"Bearer {token.credentials}"
    }
    payloads = jsonable_encoder(req)

    r = post(url=SESSION_INIT_URL, headers=header, json=payloads)
    if r.status_code == 200:
        resp = r.json()
        if resp["resultCode"] == "0":
            return JSONResponse({"status": "success", "errorCode": "0", "tokenSession": resp["data"]["tokenSession"]})
        else:
            logger.error(f"url: {SESSION_INIT_URL}")
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
    
@app.post("/v1/auth/session/validate", status_code=200, tags=["session validate"])
async def get_token(request: Request, req: SessionValidateRequest, response: Response, x_gateway_apikey: Union[str, None] = Header(default=None), token: security.HTTPBearer = Depends(auth_scheme)):
    header = {
        "Content-Type": "application/json",
        "x-Gateway-APIKey": x_gateway_apikey,
        "Authorization": f"Bearer {token.credentials}"
    }
    payloads = jsonable_encoder(req)

    r = post(url=SESSION_VALIDATE_URL, headers=header, json=payloads)
    if r.status_code == 200:
        resp = r.json()
        if resp["resultCode"] == "0":
            return JSONResponse({"status": "success", "errorCode": "0", "tokenSession": resp["data"]["tokenSession"]})
        else:
            logger.error(f"url: {SESSION_VALIDATE_URL}")
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


@app.get("/v1/specimen/get", status_code=200, response_model=UploadResponse, tags=['get specimen'])
async def get_specimen(request: Request, response: Response, profile_name: str = Query(alias="profileName")):
    profile = await get_unique_from_str(bytes(profile_name, 'utf-8'))
    filename = f"{profile}.png"
    path = join(SPC_FOLDER, filename)
    if exists(path):
        with open(path, "rb") as f:
            encoded_string = b64encode(f.read()).decode('utf-8')
            f.close()
            return JSONResponse({"status": "success", "errorCode": "0", "result": {"fileName": filename, "base64": f"{encoded_string}"}})
    else:
        JSONResponse({"status": "error", "errorCode": "84",
                     "message": f"{ErrCode.ERR_84}"})


@app.post("/v1/specimen/set", status_code=201, response_model=UploadResponse, tags=['set specimen'])
async def set_specimen(request: Request, response: Response, profile_name=Form(alias="profileName"), file: UploadFile = File(None)):
    try:
        contents = file.file.read()
        profile = await get_unique_from_str(bytes(profile_name, 'utf-8'))
        file_id = f"{profile}.png"
        with open(join(SPC_FOLDER, file_id), "wb") as f:
            f.write(contents)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return UploadResponse(status="error", error_code="81", message=f"{ErrCode.ERR_81}: {e.args}")
    finally:
        file.file.close

    return UploadResponse(status="success", error_code="0", message=f"set specimen success", file_id=f"{profile}", original_name=file.filename, save_as=f"{file_id}")


@app.post("/v1/doc/upload", status_code=201, response_model=UploadResponse, tags=['upload pdf'])
async def upload(request: Request, response: Response, file: UploadFile = File(None)):
    try:
        contents = file.file.read()
        file_id = uuid.uuid4()
        with open(f"{UNSIGNED_FOLDER}/{file_id}.pdf", "wb") as f:
            f.write(contents)
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return UploadResponse(status="error", error_code="81", message=f"{ErrCode.ERR_81}: {e.args}")
    finally:
        file.file.close

    return UploadResponse(status="success", error_code="0", message=f"upload file success", file_id=f"{file_id}", original_name=file.filename, save_as=f"{file_id}.pdf")


@app.get("/v1/doc/download", status_code=200, tags=['download signed pdf'])
async def download(request: Request, response: Response, id_file: str = Query(alias="idFile")):
    file_name = f"signed_{id_file}.pdf"
    file_path = join(SIGNED_FOLDER, file_name)
    if exists(file_path):
        return FileResponse(path=file_path, status_code=200, filename=file_name, media_type="application/pdf")

    response.status_code = status.HTTP_404_NOT_FOUND
    return UploadResponse(status="error", error_code="85", message=f"{ErrCode.ERR_85}", file_id=id_file)

@app.post("/v1/doc/sign", status_code=201, response_model=SigningResponse, tags=['sign'])
async def sign_pdf(request: Request, req: SigningRequest, response: Response, x_gateway_apikey: Union[str, None] = Header(default=None), token: security.HTTPBearer = Depends(auth_scheme)):
    async with aiohttp.ClientSession() as session:
        result = await signing_pdf(req, session, response, jwtoken=token.credentials, key_id=x_gateway_apikey)

        return result

application = app
