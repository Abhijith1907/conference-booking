from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Timing(BaseModel):
    start_ts: str
    end_ts: str


class Conference(BaseModel):
    name: str
    location: str
    topics: str = Field(description="list of topics not more than 10")
    timing: Timing
    available_slots: int = Field(
        description="avaiable slot should be greater than 0", ge=0
    )


class BookingStatus(str, Enum):
    confirmed = "CONFIRMED"
    wailist = "WAILIST"
    cancelled = "CANCELLED"


class ConferenceBookingPayload(BaseModel):
    user_id: str
