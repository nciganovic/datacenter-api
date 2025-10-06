from sqlmodel import SQLModel, create_engine, Session, select
from .models import *

sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

"""
Important: Rows used in test cases have 'Test' in their name. 
Tests will fail if you change values of unit_capacity or max_power_consumption 
on Rack or power_consumption and unit_size on Device.
"""

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
               unit_size=4, power_consumption=500, rack = rack[0]),
        Device(name="D2", description="D2 desc", serial_number="SN-004", 
               unit_size=4, power_consumption=600, rack = rack[1]),
        Device(name="D3", description="D3 desc", serial_number="SN-005", 
               unit_size=4, power_consumption=550, rack = rack[1])
    ]

    racks_for_test = [
        Rack(name="R3 Test", description="Rack 3 for testing", serial_number="SN-021", unit_capacity=8, max_power_consumption=1000),
        Rack(name="R4 Test", description="Rack 4 for testing", serial_number="SN-022", unit_capacity=8, max_power_consumption=1200),
        Rack(name="R5 Test", description="Rack 5 for testing", serial_number="SN-023", unit_capacity=8, max_power_consumption=1100),
    ]

    devices_for_test = [
        Device(name="D400_1 Test", description="D4 used for testing...", serial_number="SN-006", 
               unit_size=2, power_consumption=400),
        Device(name="D400_2 Test", description="D4 used for testing...", serial_number="SN-007", 
               unit_size=2, power_consumption=400),
        Device(name="D300 Test", description="D3 used for testing...", serial_number="SN-008", 
               unit_size=2, power_consumption=300),
        Device(name="D200 Test", description="D2 used for testing...", serial_number="SN-009", 
               unit_size=2, power_consumption=200),
        Device(name="D600 Test", description="D6 used for testing...", serial_number="SN-010", 
               unit_size=3, power_consumption=600),
        Device(name="D800 Test", description="D8 used for testing...", serial_number="SN-0100", 
               unit_size=4, power_consumption=800),
        Device(name="D1000 Test", description="D10 used for testing...", serial_number="SN-0101", 
               unit_size=4, power_consumption=1000),
    ]

    with Session(engine) as session:
        #Check if data already exists in db
        query: list[Rack] = session.exec(select(Rack)).all()
        if(len(query) > 0):
            return

        #Dummy data to play with
        for item in rack:
            session.add(item)

        for item in devices:
            session.add(item)

        #Used for test_suggestion_1 test
        for item in racks_for_test:
            session.add(item)

        for item in devices_for_test:
            session.add(item)

        session.commit()


def create_db():
    SQLModel.metadata.create_all(engine)