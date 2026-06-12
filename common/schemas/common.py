from pydantic import BaseModel, ConfigDict
from typing import Any

class BaseRequestModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class BaseResponseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
