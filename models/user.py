from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class User(BaseModel):
    user_id: str
    interested_topics: str
