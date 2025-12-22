from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON
from database import Base

from enum import Enum  # Python's Enum base class

# ---------------------- ENUM DEFINITIONS ----------------------

class PolicyType(str, Enum):
    life = "life_insurance"
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

class KycStatus(str, Enum):
    pending = "pending"
    verified = "verified"

class ActivityTypes(str, Enum):
    payment = "payment"
    policy = "policy"
    claim = "claim"
    health = "health"

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

class UserRole(str, Enum):
    user = "user"
    admin = "admin"

# ---------------------- MODELS ----------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, nullable=True)
    password = Column(String, nullable=False)  # Hashed password
    phone = Column(String, nullable=True)
    address = Column(String)
    dateOfBirth = Column(Date)
    gender = Column(String)
    panCard = Column(String, nullable=True)
    aadhar = Column(String, nullable=True)
    joinedDate = Column(Date)
    kycStatus = Column(SqlEnum(KycStatus), default=KycStatus.pending)
    role = Column(SqlEnum(UserRole), default=UserRole.user)  # User role: user or admin
    profileImage = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    annualIncome = Column('annualincome', String, nullable=True)
    # Relationships
    policies = relationship("Policy", back_populates="user")
    policy_purchases = relationship("PolicyPurchase", back_populates="user")
    claims = relationship("Claim", back_populates="user")
    documents = relationship("Documents", back_populates="user")
    nominees = relationship("Nominee", back_populates="user")
    activities = relationship("Activities", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    payments = relationship("Payments", back_populates="user")


class Policy(Base):
    __tablename__ = "policy"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(SqlEnum(PolicyType))
    planName = Column(String)
    policyNumber = Column(String, unique=True, index=True)
    coverage = Column(Float)
    premium = Column(Float)
    status = Column(String)
    startDate = Column(Date)
    expiryDate = Column(Date)
    benefits = Column(JSON, nullable=True)  
    nominee = Column(String, nullable=True)
    nomineeId = Column(Integer, ForeignKey("nominees.id"), nullable=True)
    personalDetails = Column(JSON, nullable=False)
    policyDocument = Column(String, nullable=True)
    # Relationship to user
    user = relationship("User", back_populates="policies")


class PolicyPurchase(Base):
    __tablename__ = "policy_purchase"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    type = Column(SqlEnum(PolicyType))
    planName = Column(String)
    coverage = Column(Float)
    premium = Column(Float)
    tenure = Column(Integer)
    nominee = Column(String, nullable=True)
    nomineeId = Column(Integer, ForeignKey("nominees.id"), nullable=True)
    personalDetails = Column(JSON, nullable=False)
    policyNumber = Column(String, unique=True, index=True)
    user = relationship("User", back_populates="policy_purchases")



class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), index=True)
    policyId = Column(Integer, ForeignKey("policy.id"))
    claimType = Column(String)
    amount = Column(Float)
    status = Column(String)
    user = relationship("User", back_populates="claims")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(SqlEnum(PolicyType))
    name = Column(String)
    description = Column(String)
    price = Column(Float)

class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, primary_key=True, index=True)
    fullName = Column(String)
    phone = Column(String)
    email = Column(String)
    category = Column(SqlEnum(ContactCategory))
    message = Column(String)

class Quotation(Base):
    __tablename__ = "quotation"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(SqlEnum(PolicyType))
    fullName = Column(String)
    email = Column(String)
    phone = Column(String)

class Documents(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), index=True)
    policyId = Column(Integer, ForeignKey("policy.id"))
    documentType = Column(String)
    documentUrl = Column(String)
    uploadDate = Column(Date)
    fileSize = Column(Float)
    user = relationship("User", back_populates="documents")

class Nominee(Base):
    __tablename__ = "nominees"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), index=True)
    policyId = Column(Integer, ForeignKey("policy.id"))
    name = Column(String)
    # 'relationship' is a reserved Python name used by SQLAlchemy; keep the DB column name but avoid shadowing
    relationship_type = Column('relationship', String)
    phone = Column(String)
    email = Column(String)
    user = relationship("User", back_populates="nominees")


class Activities(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), index=True)
    type = Column(SqlEnum(ActivityTypes))
    description = Column(String)
    time = Column(Date)
    amount = Column(Float)
    user = relationship("User", back_populates="activities")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    message = Column(String)
    time = Column(Date)
    type = Column(SqlEnum(NotificationTypes))
    read = Column(Boolean, default=False)
    policyId = Column(Integer, ForeignKey("policy.id"), nullable=True)
    user = relationship("User", back_populates="notifications")


class Payments(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    policyId = Column(Integer, ForeignKey("policy.id"))
    amount = Column(Float)
    orderId = Column(String)
    paidDate = Column(Date)
    paymentMethod = Column(String)
    status = Column(SqlEnum(PaymentStatus), default=PaymentStatus.pending)
    transactionId = Column(String, unique=True, index=True)
    returnUrl = Column(String)
    paymentUrl = Column(String)
    user = relationship("User", back_populates="payments")


class ApplicationProcess(Base):
    __tablename__ = "application_process"

    id = Column(Integer, primary_key=True, index=True)
    applicationId = Column(String, unique=True, index=True)
    status = Column(String)
    currentStep = Column(String)
    agentData = Column(JSON, nullable=True)
    stepHistory = Column(JSON, nullable=True)
    auditTrail = Column(JSON, nullable=True)  # Store audit entries for manual completions and actions
    reviewReason = Column(String, nullable=True)
    assignedTo = Column(String, nullable=True)
    customerId = Column(Integer, ForeignKey("users.id"), nullable=True)
    startTime = Column(Date)
    lastUpdated = Column(Date)

    user = relationship("User")
