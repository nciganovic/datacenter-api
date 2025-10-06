from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}

def test_suggestion_1():
    client.params
    response = client.get("/suggestion", params={"device_ids": [4, 5, 6, 7], "rack_ids": [3, 4, 5]})
    assert response.status_code == 200
    assert response.json()[0]["max_power_consumption"] == 1200
    assert response.json()[0]["power_consumption"] == 600
    assert response.json()[0]["power_percentage"] == 50.0
    assert response.json()[0]["unit_capacity"] == 8
    assert response.json()[0]["unit_size_taken"] == 4
    assert response.json()[0]["size_percentage"] == 50.0
    assert response.json()[0]["device_ids"] == [4, 7]

    assert response.json()[1]["max_power_consumption"] == 1100
    assert response.json()[1]["power_consumption"] == 400
    assert response.json()[1]["power_percentage"] == 36.36363636363637
    assert response.json()[1]["unit_capacity"] == 8
    assert response.json()[1]["unit_size_taken"] == 2
    assert response.json()[1]["size_percentage"] == 25.0
    assert response.json()[1]["device_ids"] == [5]

    assert response.json()[2]["max_power_consumption"] == 1000
    assert response.json()[2]["power_consumption"] == 300
    assert response.json()[2]["power_percentage"] == 30.0
    assert response.json()[2]["unit_capacity"] == 8
    assert response.json()[2]["unit_size_taken"] == 2
    assert response.json()[1]["size_percentage"] == 25.0
    assert response.json()[2]["device_ids"] == [6]

#Simulating power issue
def test_suggestion_2():
    response = client.get("/suggestion", params={"device_ids": [8, 9, 10], "rack_ids": [3, 4]})
    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough power to store all devices"

#Test case when racks and imbalanced
#First Rack is full on space so other two are taking over
#Probably better balance would be achieved if 700 was stored on third Rack increasing his power and lowered second one
def test_suggestion_3():
    response = client.get("/suggestion", params={
        "device_ids": [9, 10, 11, 12, 13, 14, 15, 16, 17, 18], 
        "rack_ids": [6, 7, 8]})
    assert response.status_code == 200
    assert response.json()[0]["max_power_consumption"] == 10000
    assert response.json()[0]["power_consumption"] == 2600
    assert response.json()[0]["power_percentage"] == 26.0
    assert response.json()[0]["unit_capacity"] == 6
    assert response.json()[0]["unit_size_taken"] == 6
    assert response.json()[0]["size_percentage"] == 100.0
    assert response.json()[0]["device_ids"] == [9, 11, 12]

    assert response.json()[1]["max_power_consumption"] == 5000
    assert response.json()[1]["power_consumption"] == 3900
    assert response.json()[1]["power_percentage"] == 78.0
    assert response.json()[1]["unit_capacity"] == 10
    assert response.json()[1]["unit_size_taken"] == 7
    assert response.json()[1]["size_percentage"] == 70.0
    assert response.json()[1]["device_ids"] == [10, 13, 14, 15, 17, 18]

    assert response.json()[2]["max_power_consumption"] == 1000
    assert response.json()[2]["power_consumption"] == 600
    assert response.json()[2]["power_percentage"] == 60.0
    assert response.json()[2]["unit_capacity"] == 4
    assert response.json()[2]["unit_size_taken"] == 1
    assert response.json()[2]["size_percentage"] == 25.0
    assert response.json()[2]["device_ids"] == [16]
