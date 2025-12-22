from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
import models, schemas, crud
from datetime import datetime
import requests
import os
import json

AGENT_SERVER_URL = os.getenv("AGENT_SERVER_URL", "http://127.0.0.1:8001")


router = APIRouter(
    prefix="/agent",
    tags=["Agent Integration"],
    responses={404: {"description": "Not found"}},
)

@router.post("/sync", response_model=schemas.ApplicationProcess)
def sync_agent_state(process: schemas.ApplicationProcessCreate, db: Session = Depends(get_db)):
    """
    Called by the Agent to create or update the application process state.
    """
    # Check if exists
    db_process = crud.get_application_process(db, process.applicationId)
    if db_process:
        # Update existing
        # We need to compute values to update. 
        # Note: 'process' is ApplicationProcessCreate, which might have different fields than Update
        # But here we treat it as an upsert payload suitable for both.
        
        update_data = process.model_dump(exclude_unset=True)
        update_data["lastUpdated"] = datetime.now().date()
        
        return crud.update_by_id(db, models.ApplicationProcess, "id", db_process.id, update_data)
    else:
        # Create new
        # Set lastUpdated same as startTime if not provided
        if not process.lastUpdated:
            process_dict = process.model_dump()
            process_dict["lastUpdated"] = datetime.now().date()
            # If generated from Pydantic model it might be simpler
            process = schemas.ApplicationProcessCreate(**process_dict)
            
        return crud.create_entry(db, models.ApplicationProcess, process)

@router.get("/applications", response_model=List[schemas.ApplicationProcess])
def get_applications(status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Get list of application processes. Used by Admin Panel AI Process Flow.
    """
    return crud.list_application_processes(db, status)

@router.get("/application/{application_id}", response_model=schemas.ApplicationProcess)
def get_application(application_id: str, db: Session = Depends(get_db)):
    """
    Get detailed application process. Used by Admin Panel Case Details.
    """
    process = crud.get_application_process(db, application_id)
    if not process:
        raise HTTPException(status_code=404, detail="Application process not found")
    return process

@router.post("/review")
def submit_review_decision(
    application_id: str = Body(...), 
    action: str = Body(..., regex="^(approve|reject|request_docs|escalate)$"), 
    reason: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Submit a human review decision. Updates the DB status and should trigger Agent resume.
    """
    process = crud.get_application_process(db, application_id)
    if not process:
        raise HTTPException(status_code=404, detail="Application process not found")
    
    # Update DB based on action
    update_data = {"lastUpdated": datetime.now().date(), "reviewReason": reason}
    
    if action == "approve":
        update_data["status"] = "approved" # Or 'processing' if it goes back to agent
        # TODO: Trigger Agent Resume (Webhook to Agent Server)
    elif action == "reject":
        update_data["status"] = "rejected"
    elif action == "request_docs":
        update_data["status"] = "ask_for_document"
    elif action == "escalate":
        update_data["status"] = "escalate_to_senior"
        
    crud.update_by_id(db, models.ApplicationProcess, "id", process.id, update_data)
    
    # Trigger Agent Resume for ALL decisions (Approve, Reject, Escalate, Docs)
    try:
        # Map action to Agent's expected format
        # Agent expects: "approve", "reject", "override", "escalate", "request_docs"
        agent_action = action
        
        payload = {
            "application_id": application_id,
            "action": agent_action,
            "override_notes": reason
        }
        # Fire and forget (or log error)
        # We use a short timeout to not block the admin 
        requests.post(f"{AGENT_SERVER_URL}/approve", json=payload, timeout=5)
    except Exception as e:
        print(f"❌ Error resuming agent workflow at {AGENT_SERVER_URL}: {e}")
    
    return {"message": f"Review action '{action}' submitted successfully", "application_id": application_id}

@router.post("/step/complete", response_model=schemas.ApplicationProcess)
def complete_step_manually(
    application_id: str = Body(...),
    step_id: int = Body(...),
    step_name: str = Body(...),
    admin_notes: str = Body(...),
    admin_id: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Manually mark a step as complete with admin verification.
    Updates the step status in stepHistory and triggers next step in agent workflow.
    """
    # Get application process
    process = crud.get_application_process(db, application_id)
    if not process:
        raise HTTPException(status_code=404, detail="Application process not found")
    
    # Get current step history
    step_history = []
    if process.stepHistory:
        if isinstance(process.stepHistory, str):
            step_history = json.loads(process.stepHistory)
        else:
            step_history = list(process.stepHistory)
    elif process.agentData and process.agentData.get("stepHistory"):
        step_history_data = process.agentData.get("stepHistory")
        if isinstance(step_history_data, str):
            step_history = json.loads(step_history_data)
        else:
            step_history = list(step_history_data)
    
    # Find and update the step
    step_found = False
    previous_status = None
    for step in step_history:
        if step.get("id") == step_id or step.get("name") == step_name:
            previous_status = step.get("status", "pending")
            step["status"] = "completed"
            step["completed_by"] = "human"
            step["admin_notes"] = admin_notes
            step["completed_at"] = datetime.now().isoformat()
            step["completion_method"] = "manual"
            if admin_id:
                step["admin_id"] = admin_id
            step_found = True
            break
    
    # If step not found in history, add it
    if not step_found:
        new_step = {
            "id": step_id,
            "name": step_name,
            "status": "completed",
            "completed_by": "human",
            "admin_notes": admin_notes,
            "completed_at": datetime.now().isoformat(),
            "completion_method": "manual",
            "timestamp": datetime.now().isoformat(),
            "summary": f"Manually completed by admin: {admin_notes}"
        }
        if admin_id:
            new_step["admin_id"] = admin_id
        step_history.append(new_step)
    
    # Update agentData if it exists
    agent_data = process.agentData or {}
    if "stepHistory" not in agent_data:
        agent_data["stepHistory"] = step_history
    
    # Create audit trail entry for manual completion
    audit_trail = []
    if process.auditTrail:
        if isinstance(process.auditTrail, str):
            audit_trail = json.loads(process.auditTrail)
        else:
            audit_trail = list(process.auditTrail)
    
    # Get admin name (if available from admin_id, otherwise use "Admin")
    admin_name = admin_id or "Admin"
    # Try to get admin name from User table if admin_id is provided
    if admin_id:
        try:
            admin_user = db.query(models.User).filter(models.User.id == int(admin_id)).first()
            if admin_user:
                admin_name = admin_user.name or admin_user.email or f"Admin #{admin_id}"
        except:
            pass  # If admin lookup fails, use admin_id as fallback
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "manual_step_completion",
        "step_name": step_name,
        "step_id": step_id,
        "admin_name": admin_name,
        "admin_id": admin_id,
        "admin_notes": admin_notes,
        "previous_status": previous_status or "pending",
        "new_status": "completed",
        "message": f"Admin {admin_name} manually completed step '{step_name}'"
    }
    audit_trail.append(audit_entry)
    
    # Prepare update data
    update_data = {
        "stepHistory": step_history,
        "agentData": agent_data,
        "auditTrail": audit_trail,
        "lastUpdated": datetime.now().date()
    }
    
    # Update currentStep if this was the current step
    if process.currentStep == step_name or process.currentStep == str(step_id):
        # Find next pending step
        next_step = None
        for step in step_history:
            if step.get("status") in ["pending", "in_progress", "in-progress"]:
                next_step = step.get("name", "unknown")
                break
        if next_step:
            update_data["currentStep"] = next_step
    
    # Update database
    updated_process = crud.update_by_id(db, models.ApplicationProcess, "id", process.id, update_data)
    
    # Trigger agent workflow to proceed to next step (fire and forget)
    try:
        payload = {
            "application_id": application_id,
            "completed_step": step_name,
            "action": "manual_complete",
            "notes": admin_notes,
            "step_id": step_id
        }
        # Try to notify agent server (non-blocking)
        requests.post(f"{AGENT_SERVER_URL}/resume", json=payload, timeout=3)
    except Exception as e:
        # Log error but don't fail the request
        print(f"⚠️ Warning: Could not notify agent server at {AGENT_SERVER_URL}/resume: {e}")
        # This is not critical - the step is already marked complete in DB
    
    return updated_process

@router.post("/step/rollback", response_model=schemas.ApplicationProcess)
def rollback_step_completion(
    application_id: str = Body(...),
    step_id: int = Body(...),
    step_name: str = Body(...),
    admin_id: Optional[str] = Body(None),
    rollback_reason: Optional[str] = Body(None),
    db: Session = Depends(get_db)
):
    """
    Rollback a manually completed step to pending status.
    Only works for steps that were manually completed.
    """
    # Get application process
    process = crud.get_application_process(db, application_id)
    if not process:
        raise HTTPException(status_code=404, detail="Application process not found")
    
    # Get current step history
    step_history = []
    if process.stepHistory:
        if isinstance(process.stepHistory, str):
            step_history = json.loads(process.stepHistory)
        else:
            step_history = list(process.stepHistory)
    elif process.agentData and process.agentData.get("stepHistory"):
        step_history_data = process.agentData.get("stepHistory")
        if isinstance(step_history_data, str):
            step_history = json.loads(step_history_data)
        else:
            step_history = list(step_history_data)
    
    # Find the step
    step_found = False
    for step in step_history:
        if step.get("id") == step_id or step.get("name") == step_name:
            # Check if step was manually completed
            if step.get("completed_by") != "human":
                raise HTTPException(
                    status_code=400, 
                    detail=f"Step '{step_name}' was not manually completed. Only manually completed steps can be rolled back."
                )
            
            # Rollback the step
            step["status"] = "pending"
            step["rollback_reason"] = rollback_reason or "Rolled back by admin"
            step["rolled_back_at"] = datetime.now().isoformat()
            step["rolled_back_by"] = admin_id or "admin"
            # Keep manual completion metadata for audit trail
            step["previous_completion"] = {
                "completed_by": step.get("completed_by"),
                "completed_at": step.get("completed_at"),
                "admin_notes": step.get("admin_notes")
            }
            step_found = True
            break
    
    if not step_found:
        raise HTTPException(status_code=404, detail=f"Step '{step_name}' not found in step history")
    
    # Update agentData if it exists
    agent_data = process.agentData or {}
    if "stepHistory" not in agent_data:
        agent_data["stepHistory"] = step_history
    
    # Create audit trail entry for rollback
    audit_trail = []
    if process.auditTrail:
        if isinstance(process.auditTrail, str):
            audit_trail = json.loads(process.auditTrail)
        else:
            audit_trail = list(process.auditTrail)
    
    admin_name = admin_id or "Admin"
    if admin_id:
        try:
            admin_user = db.query(models.User).filter(models.User.id == int(admin_id)).first()
            if admin_user:
                admin_name = admin_user.name or admin_user.email or f"Admin #{admin_id}"
        except:
            pass
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "step_rollback",
        "step_name": step_name,
        "step_id": step_id,
        "admin_name": admin_name,
        "admin_id": admin_id,
        "rollback_reason": rollback_reason or "Rolled back by admin",
        "message": f"Admin {admin_name} rolled back step '{step_name}' to pending status"
    }
    audit_trail.append(audit_entry)
    
    # Prepare update data
    update_data = {
        "stepHistory": step_history,
        "agentData": agent_data,
        "auditTrail": audit_trail,
        "lastUpdated": datetime.now().date()
    }
    
    # Update currentStep if this was the current step
    if process.currentStep == step_name or process.currentStep == str(step_id):
        update_data["currentStep"] = step_name
    
    # Update database
    updated_process = crud.update_by_id(db, models.ApplicationProcess, "id", process.id, update_data)
    
    return updated_process

