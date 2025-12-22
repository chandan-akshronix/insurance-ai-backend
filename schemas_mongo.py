from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any, Union
from datetime import datetime


class Rider(BaseModel):
    rider_id: str
    rider_name: str
    rider_cost: float


class LifeInsuranceApplication(BaseModel):
    # Accept either `user_id` or camelCase `userId` from frontend and allow string|int
    user_id: Optional[Union[str, int]] = Field(None, alias='userId')
    status: Optional[str] = 'draft'
    personal_details: Optional[dict] = None
    contact_info: Optional[dict] = None
    documents: Optional[List[dict]] = Field(default_factory=list)
    ai_extraction: Optional[dict] = None
    coverage_selection: Optional[dict] = None
    riders: Optional[List[Rider]] = Field(default_factory=list)
    compare_plans: Optional[List[dict]] = Field(default_factory=list)
    health_info: Optional[dict] = None
    nominee_details: Optional[dict] = None
    kyc_verification: Optional[dict] = None
    payment: Optional[dict] = None
    # store related SQL policy id (created in the FastAPI policy table)
    policy: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True
        # allow population by field name when aliases are used and accept alias population
        allow_population_by_field_name = True
        allow_population_by_alias = True
        # accept unknown extra fields from frontend (camelCase keys, etc.) to avoid 422
        extra = 'allow'
        json_encoders = {datetime: lambda v: v.isoformat()}
