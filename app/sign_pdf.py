import logging
import time
from fastapi import Response, status
from asn1crypto import algos, x509
from pyhanko_certvalidator import ValidationContext
from pyhanko.sign.timestamps.aiohttp_client import AIOHttpTimeStamper
from pyhanko_certvalidator.fetchers.aiohttp_fetchers import AIOHttpFetcherBackend
from pyhanko.pdf_utils.crypt import AuthStatus
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers, fields
from pyhanko.sign.fields import SigSeedSubFilter, MDPPerm
from pyhanko.sign.general import load_cert_from_pemder
from pyhanko import stamp
from pyhanko.pdf_utils import images
from pyhanko.pdf_utils.layout import SimpleBoxLayoutRule, AxisAlignment, InnerScaling, Margins
from io import BytesIO
from PIL import Image
from base64 import b64decode, b64encode
from typing import Optional
from os.path import join
from mymodel import MyModel
from config import *
from errors import ErrCode
from signers import ExternalSigner, get_certificate_chain

# setup loggers
logging.config.fileConfig(LOG_CONFIG, disable_existing_loggers=False)

# get root logger
logger = logging.getLogger('signing')


class Coordinate(MyModel):
    specimen_image: Optional[str] = "base64 string image specimen or filename"
    specimen_qr_data: Optional[str] = "string text to be encoded as QR code"
    specimen_text_data: Optional[str] = "string text to be set as appearance of signature"
    page: Optional[int] = 1
    llx: Optional[float] = 0
    lly: Optional[float] = 0
    urx: Optional[float] = 0
    ury: Optional[float] = 0


class SigningRequest(MyModel):
    system_id: str = "SYSTEM-ID"
    profile_name: str = "name@example.com"
    src: str = "daca074c-e113-46b0-8fca-8b2e608f6f18.pdf"
    doc_pass: str = "document password"
    location: str = "Jakarta"
    reason: str = "I agree to sign"
    coordinate: Optional[Coordinate]


class SigningResponse(MyModel):
    status: str
    error_code: str
    message: str = None


async def check_source(filePath):
    return os.path.exists(filePath)


async def is_base64(string):
    try:
        return b64encode(b64decode(string+'==')) == string
    except Exception:
        return False


async def signing_pdf(req: SigningRequest, session, response: Response, jwtoken: str, key_id: str):
    in_filename = join(UNSIGNED_FOLDER, req.src)
    if not await check_source(in_filename):
        response.status_code = status.HTTP_404_NOT_FOUND
        ret = SigningResponse(status="error", error_code="82",
                              message=f"{ErrCode.ERR_82}")
        logger.error(ret)
        logger.error(req)

        return ret

    # get certificate chain
    certs = await get_certificate_chain(url=CERTIFICATE_CHAIN_URL,
                                        profile_name=req.profile_name,
                                        system_id=req.system_id,
                                        key_id=key_id,
                                        jwtoken=jwtoken
                                        )

    signer = ExternalSigner(
        signing_url=HASH_URL,
        profile_name=req.profile_name,
        system_id=req.system_id,
        hash_algorithm=algos.SignedDigestAlgorithm(
            {"algorithm": "sha256_rsa"}),
        jwtoken=jwtoken,
        key_id=key_id,
        signing_cert=certs[0],
        other_certs=certs
    )

    tsa_root = []
    for cer in os.listdir(join(KEYSTORE)):
        in_cer = load_cert_from_pemder(join(KEYSTORE, cer))
        tsa_root.append(in_cer)

    validation_context = ValidationContext(
        trust_roots=certs,
        extra_trust_roots=tsa_root,
        fetcher_backend=AIOHttpFetcherBackend(session),
        allow_fetching=True
    )

    timestamper = AIOHttpTimeStamper(
        TSA_URL,
        session=session
    )

    with open(in_filename, 'rb') as inf:
        reader = PdfFileReader(inf, strict=False)
        if reader.encrypted:
            d = reader.decrypt(req.doc_pass)
            if d.status == AuthStatus.FAILED:
                response.status_code = status.HTTP_403_FORBIDDEN
                ret = SigningResponse(
                    status="error", errorCode="83", message=ErrCode.ERR_83)
                logger.error(req)
                logger.error(ret)
                return ret

        sigName = f'sig{int(time.time())}'
        w = IncrementalPdfFileWriter(inf).from_reader(reader=reader)
        box = (0, 0, 0, 0)
        page = 0
        style = None
        stamp_text = None
        qr_data = None
        background = None
        image_data = None
        if req.coordinate:
            stamp_text = req.coordinate.specimen_text_data
            qr_data = req.coordinate.specimen_qr_data
            image_data = req.coordinate.specimen_image
            page = req.coordinate.page-1
            box = (
                req.coordinate.llx,
                req.coordinate.lly,
                req.coordinate.urx,
                req.coordinate.ury
            )
        fields.append_signature_field(
            w, sig_field_spec=fields.SigFieldSpec(
                sigName,
                on_page=page,
                box=box
            )
        )
        permission = MDPPerm.FILL_FORMS
        certify = False

        meta = signers.PdfSignatureMetadata(
            field_name=sigName,
            reason=req.reason,
            location=req.location,
            subfilter=SigSeedSubFilter.PADES,
            validation_context=validation_context,
            embed_validation_info=True,
            docmdp_permissions=permission,
            certify=certify
        )

        background_layout = SimpleBoxLayoutRule(
            x_align=AxisAlignment.ALIGN_MID,
            y_align=AxisAlignment.ALIGN_MID,
            margins=Margins(0, 0, 0, 0),
            inner_content_scaling=InnerScaling.STRETCH_TO_FIT
        )

        if image_data != None and image_data != "":
            if await is_base64(image_data):
                background = images.PdfImage(Image.open(
                    BytesIO(b64decode(image_data))),
                    opacity=40)
            else:
                image_file = join(SPC_FOLDER, image_data)
                if await check_source(image_file):
                    background = images.PdfImage(
                        Image.open(image_file),
                        opacity=40)
                else:
                    ret = SigningResponse(status="error", error_code="84",
                                          message=f"{ErrCode.ERR_84}")

                    return ret

        if qr_data != None and qr_data != "":
            style = stamp.QRStampStyle(
                border_width=0,
                stamp_text=stamp_text,
                background=background,
                background_layout=background_layout,
                background_opacity=0.4,
                inner_content_layout=SimpleBoxLayoutRule(
                    x_align=AxisAlignment.ALIGN_MIN,
                    y_align=AxisAlignment.ALIGN_MID,
                    inner_content_scaling=InnerScaling.STRETCH_TO_FIT,
                    margins=Margins(0, 0, 0, 0)
                )
            )
        else:
            style = stamp.TextStampStyle(
                border_width=0,
                stamp_text=stamp_text,
                background_layout=background_layout,
                background=background,
                background_opacity=0.4
            )

        pdf_signer = signers.PdfSigner(
            meta,
            signer=signer,
            timestamper=timestamper,
            stamp_style=style
        )

        out_filename = f"signed_{req.src}"
        with open(join(SIGNED_FOLDER, out_filename), 'wb') as outf:
            await pdf_signer.async_sign_pdf(w, output=outf, appearance_text_params={'url': qr_data})

        return SigningResponse(status="success", errorCode="0", message=f"signing success, filename: {out_filename}")
