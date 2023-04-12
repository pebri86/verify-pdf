from enum import Enum

class ErrCode(str, Enum):
    ERR_81 = "there is an error while processing file"
    ERR_82 = "source pdf file not found"
    ERR_83 = "cannot decrypt file with owner password"
    ERR_84 = "specimen image file not found"
    ERR_85 = "signed pdf file not found"
    ERR_99 = "internal server error"