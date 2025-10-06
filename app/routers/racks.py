from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlmodel import Session, select
from app.database import get_session
from app.models import Rack, RackForm, Device
from app.routers.validation_helper import rack_exist_validation

router = APIRouter(prefix="/racks", tags=["racks"])

@router.get("/")
async def get_all(session: Session = Depends(get_session)):
    racks = [map_rack_form(rack) for rack in session.exec(select(Rack)).all()]
    return racks

@router.get("/{rack_id}")
async def get_single(rack_id: int, session: Session = Depends(get_session)):
    rack = session.get(Rack, rack_id)
    rack_exist_validation(rack_id, rack)
    return map_rack_form(rack)

def map_rack_form(rack: Rack):
    return RackForm(
        id = rack.id,
        name = rack.name,
        description = rack.description,
        serial_number = rack.serial_number,
        unit_capacity = rack.unit_capacity,
        max_power_consumption = rack.max_power_consumption,
        power_consumption = sum([d.power_consumption for d in rack.devices])
    )

@router.post("/")
async def create_rack(rack: Rack, session: Session = Depends(get_session)):
    try: 
        rack.name = rack.name.strip()
        rack.description = rack.description.strip()
        rack.serial_number = rack.serial_number.strip()
        
        rack_validation(rack, session, True)
        new_rack = Rack.model_validate(rack)

        session.add(new_rack)
        session.commit()
        session.refresh(new_rack)
        return new_rack
    except ValidationError as e:
        msg: list[str] = [err["msg"] for err in  e.errors()]
        raise HTTPException(
                status_code=422,
                detail={'messages': msg}
            )

def rack_validation(rack: Rack, session: Session, create_mod: bool):
    #Check if Rack with this id already exist, only check if it is creation, not update of rack
    if rack.id < 1:
        raise HTTPException(
                status_code=400,
                detail=f"Rack id must be positive number."
            )
    
    if create_mod:
        if(session.get(Rack, rack.id) is not None):
            raise HTTPException(
                status_code=400,
                detail=f"Rack with id '{rack.id}' already exists."
            )
    if(rack.unit_capacity < 1):
        raise HTTPException(
            status_code=400,
            detail=f"Unit capacity must be positive number."
        )
    
    if(rack.max_power_consumption < 1):
        raise HTTPException(
            status_code=400,
            detail=f"Max power consumption must be positive number."
        )
    
    if(not create_mod):
        rack_in_db = session.get(Rack, rack.id)
        total_consumption = sum([d.power_consumption for d in rack_in_db.devices])
        if(total_consumption > rack.max_power_consumption):
            raise HTTPException(
                status_code=400,
                detail=f"Device power consumption exceeds limits of rack power limit. First detach some devices from this rack."
            ) 
        
        total_size = sum([d.unit_size for d in rack_in_db.devices])
        if(total_size > rack.unit_capacity):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot fit all devices in current rack with this unit capacity. First detach some devices from this rack."
            ) 

    id_to_check = rack.id if not create_mod else -1
    unique_serial_number_validation(id_to_check, rack.serial_number, session)

def unique_serial_number_validation(current_id: int, value: str, session: Session): 
    select_rack = select(Rack.id).where(Rack.serial_number == value).where(Rack.id != current_id)
    rack = session.exec(select_rack).first()
    select_device = select(Device.id).where(Device.serial_number == value)
    device = session.exec(select_device).first()
    if rack is not None or device is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Serial number '{value}' already exists."
        )
    return

@router.put("/{rack_id}")
async def update_rack(rack_id: int, rack: Rack, session: Session = Depends(get_session)):
    try: 
        rack.id = rack_id
        rack_to_update: Rack = session.get(Rack, rack_id)
        rack_exist_validation(rack_id, rack_to_update)
        
        rack_validation(rack, session, False)
        Rack.model_validate(rack)

        rack_to_update.name = rack.name.strip()
        rack_to_update.description = rack.description.strip()
        rack_to_update.serial_number = rack.serial_number.strip()
        rack_to_update.unit_capacity = rack.unit_capacity
        rack_to_update.max_power_consumption = rack.max_power_consumption

        session.add(rack_to_update)
        session.commit()
        session.refresh(rack_to_update)
        return rack_to_update
    except ValidationError as e:
        msg: list[str] = [err["msg"] for err in  e.errors()]
        raise HTTPException(
                status_code=422,
                detail={'messages': msg}
            )
    
@router.delete("/{rack_id}")
async def delete_rack(rack_id: int, session: Session = Depends(get_session)):
    rack_to_delete: Rack = session.get(Rack, rack_id)
    rack_exist_validation(rack_id, rack_to_delete)
    session.delete(rack_to_delete)
    session.commit()
    return {"message": f"Rack '{rack_to_delete.name}' deleted successfully"}
