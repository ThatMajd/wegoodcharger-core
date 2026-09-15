from exceptions import APIError
from dataclasses import dataclass
from enum import Enum

class HTTPStatus(Enum):
    SUCCESS = 200
    UNAUTHORIZED = 401

@dataclass
class ChargerDeviceStatus:
    # Port Detail
    port_status: int
    power_kw: int
    elect_kwh: int
    time: int
    voltage: int
    charger_temp: float
    wire_temp: float
    
    # Mainboard Config (raw API values)
    max_power: int
    max_current: int
    
    @classmethod
    def parse_from_status(cls, status):
        """Build a status object from the decoded API response dictionary."""
        try:
            port = status["PortDetail"]
            mainboard = status["MainboardConfig"]
            return cls(
                port_status=int(port["port_first_status"]),
                power_kw=float(port["power"]) / 1000,
                elect_kwh=float(port["elec"]) / 100,
                time=int(port["time"]),
                voltage=float(port["voltage"]),
                charger_temp=float(port["dev_temper"]),
                wire_temp=float(port["wire_temper"]),
                max_power=int(mainboard["max_power"]),
                max_current=int(mainboard["max_current"]),
            )
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise APIError(
                "Status response contains missing or invalid fields in PortDetail or MainboardConfig."
            ) from exc


