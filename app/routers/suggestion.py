import math
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from app.database import get_session
from app.models import Rack, Device

router = APIRouter(prefix="/suggestion", tags=["suggestion"])

@router.get("/")
async def suggest(
    device_ids: list[int] = Query(default=[]),
    rack_ids: list[int] = Query(default=[]),
    session: Session = Depends(get_session)
    ):
    
    #get racks and sort by consumption
    select_racks = select(Rack).where(Rack.id.in_(rack_ids)).order_by(Rack.max_power_consumption.desc())
    racks_list: list[Rack] = session.exec(select_racks).all()

    #get devices and sort by consumption
    select_devices = select(Device).where(Device.id.in_(device_ids)).order_by(Device.power_consumption.desc())
    devices_list: list[Device] = session.exec(select_devices).all()

    #Test if total unit size or power consumption of devices is larger then the racks 
    #if yes go to early exit and return error message
    rack_max_units = sum([r.unit_capacity for r in racks_list])
    rack_max_pow = sum([r.max_power_consumption for r in racks_list])
    device_max_untis = sum([r.unit_size for r in devices_list])
    device_max_pow = sum([r.power_consumption for r in devices_list])

    if(device_max_untis > rack_max_units):
        raise HTTPException(
                status_code=400,
                detail="Not enough space to store all devices"
            )   
    if(device_max_pow > rack_max_pow):
        raise HTTPException(
                status_code=400,
                detail="Not enough power to store all devices"
            )

    devices_in_racks: list[DevicesInRacks] = []

    capacity_arr: list[int] = [] 
    power_arr: list[int] = []

    #initalize zeros in helper arrays
    for i in range(len(racks_list)):
        capacity_arr.append(0)
        power_arr.append(0)

    for device in devices_list:
        new_rack_pcts: list[int] = []

        for idx, rack in enumerate(racks_list):
            #not enough space or power to store device in rack
            if(capacity_arr[idx] + device.unit_size > rack.unit_capacity):
                new_rack_pcts.append(math.inf) #set max value
                continue;
            if(power_arr[idx] + device.power_consumption > rack.max_power_consumption):
                new_rack_pcts.append(math.inf) #set max value
                continue;

            pct = (power_arr[idx] + device.power_consumption) / rack.max_power_consumption * 100
            new_rack_pcts.append(pct)

        min_pct = min(new_rack_pcts)
        #Check device is added to any rack
        if(min_pct < math.inf):
            store_index = new_rack_pcts.index(min_pct)
            #Check if rack is already added if not add new one
            res = [idx for idx, dr in enumerate(devices_in_racks) if dr.rack.id == racks_list[store_index].id]
            if(len(res) == 0):
                devices_in_racks.append(DevicesInRacks(rack=racks_list[store_index], devices=[device]))
            else:
                devices_in_racks[res[0]].devices.append(device)

            power_arr[store_index] += device.power_consumption
            capacity_arr[store_index] += device.unit_size
        else:
            raise HTTPException(
                status_code=400,
                detail="Not enough space or power to store all devices"
            )

    response: list[SuggestionInfo] = []
    for dir in devices_in_racks:
        si = SuggestionInfo()
        si.rack_id = dir.rack.id
        si.rack_name = dir.rack.name
        si.max_power_consumption = dir.rack.max_power_consumption
        si.power_consumption = sum([d.power_consumption for d in dir.devices])
        si.power_percentage = sum([d.power_consumption for d in dir.devices]) / dir.rack.max_power_consumption * 100
        si.unit_capacity = dir.rack.unit_capacity
        si.unit_size_taken = sum([d.unit_size for d in dir.devices])
        si.size_percentage = sum([d.unit_size for d in dir.devices]) / dir.rack.unit_capacity * 100
        si.device_ids = [d.id for d in dir.devices]
        response.append(si)

    return response

class DevicesInRacks:
    def __init__(self, rack: Rack, devices: list[Device]):
        self.rack = rack
        self.devices = devices

    rack: Rack
    devices: list[Device]

class SuggestionInfo:
    rack_id: int
    rack_name: str
    max_power_consumption: int
    power_consumption: int
    power_percentage: float
    unit_capacity: int
    unit_size_taken: int
    size_percentage: float
    device_ids: list[int]
