from sqlmodel import SQLModel, create_engine, Session
from .models import *

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

def get_session():
    with Session(engine) as session:
        yield session

def create_dummy_data():
    rack = [
        Rack(name="R1", description="R1 desc", serial_number="SN-001", unit_capacity=10, max_power_consumption=2000),
        Rack(name="R2", description="R2 desc", serial_number="SN-002", unit_capacity=12, max_power_consumption=1500),
    ]
    
    devices = [
        Device(name="D1", description="D1 desc", serial_number="SN-003", 
               unit_size=2, power_consumption=500, rack = rack[0]),
        Device(name="D2", description="D2 desc", serial_number="SN-004", 
               unit_size=4, power_consumption=600, rack = rack[1]),
        Device(name="D3", description="D3 desc", serial_number="SN-005", 
               unit_size=4, power_consumption=550, rack = rack[1])
    ]

    with Session(engine) as session:
            for item in rack:
                session.add(item)

            for item in devices:
                session.add(item)

            session.commit()


def create_db():
    SQLModel.metadata.create_all(engine)