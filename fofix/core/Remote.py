from socket import socket, AF_INET, SOCK_DGRAM
from fofix.core import Config
import threading
import time
import jsonpickle

class Remote():
    diagnostics = None
    connection = None
    pending = []
    storage = {
        "connection": {
            "ip": None,
            "port": None,
            "type": None
        },
        "client": {
            "acks": []
        },
        "server": {
            "frame_id": 0,
            "frame_time": 0,
            "current_time": int(time.time()*1000.0),
            #"previous": None
        }
    }
    def _it_(self):
        self.config  = Config.load()
        self.type = self.config.get("video", "remote")
        self.ip = self.config.get("video", "remote_ip")
        self.port = self.config.get("video", "remote_port")

        Remote.storage["connection"]["type"] = self.type
        Remote.storage["connection"]["ip"] = self.ip
        Remote.storage["connection"]["port"] = self.port
        if (Remote.connection != None):
            if (self.get_type() > 0):
                Remote.connection = socket(AF_INET, SOCK_DGRAM)
            if (self.get_type() == 2):
                Remote.connection.bind((self.ip, self.port))

    def create_diag(self): 
        Remote.diagnostics = open("multi-shared.csv", "w")
        Remote.diagnostics.write(",".join(['Frames per Second', 'Frame Time', 'Frame Broadcast Delay']) + "\n")
    
    def write_diag(self, data):
        Remote.diagnostics.write(data)
        print('data written: ' + str(data));

    def get_type(self):
        return Remote.storage["connection"]["type"]

    def build_timestamp(self):
        return int(time.time()*1000.0)
    
    def build_send_payload(self, layer):
        current = self.build_timestamp()
        frame_time = int(current - Remote.storage["server"]["current_time"])
        payload = {
            "frame_id": Remote.storage["server"]["frame_id"],
            "frame_time": frame_time,
            "current_time": current,
            #"previous": Remote.storage["server"]["previous"],
            "current": layer
        }
        Remote.storage["server"]["frame_id"] += 1
        Remote.storage["server"]["frame_time"] = frame_time
        Remote.storage["server"]["current_time"] = current
        #Remote.storage["server"]["previous"] = layer
        if (Remote.diagnostics == None):
            self.create_diag()
            threading.Thread(target=self.send_payload, args=()).start()
       
        Remote.pending.append(payload)
    
    def send_payload(self):
        ip = Remote.storage["connection"]["ip"]
        port = Remote.storage["connection"]["port"]
        while True:
            while (len(Remote.pending) > 0):
                payload = Remote.pending.pop(0)
                pickled = jsonpickle.encode(payload)
                diff = self.build_timestamp() - payload['current_time']
                frame_time = payload['frame_time']
                if (frame_time == 0):
                    frame_time = 1
                fps = int(1000 / frame_time)
                self.write_diag(",".join([str(fps), str(payload['frame_time']), str(diff)]) + "\n")
                #Remote.connection.sendto(jsonpickle(payload), ip, port)

    def send_frame(self, layer):
        if(True or self.get_type() == 2):
            self.build_send_payload(layer)
