from typing import Optional
from pydantic import PrivateAttr
from sqlmodel import CheckConstraint, Field, Relationship, SQLModel, create_engine

class DeviceBase(SQLModel):
    name: str = Field()
    description: str = Field()
    serial_number: str = Field(unique=True, max_length=30, description="Serial number must be maximum 30 characters")
    unit_size: int = Field(gt=0, description="Value must be positive number")
    power_consumption: int = Field(gt=0, description="Value must be positive number")
    rack_id: int | None = Field(default=None, foreign_key="rack.id", ondelete="RESTRICT")

class Device(DeviceBase, table=True):
    __tablename__ = "device"

    __table_args__ = (
        CheckConstraint("unit_size > 0", name="check_positive_unit_size"),
        CheckConstraint("power_consumption > 0", name="check_positive_power_consumption"),
    )

    id: int | None = Field(default=None, primary_key=True) 
    rack : "Rack" = Relationship(back_populates="devices")

class DeviceForm(DeviceBase):
    id: int
    rack_name: str

class RackBase(SQLModel):
    name: str = Field()
    description: str = Field()
    serial_number: str = Field(unique=True, max_length=30, description="Serial number must be maximum 30 characters")
    unit_capacity: int = Field(gt=0, description="Value must be positive number")
    max_power_consumption: int = Field(gt=0, description="Value must be positive number")

class Rack(RackBase, table=True):
    __tablename__ = "rack"

    __table_args__ = (
        CheckConstraint("unit_capacity > 0", name="check_positive_unit_capacity"),
        CheckConstraint("max_power_consumption > 0", name="check_positive_max_power_consumption"),
    )

    id: int | None = Field(default=None, primary_key=True) 
    devices: list["Device"] = Relationship(back_populates="rack")

class RackForm(RackBase):
    id: int
    power_consuption: int
