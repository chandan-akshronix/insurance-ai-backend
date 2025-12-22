# schemas.py
from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import date
from enum import Enum


# ---------- ENUMS ----------
class PolicyType(str, Enum):
    vehicle = "vehicle_insurance"
    health = "health_insurance"

class ContactCategory(str, Enum):
    general = "general_enquiry"
    claim = "claim_support"
    policy = "policy_information"
    technical = "technical_support"
    complaint = "complaint"

class Addons(str, Enum):
    critical_illness = "critical_illness_cover"
    accidental_death = "accidental_death_cover"
    waiver_of_premium = "waiver_of_premium"

class PersonalDetails(BaseModel):
    name: str
    dateOfBirth: date
    gender: Literal["male", "female", "other"] 

class ActivityTypes(str, Enum):
    payment = "payment"
    policy = "policy"
    claim = "claim"
    health = "health"

class KycStatus(str, Enum):
    pending = "pending"
    verified = "verified"

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

class NotificationTypes(str, Enum):
    warning = "warning"
    success = "success"
    info = "info"
    error = "error"

class PaymentStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    cancelled = "cancelled"

# ---------- USERS ----------
class UserBase(BaseModel):
    name: str
    email: str
    phone: str
    address: str
    dateOfBirth: date
    gender: str
    panCard: str
    aadhar: str
    kycStatus: KycStatus
    role: UserRole = UserRole.user  # Default role is user
    profileImage: Optional[str] = None
    occupation: Optional[str] = None
    annualIncome: Optional[str] = None

class UserCreate(UserBase):
    password: str  # Plain password - will be hashed before storing
    joinedDate: Optional[date] = None  # Optional - will be auto-set if not provided
    role: Optional[UserRole] = None  # Optional - defaults to 'user' if not provided

class User(UserBase):
    userId: int
    joinedDate: date  # Add back for response
    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    occupation: Optional[str] = None
    annualIncome: Optional[str] = None


# ---------- POLICY ----------
class PolicyBase(BaseModel):
    policyNumber: str
    type: PolicyType
    planName: str           
    coverage: float
    premium: float
    tenure: int
    startDate: date
    expiryDate: date
    benefits: List[Addons]
    nominee: str
    nomineeId: int
    personalDetails: PersonalDetails
    policyDocument: str
   


class PolicyCreate(PolicyBase):
    userId: int

class Policy(PolicyBase):
    policyId: int
    userId: Optional[int] = None
    model_config = {"from_attributes": True}

class PolicyUpdate(BaseModel):

    type: Optional[PolicyType] = None
    benefits: Optional[List[Addons]] = None
    planName: Optional[str] = None
    coverage: Optional[float] = None
    premium: Optional[float] = None
    status: Optional[str] = None
    startDate: Optional[date] = None
    expiryDate: Optional[date] = None
    nominee: Optional[str] = None
    nomineeId: Optional[int] = None
    policyDocument: Optional[str] = None

# ---------- CLAIMS --------------------------------------------------------------------------
class ClaimBase(BaseModel):
    userId: int
    policyId: int
    claimType: str
    amount: float
    status: str

class ClaimCreate(ClaimBase):
    pass

class Claim(ClaimBase):
    claimId: int
    model_config = {"from_attributes": True}

class ClaimUpdate(BaseModel):
    claimType: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None

# ---------- PRODUCT ----------------------------------------------------------------------------
class ProductBase(BaseModel):
    category: PolicyType
    name: str
    description: str
    price: float

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    productId: int
    model_config = {"from_attributes": True}

class ProductUpdate(BaseModel):
    category: Optional[PolicyType] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

# ---------- CONTACT ----------------------------------------------------------------------------
class ContactBase(BaseModel):
    fullName: str
    phone: str
    email: str
    category: ContactCategory
    message: str

class ContactCreate(ContactBase):
    pass

class Contact(ContactBase):
    contactId: int
    model_config = {"from_attributes": True}

class ContactUpdate(BaseModel):
    fullName: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    category: Optional[ContactCategory] = None
    message: Optional[str] = None

# ---------- QUOTATION ----------------------------------------------------------------------------
class QuotationBase(BaseModel):
    category: PolicyType
    fullName: str
    email: str
    phone: str

class QuotationCreate(QuotationBase):
    pass

class Quotation(QuotationBase):
    quotationId: int
    model_config = {"from_attributes": True}

class QuotationUpdate(BaseModel):
    category: Optional[PolicyType] = None
    fullName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None


# ---------- DOCUMENTS ------------------------------------------------------------------------------------
class DocumentBase(BaseModel):  
    userId: int
    policyId: Optional[int] = None
    documentType: str
    documentUrl: str
    uploadDate: date
    fileSize: float

class DocumentCreate(DocumentBase):
    pass    

class Document(DocumentBase):
    documentId: int
    model_config = {"from_attributes": True}

class DocumentUpdate(BaseModel):
    documentType: Optional[str] = None
    documentUrl: Optional[str] = None

# ---------- NOMINEE ----------------------------------------------------------------------------
class NomineeBase(BaseModel):
    userId: int
    policyId: int
    name: str
    relationship: str
    phone: str
    email: str

class NomineeCreate(NomineeBase):
    pass

class Nominee(NomineeBase):
    nomineeId: int
    model_config = {"from_attributes": True}

class NomineeUpdate(BaseModel):
    name: Optional[str] = None
    relationship: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


# Policy purchase request schema
class PolicyPurchaseCreate(BaseModel):
    userId: int
    type: PolicyType
    planName: str
    coverage: float
    premium: float
    tenure: int
    nominee: Optional[str] = None
    nomineeId: Optional[int] = None
    personalDetails: Optional[PersonalDetails] = None
    policyNumber: str


# ---------- ACTIVITIES --------------------------------------------------------------------------

class ActivitiesBase(BaseModel):
    userId: int
    type: ActivityTypes
    description: str
    time: date
    amount: float

class ActivityCreate(ActivitiesBase):
    pass        

class Activity(ActivitiesBase):
    activityId: int
    model_config = {"from_attributes": True}

# ---------- NOTIFICATIONS --------------------------------------------------------------------------
class NotificationBase(BaseModel):
    message: str
    time: date
    type: NotificationTypes
    read: bool = False
    policyId: Optional[int] = None

class NotificationCreate(NotificationBase):
    userId: int    

class Notification(NotificationBase):
    notificationId: int
    userId: Optional[int] = None
    model_config = {"from_attributes": True}


#---------- PAYMENTS --------------------------------------------------------------------------

class PaymentBase(BaseModel):
    userId: int
    policyId: int
    amount: float
    orderId: str
    paidDate: date
    paymentMethod: str
    status: PaymentStatus = PaymentStatus.pending
    transactionId: str
    returnUrl: str
    paymentUrl: str

class PaymentCreate(PaymentBase):
    pass        

class Payment(PaymentBase):
    paymentId: int
    model_config = {"from_attributes": True}


# ---------- APPLICATION PROCESS ------------------------------------------------------------------

class ApplicationProcessBase(BaseModel):
    applicationId: str
    status: str
    currentStep: str
    assignedTo: Optional[str] = None


class ApplicationProcessCreate(ApplicationProcessBase):
    customerId: Optional[int] = None
    startTime: date
    agentData: Optional[dict] = None
    stepHistory: Optional[List[dict]] = None
    auditTrail: Optional[List[dict]] = None


class ApplicationProcessUpdate(BaseModel):
    status: Optional[str] = None
    currentStep: Optional[str] = None
    agentData: Optional[dict] = None
    stepHistory: Optional[List[dict]] = None
    auditTrail: Optional[List[dict]] = None
    reviewReason: Optional[str] = None
    assignedTo: Optional[str] = None
    lastUpdated: Optional[date] = None


class ApplicationProcess(ApplicationProcessBase):
    id: int
    agentData: Optional[dict] = None
    stepHistory: Optional[List[dict]] = None
    auditTrail: Optional[List[dict]] = None
    reviewReason: Optional[str] = None
    startTime: date
    lastUpdated: Optional[date] = None
    customerId: Optional[int] = None

    model_config = {"from_attributes": True}
