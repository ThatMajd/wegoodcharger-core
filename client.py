from exceptions import FeatureNotImplementedError, APIError
import websocket
from getpass import getpass
import json
import time

from network import request_raw, build_headers
from models import ChargerDeviceStatus, HTTPStatus

DEFAULT_BASE_URL = "https://ev.weguyun.com"
WS_URL = lambda deviceId, token: f"wss://ev.weguyun.com/websocket/{deviceId}/{token}"

class CloudClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: str = ""
    ):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.device_payload = dict()
        self.charger_device_status = None
        
        if not self.token:
            self.login()
        
        
        self.get_device()
        
    def _request(self, method: str, url: str, **kwargs):
        """Cloud server always returns status 200, but the actual status is returned in the body of the response"""
        # Regular HTTP errors will be caught by the raw method
        response = request_raw(method=method, url=url, **kwargs)
        
        # Cloud responses are handled here
        status = response.json()["code"]
        
        if status == HTTPStatus.UNAUTHORIZED.value:
            print("Session expired, please login again to refresh token")
            print(f"WARNING: {method} {url}")
            
            self.login()
            kwargs["headers"] = build_headers(self.token)
            
            return self._request(method, url, **kwargs)
            
        elif status == HTTPStatus.SUCCESS.value:
            if "msg" in response.json():
                # Visit requests
                return response
            
            if "data" not in response.json():
                print(f'WARNING: {url} returned no data, either parameters are missing or a physical condition (like charger not plugged in) is not met')
            return response
        else:
            raise APIError(f'Server returned unexpected error {status}')
        
    
    def login(self):
        # TODO handle incorrect credintials
        
        email = input("Email: ")
        password = getpass("Pass: ")
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/mailLogin",
            json={"username": email, "password": password},
        )
        self.token = str(response.json()["token"])
        
        print("Logged in")
    
    
    def get_info(self):
        """Returns user telemtry not needed for implementations"""
        response = self._request(
            "GET",
            f"{DEFAULT_BASE_URL}/getInfo",
            headers = build_headers(token=self.token)
        )
        return response.json()
    
    def is_online(self):
        return self.device_payload["isOnline"]

    def get_device(self):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/device/deviceList",
            headers = build_headers(self.token)
        )
        num_devices = len(response.json()["data"])
    
        if num_devices > 1:
            raise FeatureNotImplementedError("Multiple devices aren't supported yet.")
        elif num_devices == 0:
            raise APIError("Expected device data, but the API returned none. Check if you registered a device")
        
        device = response.json()["data"][0]
        
        self.device_payload = {
            'deviceId': device["deviceId"],
            'ccid': device["ccid"],
            'qrcode': device["qrcode"],
            'createTime': device["createTime"],
            'lastOnline': device["heartTime"],
            'isOnline': device["status"] == 1
        }
        
        if not self.device_payload["isOnline"]:
            print(f"Device {self.device_payload['deviceId']} is offline, last seen {self.device_payload['lastOnline']} (China/Server time)")
        
        return self.device_payload
        
    def charge_records(self, page_num: int = 1, page_size: int = 6):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/chargeRecord/list?&pageNum={page_num}&pageSize={page_size}",
            headers = build_headers(self.token),
            json = {
                "pageNum": page_num,
                "pageSize": page_size,
                "reasonable": True,
            }
        )
        return response.json()

    def restart_mainboard(self):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/device/restartMainboard",
            headers = build_headers(self.token),
            json = {
                "deviceId": self.device_payload["ccid"],
                "ccid": self.device_payload["ccid"],
                "qrcode": self.device_payload["qrcode"],
            }
        )
        return response.json()

    def status(self, print_extended_status=False):
        if not self.is_online():
            # TODO Return proper status
            print("Device Offline!")
            return
        
        detail_visit_time = self._sendPortDetailCmd()
        mainboard_visit_time = self._sendMainboardCmd()

        wsocket_url = WS_URL(self.device_payload["ccid"], self.token)
        socket = websocket.create_connection(wsocket_url, timeout=10)

        time.sleep(1)
        
        status = {
            "PortDetail": self._getPortDetail(detail_visit_time).get("data", {}),
            "MainboardConfig": self._getMainboardConfig(mainboard_visit_time).get("data", {}),
            "WebSocket": json.loads(socket.recv())
        }
        
        socket.close()
        
        self.charger_device_status = status
        return json.dumps(status, indent=4)
        
        if print_extended_status:
            print(json.dumps(status, indent=4))
        
        print("Check for additional stats during chargetime")
        self.charger_device_status = ChargerDeviceStatus.parse_from_status(status)
        
        return self.charger_device_status

    
    def _sendPortDetailCmd(self):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/device/sendPortDetailCmd",
            headers = build_headers(self.token),
            json = {
                "deviceId": self.device_payload["ccid"],
                "ccid": self.device_payload["ccid"],
                "qrcode": self.device_payload["qrcode"],
            }
        )
        return response.json()['msg']
    
    def _sendMainboardCmd(self):
            response = self._request(
                "POST",
                f"{DEFAULT_BASE_URL}/device/sendMainboardCmd",
                headers = build_headers(self.token),
                json = {
                    "deviceId": self.device_payload["ccid"],
                    "ccid": self.device_payload["ccid"],
                    "qrcode": self.device_payload["qrcode"],
                }
            )
            return response.json()['msg']
    
    def _getPortDetail(self, visit_time):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/device/getPortDetail",
            headers = build_headers(self.token),
            json = {
                "time": visit_time,
                "deviceId": self.device_payload["ccid"],
                "ccid": self.device_payload["ccid"],
                "qrcode": self.device_payload["qrcode"],
            }
        )
        return response.json()

    def _getMainboardConfig(self, visit_time):
        response = self._request(
            "POST",
            f"{DEFAULT_BASE_URL}/device/getMainboardConfig",
            headers = build_headers(self.token),
            json = {
                "time": visit_time,
                "deviceId": self.device_payload["ccid"],
                "ccid": self.device_payload["ccid"],
                "qrcode": self.device_payload["qrcode"],
            }
        )
        return response.json()

   
