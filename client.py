from network import request, build_headers
from exceptions import FeatureNotImplementedError, APIError
import websocket
import json
import time
from getpass import getpass

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
        
        if not token:
            email = input("Email: ")
            password = getpass("Pass: ")
            self.login(email, password)
        
        self.get_device()
        
    
    def login(self, email, password):
        response = request(
            "POST",
            f"{DEFAULT_BASE_URL}/mailLogin",
            json={"username": email, "password": password},
        )
        print("Logged in")
        self.token = str(response.json()["token"])
    
    def get_info(self):
        """Returns user telemtry not needed for implementations"""
        response = request(
            "GET",
            f"{DEFAULT_BASE_URL}/getInfo",
            headers = build_headers(self.token)
        )
        return response.json()

    def get_device(self):
        response = request(
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
            'lastOnline': device["heartTime"]
        }
        return self.device_payload
        

    def status(self):
        
        detail_visit_time = self._sendPortDetailCmd()
        mainboard_visit_time = self._sendMainboardCmd()

        wsocket_url = WS_URL(self.device_payload["ccid"], self.token)
        socket = websocket.create_connection(wsocket_url, timeout=10)

        status = {
            "PortDetail": self._getPortDetail(detail_visit_time),
            "MainboardConfig": self._getMainboardConfig(mainboard_visit_time),
            "WebSocket": socket.recv()
        }
        
        socket.close()
        
        return json.dumps(status, indent=4)
    
    def _sendPortDetailCmd(self):
        response = request(
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
            response = request(
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
        response = request(
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
            response = request(
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

   
