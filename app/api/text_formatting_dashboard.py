"""
API routes for the text formatting dashboard
"""
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Dict, Any, Optional
from pathlib import Path
import os

from app.utils.text_formatting.monitor import get_monitor

# Create router
router = APIRouter(
    prefix="/text-formatting",
    tags=["text-formatting"],
    responses={404: {"description": "Not found"}},
)

# Set up templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Serve the text formatting dashboard HTML
    """
    return templates.TemplateResponse(
        "text_formatting_dashboard.html",
        {"request": request}
    )

@router.get("/report")
async def get_report(time_period: str = "day"):
    """
    Generate a report of text formatting performance
    
    Args:
        time_period: Time period for the report (day, week, month)
        
    Returns:
        Report data
    """
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="Invalid time period. Must be 'day', 'week', or 'month'.")
    
    # Get the monitor
    monitor = get_monitor()
    
    # Generate the report
    report = monitor.generate_report(time_period)
    
    return report

@router.get("/events")
async def get_events(time_period: str = "day", approach: Optional[str] = None, event_type: Optional[str] = None):
    """
    Get text formatting events
    
    Args:
        time_period: Time period for the events (day, week, month)
        approach: Filter by approach (structured_output, backend_processing, frontend_parsing, css_formatting)
        event_type: Filter by event type (success, fallback, error)
        
    Returns:
        List of events
    """
    # Validate time period
    if time_period not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="Invalid time period. Must be 'day', 'week', or 'month'.")
    
    # Get the monitor
    monitor = get_monitor()
    
    # Load events
    events = monitor._load_events(time_period)
    
    # Filter by approach if specified
    if approach:
        events = [e for e in events if e["approach"] == approach]
    
    # Filter by event type if specified
    if event_type:
        events = [e for e in events if e["event"] == event_type]
    
    return events

@router.post("/save-events")
async def save_events():
    """
    Save events to disk
    
    Returns:
        Success message
    """
    # Get the monitor
    monitor = get_monitor()
    
    # Save events
    monitor.save_events()
    
    return {"message": "Events saved successfully"}