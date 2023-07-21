from pydantic import BaseModel
from typing import Optional

def to_camel(string):
    init, *temp = string.split('_')
    res = ''.join([init.lower(), *map(str.title, temp)])

    return res

class MyModel(BaseModel):
    class Config:
        alias_generator = to_camel
        allow_population_by_field_name = True
        
class ParamTokenRequest(MyModel):
    system_id: str

class TokenRequest(MyModel):
    param: ParamTokenRequest
    
class ParamSessionInitRequest(MyModel):
    email: str
    system_id: str
    send_sms: str = "0"
    send_email: str = "1"
    
class SessionInitRequest(MyModel):
    param: ParamSessionInitRequest
    
class ParamSessionValidateRequest(MyModel):
    email: str
    system_id: str
    token_session: str
    otp_code: str
    
class SessionValidateRequest(MyModel):
    param: ParamSessionValidateRequest
    
class Coordinate(MyModel):
    page: Optional[int] = 1
    llx: Optional[float] = 0
    lly: Optional[float] = 0
    urx: Optional[float] = 0
    ury: Optional[float] = 0
    
class SigningCoordinate(Coordinate):
    is_base64: Optional[bool] = False
    specimen_image: Optional[str] = ""
    specimen_qr_data: Optional[str] = ""
    specimen_text_data: Optional[str] = ""    

class SigningRequest(MyModel):
    system_id: str = "SYSTEM-ID"
    profile_name: str = "name@example.com"
    src: str = "daca074c-e113-46b0-8fca-8b2e608f6f18.pdf"
    doc_pass: str = "document password"
    location: str = "Jakarta"
    reason: str = "I agree to sign"
    coordinate: Optional[SigningCoordinate]

class SigningResponse(MyModel):
    status: str
    error_code: str
    message: str = None

class UploadResponse(SigningResponse):
    file_id: str = None
    original_name: str = None
    save_as: str = None