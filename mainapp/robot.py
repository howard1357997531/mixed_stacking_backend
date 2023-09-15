import socket
import time
import pandas as pd
import csv
from django.conf import settings
import os

##########################################################################
class robot_control():
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_control(self,data_packet):
        self.client_socket.sendto(data_packet, (self.server_ip, self.server_port))
        response, addr = self.client_socket.recvfrom(1024)
        return response

    def send_command(self, control_input):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 10 00 00 " + control_input.replace(" ", ""))
        response = self.send_control(data_packet) 
        RES = str('5945524320000000030101010000008039393939393939398200000000000000')
        if response.hex() == RES:
            print('fail')
        else:
            print('success')


    def reset(self):
        self.send_command('00')
        self.send_command('25')
        self.send_command('00')
    
    def servo(self):
        self.send_command('01')
        self.send_command('05')
        

    def start(self):
        self.send_command('15')

    def pause(self):
        self.send_command('07')
        self.send_command('05')

    def close(self):
        self.client_socket.close()
        print("Connection closed.")

##########################################################################
def decimal_to_hex(decimal): #傳進來的數值
        hex_string = hex(decimal & 0xFFFFFFFF)[2:]  
        hex_padded = hex_string.zfill(8)
        hex_reversed = hex_padded[6:8] + hex_padded[4:6] + hex_padded[2:4] + hex_padded[0:2]
        hex_formatted = ' '.join(hex_reversed[i:i+2] for i in range(0, len(hex_reversed), 2))
        return hex_formatted

def speed(D_data):
    robot=robot_control('192.168.1.15',10040)
    D_data=D_data*50
    D_data_hex= decimal_to_hex(D_data)
    data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 01 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
    robot.send_control(data_packet)
    return D_data 

#不斷讀取重製時'00'break全部迴圈   
def request_2701():
    robot=robot_control('192.168.1.15',10040)
    data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 78 00 8D 0A 01 0E 00 00 00" )
    response=robot.send_control(data_packet)
    response_R = response.hex()
    #print(f"Received response from MOTOMAN robot: {response.hex()}")
    return response_R 

def userbase(D_data):
        robot=robot_control('192.168.1.15',10040)
        D_data_hex= decimal_to_hex(D_data)
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 04 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 10 00 01 02 00 00  " + D_data_hex.replace(" ", ""))
        robot.send_control(data_packet)
        return D_data
   
##########################################################################
def main(id, list_count):
        robot = robot_control('192.168.1.15',10040)
        robot.reset()
        robot.servo()
        robot.start()
    
        file = os.path.join(settings.MEDIA_ROOT, f'Figures_{id}', 'box_positions_conveyor.csv')
        file2 = os.path.join(settings.MEDIA_ROOT, f'Figures_{id}', 'box_positions_final.csv')

        Supply = pd.read_csv(file)
        Place = pd.read_csv(file2)
        Supply_columns = Supply[['pos_x', 'pos_y', 'pos_z']]
        Place_columns = Place[['bin_name','X_cog', 'Y_cog', 'Z_cog','orientation']]
        #print(Supply_columns )
        #print(Place_columns )  
        catch_list = []
        put_list = []
        put_base=[] 
        posture1=[180.0,0.0,0.0]
        posture2=[180.0,0.0,90.0]
        for index, row in Supply_columns.iterrows():
            supply_initial = row.to_list()
            supply_data=supply_initial+posture1
            catch_list.append(supply_data)
        for index, row in Place_columns.iterrows():
            place_initial = row.to_list()
            if  place_initial[4] == 1.0:
                place_data=place_initial[1:4]+posture2
            else :
                place_data=place_initial[1:4]+posture1    
            put_list.append(place_data)
            put_base.append(place_initial[0])
        #print(put_list)
        print("putbase:", put_base)
        count=1
        for catch_input, put_input, putbase_input in zip(catch_list, put_list, put_base):
                #print(catch_pos)
                #print(put_pos)
                while True:
                    if request_2701().endswith("00"):
                        break
                    #-----------------
                    name = Supply['matched_box_name'].tolist()
                    name = [i.replace("#", "").replace("外箱", "") for i in name]
                    txt_path = os.path.join(settings.MEDIA_ROOT, "output.txt")
                    with open(txt_path, 'w', encoding='utf-8') as t:
                        t.write(f'{count},準備抓取第{count}個物件,{name[count-1]},prepare,{int(putbase_input)}')
                    #-----------------
                    print('catch第%d次'%(count))
                    result=send_data(1,catch_input)
                    if result==(True,True):
                        break
                while True:
                    if request_2701().endswith("00"):
                        break
                    #-----------------
                    name = Supply['matched_box_name'].tolist()
                    name = [i.replace("#", "").replace("外箱", "") for i in name]
                    txt_path = os.path.join(settings.MEDIA_ROOT, "output.txt")
                    with open(txt_path, 'w', encoding='utf-8') as t:
                        t.write(f'{count},正在操作第{count}個物件,{name[count-1]},operate,{int(putbase_input)}')
                    #-----------------
                    print('put第%d次'%(count))
                    if  putbase_input==1.0:
                        print('pallet2')
                        userbase(3)
                    else:
                        print('pallet3')
                        userbase(4)
                    result=send_data(2,put_input)
                    if result==(True,True):
                        count+=1
                        break
                   
                if count==int(list_count + 1) or request_2701().endswith("00"):
                    print("list_count(inner):", list_count)
                    if request_2701().endswith("00"):
                        print('系統重製')
                    else:
                        print("count(inner):",count)
                        home_input=[0, 0, 0, 0, 0, 0]
                        result=send_data(3,home_input)
                    break

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.close()
        robot.pause()
        robot.reset()
        print("Connection closed.")   
            
##########################################################################
def send_data(case, D_data):

    robot=robot_control('192.168.1.15',10040)

    def decimal_to_hex(decimal): #傳進來的數值
        hex_string = hex(decimal & 0xFFFFFFFF)[2:]  
        hex_padded = hex_string.zfill(8)
        hex_reversed = hex_padded[6:8] + hex_padded[4:6] + hex_padded[2:4] + hex_padded[0:2]
        hex_formatted = ' '.join(hex_reversed[i:i+2] for i in range(0, len(hex_reversed), 2))
        return hex_formatted
    
    #D格式資料處理+傳送
    def data_pos():
        for position, value in data_D.items():
            if position in ['case']:
                decimal_value = int(value * 1)
            elif position in ['X', 'Y', 'Z']:
                decimal_value = int(value * 1000)
            else:
                decimal_value = int(value * 10000)
            hex_value = decimal_to_hex(decimal_value)
            #print(hex_value)

            Datalengh_mapping = {'case': '04','X': '04','Y': '04','Z': '04','A': '04','B': '04','C': '04'}#資料長度
            position_mapping = {'case': '12','X': '04','Y': '05','Z': '06','A': '07','B': '08','C': '09'}#座標編號
            Write_mapping = '02'

            data_packet = bytes.fromhex(f"59 45 52 43 20 00 {Datalengh_mapping[position]} 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 {position_mapping[position]} 00 01 {Write_mapping}  00 00 " + hex_value.replace(" ", ""))
            robot.send_control(data_packet)
            #print(f"Received response from MOTOMAN robot: {response.hex()}")

    #放置點資料處理+傳送
    '''        
    def put_send():

        for position, value in put_pos.items():
            if position in ['case']:
                decimal_value = int(value * 1)
            elif position in ['X', 'Y', 'Z']:
                decimal_value = int(value * 1000)
            else:
                decimal_value = int(value * 10000)
            hex_value = decimal_to_hex(decimal_value)
            #print(hex_value)

            Datalengh_mapping = {'case': '04','X': '04','Y': '04','Z': '04','A': '04','B': '04','C': '04'}#資料長度
            position_mapping = {'case': '12','X': '0a','Y': '0b','Z': '0c','A': '0d','B': '0e','C': '0f'}#座標編號
            Write_mapping = '02'

            data_packet = bytes.fromhex(f"59 45 52 43 20 00 {Datalengh_mapping[position]} 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7C 00 {position_mapping[position]} 00 01 {Write_mapping}  00 00 " + hex_value.replace(" ", ""))
            client_socket.sendto(data_packet, (server_ip, server_port))
            response, addr = client_socket.recvfrom(1024)
            '''        
   
    def Loadcoord(a):
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 08 00 01 02 00 00  " + B_data_input.replace(" ", ""))
        robot.send_control(data_packet)
        return a
    
    def request_B8():
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 08 00 01 0E 00 00 00" )
        response=robot.send_control(data_packet)
        response_R = response.hex()
        return response_R
    
    def request_B100():
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 64 00 01 0E 00 00 00" )
        response=robot.send_control(data_packet)
        response_R = response.hex()
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        return response_R
    
    def request_B103():
        data_packet = bytes.fromhex(f"59 45 52 43 20 00 01 00 03 01 00 01 00 00 00 00 39 39 39 39 39 39 39 39 7A 00 67 00 01 0E 00 00 00" )
        response=robot.send_control(data_packet)
        response_R = response.hex()
        #print(f"Received response from MOTOMAN robot: {response.hex()}")
        return response_R
    
    def fail():
        return False
    
    def success():
        return True 
    
    
    while True:
        if request_B103().endswith("01"):
            print('回到起始位')
            break
           
    print(D_data)
    data_D={'case':case,'X':D_data[0],'Y':D_data[1],'Z':D_data[2],'A':D_data[3],'B':D_data[4],'C':D_data[5]}
    data_pos()
    B_data_input = '01' #傳送座標
    Loadcoord(B_data_input)
    B8=0
    B100=0

    #response_B8=request_B8()
    if request_B8().endswith("01"):
        B8=success()
        print('Send_data success')
    else:
        print('Send_data fail')
        B8=fail()
        B100=fail()

    while B8==success():
        if request_2701().endswith("00"):
            print('STOP1')
            break
        if request_B8().endswith("01"):
           B8=success()       
        if request_B100().endswith("01"):
            print('Robot recieve_data success')
            while True:
                if request_B100().endswith("00"):
                    B100=success()
                    print('Robot action finish')
                    request_B8()
                    break
                if request_2701().endswith("00"):
                    print('STOP2')
                    break
              
        if request_B8().endswith("00"):
            B8=fail()
            B100=fail()
            print('Send_data fail')
            break

        if request_2701().endswith("00"):
            print('STOP3')
            break

        if B100==success() and B8==success():
            print('Send_data next time')
            break  
            
    return (B8,B100)
                    