"""
Public endpoints - accessible without authentication
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from database import get_db

router = APIRouter(prefix="/public", tags=["Public"])

@router.get("/stats")
def get_platform_stats(db: Session = Depends(get_db)):
    """
    Get public platform statistics
    """
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_policies = db.query(func.count(models.Policy.id)).scalar() or 0
    total_claims = db.query(func.count(models.Claim.id)).scalar() or 0
    
    # Calculate claims resolved (approved or rejected)
    resolved_claims = db.query(func.count(models.Claim.id)).filter(
        models.Claim.status.in_(['approved', 'rejected'])
    ).scalar() or 0
    
    return {
        "totalUsers": total_users,
        "totalPolicies": total_policies,
        "totalClaims": total_claims,
        "claimsResolved": resolved_claims,
        "satisfactionRate": "4.8/5",
        "yearsOfService": "10+"
    }

@router.get("/testimonials")
def get_testimonials():
    """
    Get customer testimonials
    """
    return [
        {
            "id": 1,
            "name": "Rajesh Kumar",
            "role": "Business Owner",
            "rating": 5,
            "text": "SecureInsure has been a reliable partner for our business insurance needs. Their claims process is smooth and transparent.",
            "avatar": "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=100&h=100&fit=crop"
        },
        {
            "id": 2,
            "name": "Priya Sharma",
            "role": "Software Engineer",
            "rating": 5,
            "text": "The digital experience is fantastic. I can manage all my policies from my phone. Highly recommended!",
            "avatar": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop"
        },
        {
            "id": 3,
            "name": "Amit Patel",
            "role": "Entrepreneur",
            "rating": 4,
            "text": "Great customer service and competitive rates. They helped me find the perfect health insurance plan for my family.",
            "avatar": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=100&h=100&fit=crop"
        }
    ]

