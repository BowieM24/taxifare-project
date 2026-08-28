from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class ErrorDetail(BaseModel):
    """
    Standard Electrum error shema for HTTP 400 and 500 responses.
    """
    schema_: str = Field("ErrorDetail", alias="schema")
    message: str
    detail: Optional[str] = None

class StatusReasonInfo(BaseModel):
    """
    Carries specific banking failure codes (e.g., AM04 Insufficient Funds, AC06 Blocked Account).
    """
    reason : Optional[Dict[str, Any]] = None
    additionalInformation: Optional[str] = None

class TranInfo(BaseModel):
    tranUetr: Optional[str] = None
    direction: Optional[str] = None
    paymentScheme: Optional[str] = None 
    service: Optional[str] = None

class MessageInfo(BaseModel):
    messageIdentification: Optional[str] = None
    creationDateTime: Optional[str] = None
    httpStatusCode: Optional[int] = None

class ElectrumEventPayload(BaseModel):
    name: Optional[str] = None
    apiVersion: str
    event_class: Optional[str] = Field(None, alias="class")
    type: Optional[str] = None
    stageVersion: Optional[int] = None
    tranInfo: Optional[TranInfo] = None
    messageInfo: Optional[MessageInfo] = None
    payload: Optional[Dict[str, Any]] = None
    