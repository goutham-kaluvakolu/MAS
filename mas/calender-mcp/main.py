import datetime
import os.path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel, Field

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from dotenv import load_dotenv
from fastapi_mcp import FastApiMCP
import uvicorn

# --- Google API Configuration ---
SCOPES = ["https://www.googleapis.com/auth/calendar"]

load_dotenv()
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"

def get_service_dependency():
    """
    Handles Google authentication and returns a Google Calendar API service object.
    This function is now designed to be used with FastAPI's Depends.
    """
    creds = None
    
    scopes_str = os.getenv("SCOPES")
    scopes = scopes_str.split(' ') if scopes_str else SCOPES

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("No valid token.json found or token expired. Starting new authentication flow...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, scopes)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)
        return service
    except HttpError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred with Google Calendar API: {error}"
        )

# --- FastAPI Application ---
app = FastAPI(
    title="Google Calendar MCP",
    description="FastAPI server for managing Google Calendar events.",
    version="1.1.0" # Version bump for new changes
)

mcp = FastApiMCP(app)
mcp.mount()

# --- Pydantic Models for Request Bodies and Responses ---

class EventTime(BaseModel):
    dateTime: Optional[datetime.datetime] = None
    date: Optional[datetime.date] = None
    timeZone: str = Field(default="UTC", description="Timezone (e.g., 'America/New_York', 'UTC')")

    def model_dump_for_google(self):
        """Dumps the model in the format Google API expects."""
        if self.dateTime:
            return {"dateTime": self.dateTime.isoformat(), "timeZone": self.timeZone}
        elif self.date:
            return {"date": self.date.isoformat(), "timeZone": self.timeZone}
        return {}

class CalendarEventBase(BaseModel):
    summary: str = Field(..., description="Summary or title of the event")
    location: Optional[str] = None
    description: Optional[str] = None
    start: EventTime
    end: EventTime

class CalendarEventCreate(CalendarEventBase):
    pass

class CalendarEventResponse(CalendarEventBase):
    id: str
    htmlLink: str
    status: str

# --- NEW: Helper function to reduce code duplication ---
def _parse_google_event_dict(event: dict) -> CalendarEventResponse:
    """Parses a raw event dictionary from Google API into our response model."""
    return CalendarEventResponse(
        id=event['id'],
        htmlLink=event['htmlLink'],
        status=event['status'],
        summary=event.get('summary', '(No Title)'),
        location=event.get('location'),
        description=event.get('description'),
        start=EventTime(
            dateTime=event['start'].get('dateTime'),
            date=event['start'].get('date'),
            timeZone=event['start'].get('timeZone', 'UTC')
        ),
        end=EventTime(
            dateTime=event['end'].get('dateTime'),
            date=event['end'].get('date'),
            timeZone=event['end'].get('timeZone', 'UTC')
        )
    )

# --- API Endpoints ---

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Google Calendar MCP FastAPI server!"}

@app.get("/events/upcoming", response_model=List[CalendarEventResponse])
async def get_upcoming_events(
    max_results: int = 10,
    calendar_id: str = "primary",
    service: Resource = Depends(get_service_dependency) # CHANGED: Use dependency injection
):
    """
    Fetches the next N upcoming events from the specified calendar.
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        # CLEANER: Use the helper function
        return [_parse_google_event_dict(event) for event in events]
    except HttpError as error:
        error_details = error.content.decode()
        raise HTTPException(
            status_code=error.resp.status,
            detail=f"Error fetching upcoming events from Google Calendar: {error_details}"
        )

@app.get("/events/range", response_model=List[CalendarEventResponse])
async def get_events_in_range(
    start_time: datetime.datetime,
    end_time: datetime.datetime,
    calendar_id: str = "primary",
    max_results: int = 250,
    service: Resource = Depends(get_service_dependency) # CHANGED: Use dependency injection
):
    """
    Fetches events within a specified date/time range.
    """
    try:
        events_result = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start_time.isoformat(),
                timeMax=end_time.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        # CLEANER: Use the helper function
        return [_parse_google_event_dict(event) for event in events]
    except HttpError as error:
        raise HTTPException(
            status_code=error.resp.status,
            detail=f"Error fetching events in range: {error.content.decode()}"
        )


@app.post("/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
async def add_event(
    event_data: CalendarEventCreate,
    calendar_id: str = "primary",
    service: Resource = Depends(get_service_dependency) # CHANGED: Use dependency injection
):
    """
    Adds a new event to the specified calendar.
    """
    event = {
        'summary': event_data.summary,
        'location': event_data.location,
        'description': event_data.description,
        'start': event_data.start.model_dump_for_google(),
        'end': event_data.end.model_dump_for_google(),
    }
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        # CLEANER: Use the helper function
        return _parse_google_event_dict(created_event)
    except HttpError as error:
        raise HTTPException(
            status_code=error.resp.status,
            detail=f"Error adding event: {error.content.decode()}"
        )

@app.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    service: Resource = Depends(get_service_dependency) # CHANGED: Use dependency injection
):
    """
    Deletes an event from the specified calendar by its ID.
    """
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        return None # Return None for 204 No Content status
    except HttpError as error:
        if error.resp.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event with ID '{event_id}' not found in calendar '{calendar_id}'."
            )
        else:
            raise HTTPException(
                status_code=error.resp.status,
                detail=f"Error deleting event: {error.content.decode()}"
            )
            
mcp.setup_server()

# --- Entry point ---
if __name__ == "__main__":
    print("Starting Google Calendar FastAPI Server...")
    print("Server will be available at: http://localhost:8001")
    print("API documentation available at: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True, log_level="debug")