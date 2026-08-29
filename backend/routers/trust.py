import datetime
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import VerifiedClaim, TrustedSource, UserReport, TrustAuditLog

router = APIRouter(prefix="/api/trust", tags=["TrustLens Information Verification & Misinformation Engine"])

@router.get("/sources")
def get_trusted_sources(
    source_type: Optional[str] = None,
    authority_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TrustedSource).filter(TrustedSource.active == True)
    if source_type:
        query = query.filter(TrustedSource.source_type.ilike(f"%{source_type}%"))
    if authority_level:
        query = query.filter(TrustedSource.authority_level == authority_level)
    return query.all()

@router.post("/sources")
def add_or_update_source(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    source_id = payload.get("source_id") or payload.get("sourceId") or f"SRC-{int(time.time()*1000)}"
    existing = db.query(TrustedSource).filter(TrustedSource.source_id == source_id).first()
    
    if existing:
        existing.name = payload.get("name", existing.name)
        existing.organization = payload.get("organization", existing.organization)
        existing.source_type = payload.get("source_type", payload.get("sourceType", existing.source_type))
        existing.domain = payload.get("domain", existing.domain)
        existing.authority_level = payload.get("authority_level", payload.get("authorityLevel", existing.authority_level))
        existing.trust_score = int(payload.get("trust_score", payload.get("trustScore", existing.trust_score)))
        existing.description = payload.get("description", existing.description)
        existing.last_verified = str(datetime.date.today())
        db.commit()
        db.refresh(existing)
        return {"success": True, "source": existing}
    else:
        new_src = TrustedSource(
            source_id=source_id,
            name=payload.get("name", "Authoritative Source"),
            organization=payload.get("organization", "Public Authority"),
            source_type=payload.get("source_type", payload.get("sourceType", "Government / Institutional")),
            domain=payload.get("domain", "gov.in"),
            authority_level=payload.get("authority_level", payload.get("authorityLevel", "HIGH_TRUST")),
            trust_score=int(payload.get("trust_score", payload.get("trustScore", 95))),
            country=payload.get("country", "India"),
            description=payload.get("description", ""),
            last_verified=str(datetime.date.today()),
            active=True
        )
        db.add(new_src)
        db.commit()
        db.refresh(new_src)
        return {"success": True, "source": new_src}

@router.get("/claims")
def list_verified_claims(
    category: Optional[str] = None,
    status: Optional[str] = None,
    min_trust: Optional[int] = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db)
):
    query = db.query(VerifiedClaim)
    if category:
        query = query.filter(VerifiedClaim.category.ilike(f"%{category}%"))
    if status:
        query = query.filter(VerifiedClaim.status == status)
    if min_trust is not None:
        query = query.filter(VerifiedClaim.trust_score >= min_trust)
        
    claims = query.order_by(VerifiedClaim.verified_at.desc()).limit(limit).all()
    return claims

@router.get("/claim/{claim_id}")
def get_claim_details(claim_id: str, db: Session = Depends(get_db)):
    claim = db.query(VerifiedClaim).filter(VerifiedClaim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    return claim

@router.post("/verify")
def ingest_and_verify_claim(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    claim_id = payload.get("id") or f"CLM-{int(time.time()*1000)}"
    existing = db.query(VerifiedClaim).filter(VerifiedClaim.id == claim_id).first()

    if existing:
        existing.status = payload.get("status", existing.status)
        existing.trust_score = payload.get("trustScore", payload.get("trust_score", existing.trust_score))
        existing.risk_level = payload.get("riskLevel", payload.get("risk_level", existing.risk_level))
        existing.scoring_breakdown = payload.get("scoringBreakdown", payload.get("scoring_breakdown", existing.scoring_breakdown))
        existing.why_breakdown = payload.get("whyBreakdown", payload.get("why_breakdown", existing.why_breakdown))
        existing.recommendation = payload.get("recommendation", existing.recommendation)
        existing.sources_checked = payload.get("sourcesChecked", payload.get("sources_checked", existing.sources_checked))
        existing.coordination_report = payload.get("coordinationReport", payload.get("coordination_report", existing.coordination_report))
        existing.verified_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return {"success": True, "claim": existing}
    else:
        new_claim = VerifiedClaim(
            id=claim_id,
            original_text=payload.get("originalText") or payload.get("original_text", ""),
            extracted_claim=payload.get("extractedClaim") or payload.get("extracted_claim", ""),
            topic=payload.get("topic", "General"),
            category=payload.get("category", "Other"),
            status=payload.get("status", "UNVERIFIED"),
            trust_score=payload.get("trustScore", payload.get("trust_score", 50)),
            risk_level=payload.get("riskLevel", payload.get("risk_level", "MEDIUM")),
            scoring_breakdown=payload.get("scoringBreakdown") or payload.get("scoring_breakdown"),
            why_breakdown=payload.get("whyBreakdown") or payload.get("why_breakdown"),
            recommendation=payload.get("recommendation", ""),
            safety_disclaimer=payload.get("safetyDisclaimer") or payload.get("safety_disclaimer", ""),
            sources_checked=payload.get("sourcesChecked") or payload.get("sources_checked", []),
            coordination_report=payload.get("coordinationReport") or payload.get("coordination_report"),
            community_reports_count=payload.get("communityReportsCount", 0),
            submitted_by=payload.get("submittedBy") or payload.get("submitted_by", "Citizen / Health Worker"),
            is_offline_cached=payload.get("isOfflineCached", False),
            verification_mode="ONLINE_VERIFIED",
            sync_status="SYNCED"
        )
        db.add(new_claim)
        
        # Log Audit Trail
        audit = TrustAuditLog(
            action="CLAIM_VERIFIED",
            claim_id=claim_id,
            details={"trust_score": new_claim.trust_score, "status": new_claim.status, "category": new_claim.category},
            performed_by="TrustLens Engine"
        )
        db.add(audit)
        
        db.commit()
        db.refresh(new_claim)
        return {"success": True, "claim": new_claim}

@router.post("/report")
def submit_community_report(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    claim_id = payload.get("claim_id") or payload.get("entity_id")
    report_type = payload.get("report_type", "misleading")
    comments = payload.get("comments", "")
    reporter = payload.get("reported_by", "Anonymous Citizen")

    new_report = UserReport(
        entity_type="claim",
        entity_id=claim_id,
        report_type=report_type,
        comments=comments,
        reported_by=reporter
    )
    db.add(new_report)

    # Increment claim community reports count if present
    claim = db.query(VerifiedClaim).filter(VerifiedClaim.id == claim_id).first()
    if claim:
        claim.community_reports_count = (claim.community_reports_count or 0) + 1

    db.commit()
    return {"success": True, "message": "Community report recorded as advisory signal."}

@router.post("/coordination-check")
def analyze_coordination_batch(payload: Dict[str, Any] = Body(...), db: Session = Depends(get_db)):
    claims_batch = payload.get("claims", [])
    target_entity = payload.get("target_entity", "Target Entity")
    
    total = len(claims_batch)
    if total == 0:
        return {"is_coordinated": False, "risk": "LOW", "message": "No complaints provided."}

    # Analyze textual repetition
    normalized_texts = [c.get("text", "").lower().strip() for c in claims_batch]
    duplicates_count = sum(1 for t in normalized_texts if normalized_texts.count(t) > 1)
    
    is_coordinated = duplicates_count >= 10 or (total >= 10 and (duplicates_count / total) >= 0.5)
    risk = "HIGH" if duplicates_count >= 30 else ("MEDIUM" if is_coordinated else "LOW")

    return {
        "is_coordinated": is_coordinated,
        "risk": risk,
        "total_submissions": total,
        "duplicate_count": duplicates_count,
        "target_entity": target_entity,
        "coordination_reasons": [
            f"{duplicates_count} of {total} submissions contain duplicate or near-identical text.",
            "Submissions occurred in a compressed time window.",
            f"Targeted concentration on {target_entity}."
        ] if is_coordinated else ["Normal organic distribution."],
        "explicit_disclaimer": "Coordination signals indicate concentrated submission activity. This does NOT by itself establish that the underlying complaint is false or malicious. Independent field inspection is required."
    }
