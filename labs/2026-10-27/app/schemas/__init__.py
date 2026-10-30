from pydantic import BaseModel, ConfigDict, Field, field_validator

class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class Signup(Input):
    email: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=10, max_length=128)

    @field_validator("email")
    @classmethod
    def email_shape(cls, value):
        value = value.strip().lower()
        if value.count("@") != 1 or " " in value:
            raise ValueError("email format")
        return value

class ItemInput(Input):
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    price: float = Field(ge=0, le=1_000_000_000)

class ItemPatch(Input):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    price: float | None = Field(default=None, ge=0, le=1_000_000_000)

    @field_validator("name", "description", "price")
    @classmethod
    def no_explicit_null(cls, value):
        if value is None:
            raise ValueError("omit unchanged fields; null is not allowed")
        return value

class Named(Input):
    name: str = Field(min_length=1, max_length=100)

class Telemetry(Input):
    raw: int = Field(strict=True, ge=0, le=2147483647)
    touched: bool
    led: bool

class LedCommand(Input):
    led: bool
