"""The shape of an AI assessment. Pydantic rejects anything that doesn't fit."""

from pydantic import BaseModel, Field, field_validator

from ..severity import Severity


class Assessment(BaseModel):
    """What the AI tells the analyst about one alert."""

    summary: str = Field(min_length=1)
    risk_level: Severity
    confidence: int = Field(ge=0, le=100)  # how sure the AI is, in percent
    likely_false_positive: bool
    investigation_steps: list[str] = Field(min_length=1)

    @field_validator("risk_level", mode="before")
    @classmethod
    def accept_any_letter_case(cls, value):
        """Models answer 'high' or 'HIGH'; our labels are 'High'."""
        if isinstance(value, str):
            return value.strip().capitalize()
        return value
