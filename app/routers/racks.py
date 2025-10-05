from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlmodel import Session, select
from app.database import get_session
from app.models import Rack, RackForm, Device

router = APIRouter(prefix="/racks", tags=["racks"])

@router.get("/")
def get_all(session: Session = Depends(get_session)):
    racks = [map_rack_form(rack) for rack in session.exec(select(Rack)).all()]
    return racks

@router.get("/{rack_id}")
def get_single(rack_id: int, session: Session = Depends(get_session)):
    rack = session.get(Rack, rack_id)
    if not rack:
        raise HTTPException(status_code=404, detail=f"Rack with id {rack_id} not found")
    return map_rack_form(rack)

def map_rack_form(rack: Rack):
    return RackForm(
        id = rack.id,
        name = rack.name,
        description = rack.description,
        serial_number = rack.serial_number,
        unit_capacity = rack.unit_capacity,
        max_power_consumption = rack.max_power_consumption,
        power_consuption = sum([d.power_consumption for d in rack.devices])
    )

@router.post("/")
def create_rack(rack: Rack, session: Session = Depends(get_session)):
    try: 
        rack.name = rack.name.strip()
        rack.description = rack.description.strip()
        rack.serial_number = rack.serial_number.strip()

        #unique_serial_number_validation(-1, rack.serial_number, session)
        new_rack = Rack.model_validate(rack)
        rack_validation(rack, session, True)

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
            detail=f"Max power consuption must be positive number."
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
def update_rack(rack_id: int, rack: Rack, session: Session = Depends(get_session)):
    try: 
        rack.id = rack_id
        rack_to_update: Rack = session.get(Rack, rack_id)
        if not rack_to_update:
            raise HTTPException(status_code=404, detail=f"Rack with id {rack_id} not found")
        
        Rack.model_validate(rack)
        rack_validation(rack, session, False)

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
def delete_rack(rack_id: int, session: Session = Depends(get_session)):
    rack_to_delete: Rack = session.get(Rack, rack_id)
    if not rack_to_delete:
        raise HTTPException(status_code=404, detail=f"Rack with id {rack_id} not found")
    session.delete(rack_to_delete)
    session.commit()
    return {"message": f"Rack {rack_to_delete.name} deleted successfully"}