import datetime
import uuid
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OTP/PIN login
    pin_hash = Column(String(255), nullable=True)       # 4-6 digit offline PIN
    name = Column(String(100), nullable=False)
    role = Column(String(30), default="health_worker")  # health_worker, doctor, vet, citizen, admin
    village = Column(String(100), default="Kopargaon")
    phone = Column(String(20), nullable=True)
    specialization = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Case(Base):
    __tablename__ = "cases"

    id = Column(String(64), primary_key=True, index=True)  # Client generated UUID or timestamp
    case_type = Column(String(30), nullable=False)          # human_general, child_development, livestock
    subject_name = Column(String(100), nullable=False)
    age_or_dob = Column(String(50), nullable=True)
    gender_or_sex = Column(String(20), nullable=True)
    species = Column(String(50), default="Human")
    tag_or_id = Column(String(50), nullable=True)
    guardian_or_owner = Column(String(100), nullable=True)
    contact_phone = Column(String(20), nullable=True)
    village = Column(String(100), default="Kopargaon")
    location_gps = Column(String(100), nullable=True)
    risk_level = Column(String(20), default="GREEN")        # GREEN, YELLOW, ORANGE, RED
    triage_summary = Column(Text, nullable=True)
    primary_condition = Column(String(150), nullable=True)
    confidence_score = Column(Float, default=0.85)
    data_payload = Column(JSON, nullable=True)              # Symptoms, Vitals, Milestones, Growth Data
    images = Column(JSON, nullable=True)                    # Array of base64 images / URLs
    status = Column(String(30), default="screened")         # screened, escalated, reviewed, resolved
    assigned_role = Column(String(30), nullable=True)       # doctor, vet
    assigned_doctor_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    client_created_at = Column(DateTime, default=datetime.datetime.utcnow)
    server_synced_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_synced = Column(Boolean, default=True)

    reviews = relationship("ClinicalReview", back_populates="case", cascade="all, delete-orphan")

class ClinicalReview(Base):
    __tablename__ = "clinical_reviews"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id"), nullable=False)
    reviewer_name = Column(String(100), nullable=False)
    reviewer_role = Column(String(30), nullable=False)      # doctor, vet
    reviewer_notes = Column(Text, nullable=False)
    prescribed_treatment = Column(Text, nullable=True)
    escalation_instructions = Column(Text, nullable=True)
    verified_risk_level = Column(String(20), nullable=True)
    is_urgent_referral = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    case = relationship("Case", back_populates="reviews")

class OutbreakAlert(Base):
    __tablename__ = "outbreak_alerts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    disease = Column(String(100), nullable=False)
    target_group = Column(String(50), nullable=False)
    village = Column(String(100), nullable=False)
    severity = Column(String(20), default="WARNING")        # WARNING, CRITICAL, RESOLVED
    description = Column(Text, nullable=False)
    precautions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(String(50), primary_key=True, index=True)  # e.g. DOC-001 or VET-001
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, unique=True)  # Auth link
    role = Column(String(20), default="doctor")  # doctor, vet
    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    medical_reg_no = Column(String(50), nullable=True)
    education = Column(String(200), nullable=False)
    experience_years = Column(Integer, default=5)
    specialization = Column(String(150), nullable=True)
    consultation_fee = Column(String(100), nullable=False)
    clinic_name = Column(String(150), nullable=False)
    village = Column(String(100), nullable=False, index=True)
    pincode = Column(String(10), default="423601")
    address = Column(Text, nullable=False)
    phone = Column(String(30), nullable=False)
    whatsapp = Column(String(30), nullable=True)
    opd_timings = Column(String(150), nullable=False)
    languages = Column(String(150), default="Marathi, Hindi, English")
    facilities = Column(Text, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    availability_state = Column(String(20), default="AVAILABLE")
    last_status_time = Column(String(50), nullable=True)
    verified = Column(Boolean, default=False)

class ClinicalKnowledge(Base):
    __tablename__ = "clinical_knowledge"

    id = Column(String(50), primary_key=True, index=True)
    symptom = Column(String(200), nullable=False, index=True)
    raw_symptom_text = Column(Text, nullable=True)
    condition = Column(String(200), nullable=False, index=True)
    attributes = Column(JSON, nullable=True)
    source = Column(String(100), default="EkaCare/BODHI-S")
    verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), nullable=True)
    cases_synced_count = Column(Integer, default=0)
    client_timestamp = Column(DateTime, nullable=True)
    server_timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(30), default="SUCCESS")

# =============================================================================
# TRUSTLENS INFORMATION VERIFICATION & MISINFORMATION DETECTION MODELS
# =============================================================================

class TrustedSource(Base):
    __tablename__ = "trusted_sources"

    source_id = Column(String(50), primary_key=True)  # e.g. SRC-MYSCHEME-01, SRC-MOHFW-04
    name = Column(String(200), nullable=False)
    organization = Column(String(200), nullable=False)
    source_type = Column(String(100), nullable=False)
    domain = Column(String(150), nullable=False, unique=True, index=True)
    authority_level = Column(String(50), default="HIGH_TRUST") # HIGH_TRUST, MEDIUM_TRUST, LOW_TRUST, UNKNOWN
    trust_score = Column(Integer, default=95)
    country = Column(String(50), default="India")
    description = Column(Text, nullable=True)
    last_verified = Column(String(50), nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class VerifiedClaim(Base):
    __tablename__ = "verified_claims"

    id = Column(String(64), primary_key=True, index=True)  # e.g. CLM-XXXX
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    original_text = Column(Text, nullable=False)
    extracted_claim = Column(Text, nullable=True)
    topic = Column(String(150), nullable=True)
    category = Column(String(50), default="Other", index=True) # Government, Healthcare, Agriculture, Civic, Education, Finance, Other
    status = Column(String(30), default="UNVERIFIED", index=True) # VERIFIED, UNVERIFIED, SUSPICIOUS, CONTRADICTED
    trust_score = Column(Integer, default=50) # 0 to 100
    risk_level = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH
    scoring_breakdown = Column(JSON, nullable=True)
    why_breakdown = Column(JSON, nullable=True)
    recommendation = Column(Text, nullable=True)
    safety_disclaimer = Column(Text, nullable=True)
    sources_checked = Column(JSON, nullable=True)
    coordination_report = Column(JSON, nullable=True)
    community_reports_count = Column(Integer, default=0)
    submitted_by = Column(String(100), default="Anonymous")
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    verified_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_offline_cached = Column(Boolean, default=False)
    verification_mode = Column(String(30), default="ONLINE_VERIFIED")
    normalized_hash = Column(String(64), index=True, nullable=True)
    sync_status = Column(String(20), default="SYNCED")

class UserReport(Base):
    __tablename__ = "user_reports"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type = Column(String(50), default="claim") # claim, profile, review
    entity_id = Column(String(64), nullable=False, index=True)
    report_type = Column(String(50), nullable=False) # false_info, misleading, suspicious, harmful, duplicate
    comments = Column(Text, nullable=True)
    reported_by = Column(String(100), default="Anonymous Citizen")
    reported_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(30), default="pending")

class TrustAuditLog(Base):
    __tablename__ = "trust_audit_logs"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(100), nullable=False)
    claim_id = Column(String(64), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    performed_by = Column(String(100), default="System / Verifier")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
