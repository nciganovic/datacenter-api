from fastapi import HTTPException
from app.models import Device, Rack


def rack_exist_validation(rack_id: int, rack: Rack):
    if(rack is None):
        raise HTTPException(
            status_code=404, 
            detail=f"Rack with id {rack_id} does not exist"
        )
    
def device_exist_validation(device_id: int, device: Device):
    if device is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Device with id {device_id} does not exist"
        )