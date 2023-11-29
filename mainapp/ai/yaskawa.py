import socket
class Yaskawa_control():
    def decimal_to_hex(decimal): 
        hex_string = hex(decimal & 0xFFFFFFFF)[2:]  
        hex_padded = hex_string.zfill(8)
        hex_reversed = hex_padded[6:8] + hex_padded[4:6] + hex_padded[2:4] + hex_padded[0:2]
        hex_formatted = ' '.join(hex_reversed[i:i+2] for i in range(0, len(hex_reversed), 2))
        return hex_formatted
    
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_control(self,data_packet):
        self.client_socket.sendto(data_packet, (self.server_ip, self.server_port))
        response, addr = self.client_socket.recvfrom(1024)
        return response
    
    def request_sensor11(self):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 D4 07 01 0E 00 00 00" )
        response=self.send_control(data_packet)
        response_R = response.hex()
        signal_hex = response_R[-2:]
        signal_int = int(signal_hex, 16)
        signal_binary = bin(signal_int)[2:].zfill(8) 
        if signal_binary[-3] == '1':
            status=True
        else:
            status=False
        return status

   
# robot=Yaskawa_control('192.168.1.15',10040)
# while True:
#     robot.request_sensor11() ####不斷偵測物體
#     if robot.request_sensor11():
#         print('start camera')
#         while True:
#             #camera finish break
#             print(' camera finish')

