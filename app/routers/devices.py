from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlmodel import Session, select
from app.database import get_session
from app.models import DeviceForm, Device, Rack, AddDeviceForm
from app.routers.validation_helper import device_exist_validation, rack_exist_validation

router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/")
async def get_all(session: Session = Depends(get_session)):
    racks = [map_device_form(d) for d in session.exec(select(Device)).all()]
    return racks

@router.get("/{device_id}")
async def get_single(device_id: int, session: Session = Depends(get_session)):
    device: Device = session.get(Device, device_id)
    device_exist_validation(device_id, device)
    return map_device_form(device)

def map_device_form(device: Device):
    return DeviceForm(
        id = device.id,
        name = device.name,
        description = device.description,
        serial_number = device.serial_number,
        unit_size = device.unit_size,
        power_consumption = device.power_consumption,
        rack_id = device.rack_id,
        rack_name = device.rack.name if device.rack is not None else "None" 
    )

@router.post("/")
async def create_device(device: Device, session: Session = Depends(get_session)):
    try: 
        device.name = device.name.strip()
        device.description = device.description.strip()
        device.serial_number = device.serial_number.strip()

        device_validation(device, session, True)
        Device.model_validate(device)

        session.add(device)
        session.commit()
        session.refresh(device)
        return device
    except ValidationError as e:
        msg: list[str] = [err["msg"] for err in  e.errors()]
        raise HTTPException(
                status_code=422,
                detail={'messages': msg}
            )

def device_validation(device: Device, session: Session, create_mod: bool):
    #Check if Device with this id already exist, only check if it is creation, not update of device
    if device.id is not None:
        if device.id < 1:
            raise HTTPException(
                    status_code=400,
                    detail=f"Device id must be positive number."
                )
        
        if create_mod:
            if(session.get(Device, device.id) is not None):
                raise HTTPException(
                    status_code=400,
                    detail=f"Device with id '{device.id}' already exists."
            )
    if(device.unit_size < 1):
        raise HTTPException(
            status_code=400,
            detail=f"Unit capacity must be positive number."
        )
    
    if(device.power_consumption < 1):
        raise HTTPException(
            status_code=400,
            detail=f"Power consuption must be positive number."
        )
    
    if(device.rack_id is not None):
        rack: Rack = session.get(Rack, device.rack_id)
        rack_exist_validation(device.rack_id, rack)
        power_consumption_validation(create_mod, rack, device)
        unit_size_validation(create_mod, rack, device)

    id_to_check = device.id if not create_mod else -1
    unique_serial_number_validation(id_to_check, device.serial_number, session)

def power_consumption_validation(create_mod: bool, rack: Rack, device: Device):
    #if it is update mod then we dont want to take into considaration current device
    total_consumption: int
    if(create_mod):
        total_consumption = sum([d.power_consumption for d in rack.devices])
    else:
        total_consumption = sum([d.power_consumption for d in rack.devices if d.id != device.id])

    if(total_consumption + device.power_consumption > rack.max_power_consumption):
        raise HTTPException(
            status_code=400,
            detail=f"Power consumption exceeds maximum allowed value in the current rack."
        )

def unit_size_validation(create_mod: bool, rack: Rack, device: Device):
    total_unit_size: int
    if(create_mod):
        total_unit_size: int = sum([d.unit_size for d in rack.devices])
    else:
        total_unit_size: int = sum([d.unit_size for d in rack.devices if d.id != device.id])
    
    if(total_unit_size + device.unit_size > rack.unit_capacity):
        raise HTTPException(
            status_code=400,
            detail=f"There is not enough space in rack to store this device."
        )
    
def unique_serial_number_validation(current_id: int, value: str, session: Session): 
    select_rack = select(Rack.id).where(Rack.serial_number == value)
    rack = session.exec(select_rack).first()
    select_device = select(Device.id).where(Device.serial_number == value).where(Device.id != current_id)
    device = session.exec(select_device).first()
    if device is not None or rack is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Serial number '{value}' already exists."
        )
    return

@router.put("/{device_id}")
async def update_device(device_id: int, device: Device, session: Session = Depends(get_session)):
    try: 
        device.id = device_id
        device_to_update: Device = session.get(Device, device_id)
        device_exist_validation(device_id, device_to_update)
        
        device_validation(device, session, False)
        Device.model_validate(device)

        device_to_update.name = device.name.strip()
        device_to_update.description = device.description.strip()
        device_to_update.serial_number = device.serial_number.strip()
        device_to_update.unit_size = device.unit_size
        device_to_update.power_consumption = device.power_consumption
        device_to_update.rack_id = device.rack_id

        session.add(device_to_update)
        session.commit()
        session.refresh(device_to_update)
        return device_to_update
    except ValidationError as e:
        msg: list[str] = [err["msg"] for err in  e.errors()]
        raise HTTPException(
                status_code=422,
                detail={'messages': msg}
            )
    
@router.delete("/{device_id}")
async def delete_device(device_id: int, session: Session = Depends(get_session)):
    device_to_delete: Device = session.get(Device, device_id)
    device_exist_validation(device_id, device_to_delete)
    session.delete(device_to_delete)
    session.commit()
    return {"message": f"Device '{device_to_delete.name}' deleted successfully"}

@router.post("/add_to_rack")
async def add_device_to_rack(form: AddDeviceForm, session: Session = Depends(get_session)):
    rack = session.get(Rack, form.rack_id)
    rack_exist_validation(form.rack_id, rack)
    device = session.get(Device, form.device_id)
    device_exist_validation(form.device_id, device)
    
    if device.rack_id == rack.id:
        return {"message": "Device is already added to this rack"}
    
    power_consumption_validation(True, rack, device)
    unit_size_validation(True, rack, device)

    device.rack_id = rack.id
    session.add(device)
    session.commit()
    session.refresh(device)
    return {"message": f"Device '{device.name}' is added to rack '{rack.name}'"}

@router.post("/remove_from_rack")
async def remove_device_from_rack(form: AddDeviceForm, session: Session = Depends(get_session)):
    rack = session.get(Rack, form.rack_id)
    rack_exist_validation(form.rack_id, rack)
    device = session.get(Device, form.device_id)
    device_exist_validation(form.device_id, device)
    
    if device.rack_id != rack.id:
        return {"message": "Device is already removed from this rack"}

    device.rack_id = None
    session.add(device)
    session.commit()
    session.refresh(device)
    return {"message": f"Device '{device.name}' is removed to rack '{rack.name}'"}
