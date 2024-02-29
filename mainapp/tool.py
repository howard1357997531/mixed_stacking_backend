a = ["1", "1", "1", "1", "1_insert", "1_insert", "1_insert", "2", "1", "2_insert"]
# a = ["1", "1", "2", "1_insert", "1_insert", "2_insert", "2", "3", "3", "3","2_insert"]
a = ["1_insert", "1_insert", "1", "1", "2", "2_insert", "1_insert", "1_insert", "2", "3", "3", "3","2_insert"]

# reset_index_org = [2, 8 , 10]

def parse_execution_data(data, reset_index_org):
    datas = []
    insert_index = []
    reset_index = []
    data_temp = None
    insert_temp = None
    count = -1
    reset_index_count = 0
    for i in data:
        count_in_reset_index = reset_index_count in reset_index_org
        if i.endswith('_insert'):
            # 一開始進來 insert_temp 必為 none，先走 else 
            # insert_temp 為上一個插單 id
            # 每次進來都會 data_temp = None
            data_temp = None
            insert_num = i.replace('_insert', '')
            if insert_temp and not count_in_reset_index:
                if insert_num == insert_temp:
                    if '*' in datas[count]:
                        num = datas[count].split('*')[0]
                        times = int(datas[count].split('*')[1]) + 1
                        datas[count] = num + '*' + str(times)
                    else:
                        datas[count] = datas[count] + '*' + '2'
                else:
                    count += 1
                    datas.append(insert_num)
                    insert_index.append(count)
                insert_temp = insert_num
            else:
                count += 1
                datas.append(insert_num)
                insert_index.append(count)
                # 如果 count_in_reset_index = False 才會改變 insert_temp
                if count_in_reset_index:
                    insert_temp = None
                    reset_index.append(count)
                else:
                    insert_temp = insert_num
        else:
            # 一開始進來 data_temp 必為 none，先走 else 
            # data_temp 為上一個非插單 id
            # 每次進來都會 insert_temp = None
            insert_temp = None
            if data_temp and not count_in_reset_index:
                if i == data_temp:
                    if '*' in datas[count]:
                        num = datas[count].split('*')[0]
                        times = int(datas[count].split('*')[1]) + 1
                        datas[count] = num + '*' + str(times)
                    else:
                        datas[count] = datas[count] + '*' + '2'
                else:
                    count += 1
                    datas.append(i)
                data_temp = i
            else:
                count += 1
                datas.append(i)
                # 如果 count_in_reset_index = False 才會改變 data_temp
                if count_in_reset_index:
                    data_temp = None
                    reset_index.append(count)
                else:
                    data_temp = i
        reset_index_count += 1
    
    return datas, insert_index, reset_index

import random
import time
from copy import deepcopy
from channels.layers import get_channel_layer
from web_socket.consumers import RobotControlConsumers
from asgiref.sync import async_to_sync

channel_layer = get_channel_layer()

def websocket_robot_state(state):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'robot_mode_change',
            'mode': state
        }
    )

def websocket_object_count(count):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'object_count_change',
            'count': count
        }
    )

def websocket_object_name(name, nextName):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'object_name_change',
            'name': name,
            'nextName': nextName,
        }
    )

def websocket_visual_result(visual_result, count, buffer_order=None, check_numberlist=None):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {
            'type': 'visual_result_change',
            'visual_result': visual_result,  #當前照到的 ['#18', '#9']
            'visual_count': count,           #正要做第幾個正確物件(+1條件為做正確物件時手臂到最高點時)
            'buffer_order': buffer_order,    #buffer區相對位置各個物件數量 [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
            'check_numberlist': check_numberlist, # 手臂執行序 [2, 1] 1:輸送帶到堆棧、2:輸送帶到buffer、3:buffer到輸送帶
        }
    )

def websocket_buffer(bufferquanlity):
    return async_to_sync(channel_layer.group_send)(
        'count_room',
        {   
            'type': 'visual_buffer_change',
            "bufferquanlity": bufferquanlity   # 
        }
    )

class RobotTest():
    def __init__(self):
        self.call_reset = False
        self.order_count = 0
        self.checknumberlist = []
        self.buffer_order = []
        self.box_id_checked = []
        self.buffer_name = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
        self.checked_quanlity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
         
        self.camera_update_count = 1
        self.detect_count = 1

    def check_has_three(self, datas):
        temp = []
        for data in datas:
            temp.append(data)
            if data == 3:
                temp.append(2)
        return temp
    
    def robot_reset(self):
        self.call_reset = True
        
    def supply_check(self, order_data):
        self.call_reset = False
        self.order_count = 0
        self.checknumberlist = []
        self.buffer_order = []
        self.box_id_checked = []
        self.check = checknumberlist()
        self.camera_update_count = 1
        self.detect_count = 1
        # orders = '7A,35,22,29,13,13,35,33,29,16A,13,18A,9,33,29,20,22,20,7A,33,29,9,22,20,26,7A,33,13,18A,26,18A,16A,18A'
        # orders = '7A,35,22,29,13,13,35,33,29'
        # self.orders = orders.split(',')
        self.orders = deepcopy(order_data)
        self.order_length = len(order_data)
        count = 1
        correct_count = 1
        
        for order in order_data:
            while True:
                # temp = random.sample(self.buffer_name, 2)
                # temp.append(self.orders[count - 1])
                temp = random.sample(self.buffer_name, 1)
                temp = random.choice(temp)
        
                correct_count += 1
                # correct_count == 4: 第三次比對結果一定對
                if correct_count == 4:
                    temp = order
                self.box_id_checked.append(temp)
                
                if order == temp:
                    count += 1
                    correct_count = 1
                    break
        
        self.checknumberlist_finish = self.check.supply_check(order_data, self.box_id_checked)

        print("box_id_checked:", self.box_id_checked)
        print('checknumberlist_finish: ', self.checknumberlist_finish)
        
        self.box_id_checked = self.box_id_checked + ['7A', '9', '13', '16A',  '9']
        self.checknumberlist_finish = self.checknumberlist_finish + [2, 2, 2, 2, 2]

        # ----------------------------------------
        print(f'準備操作第 {self.detect_count} 個物件(停2秒)')
        time.sleep(2)
        websocket_object_count(self.detect_count)
        websocket_robot_state('prepare')
        # ----------------------------------------

        while self.orders and not self.call_reset:
            print('\norder_count: ', self.order_count)
            
            if self.camera_update_count <= 4:   
                # ----------------------------------------
                visual_result = self.box_id_checked[:self.camera_update_count]
                check_numberlist = self.checknumberlist_finish[:self.camera_update_count]
                print(visual_result)
                print(check_numberlist)
                websocket_visual_result(visual_result, self.detect_count, None, check_numberlist)
                time.sleep(1)
                # ----------------------------------------

                self.camera_update_count += 1
            else:
                print(f'準備操作第 {self.detect_count} 個物件(停2秒)')

                # ----------------------------------------
                websocket_object_count(self.detect_count)
                websocket_robot_state('prepare')
                # ----------------------------------------
                time.sleep(2)
                
                self.check_buffer()
                if self.orders:
                    temp = self.box_id_checked[self.camera_update_count - 5]
                    # print('正確答案: ', self.orders[0], '來料: ', temp)
                    if temp == self.orders[0]:
                        self.order_count += 1
                        self.box_is_correct()
                        
                        print(f'正在操作第 {self.detect_count} 個物件(停2秒)')

                        # ----------------------------------------
                        websocket_robot_state('operate')
                        visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
                        check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
                        check_numberlist = self.check_has_three(check_numberlist)
                        websocket_visual_result(visual_result, self.detect_count, None, check_numberlist)
                        # ----------------------------------------

                        self.detect_count += 1
                        self.camera_update_count += 1
                    else:
                        self.box_is_wrong(self.buffer_name, temp)
                        # ----------------------------------------
                        visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
                        check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
                        check_numberlist = self.check_has_three(check_numberlist)
                        websocket_visual_result(visual_result, self.detect_count, None, check_numberlist)
                        # ----------------------------------------

                        self.camera_update_count += 1
                        print('錯誤!! 夾至 Buffer 區(停2秒)')
                    
                    # ----------------------------------------7
                    print(visual_result)
                    print(check_numberlist)
                    # ----------------------------------------

                    time.sleep(2)
            
            if self.order_count == self.order_length:
                break
        
        end_state = 'finish' if not self.call_reset else 'reset'
        return end_state

    def check_buffer(self):
        if self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
            self.camera_update_count -= 1

        while self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
            # print(f'buffer 區有{self.orders[0]}')
            print(f'從 Buffer 夾第 {self.detect_count} 個物件至棧板(停2秒)')
            self.checknumber = 3
            self.checknumberlist.append(self.checknumber)
            self.checked_quanlity[self.buffer_name.index(self.orders[0])] -= 1
            self.order_count += 1
            self.buffer_order.append(self.orders.pop(0))
            print('\norder_count: ', self.order_count)
            print('buffer_order: ', self.buffer_order)

            # ----------------------------------------
            websocket_robot_state('buffer_to_main')
            websocket_buffer(self.checked_quanlity)
            visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
            check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
            check_numberlist = self.check_has_three(check_numberlist)
            websocket_visual_result(visual_result, self.detect_count, None, check_numberlist)
            # ----------------------------------------

            time.sleep(2)

            self.detect_count += 1

            if not self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
                self.camera_update_count += 1

    def box_is_correct(self):
        correct_number = 1
        self.checknumberlist.append(correct_number)
        self.orders.pop(0)

    def box_is_wrong(self, items, temp):
        wrong_number = 2
        self.checknumberlist.append(wrong_number)
        index_buffer = items.index(temp)
        self.checked_quanlity[index_buffer] += 1

        # ----------------------------------------
        websocket_robot_state('buffer')
        websocket_buffer(self.checked_quanlity)
        # ----------------------------------------

class checknumberlist():
    def __init__(self):
        self.order_count = 0
        self.checknumberlist = []
        self.buffer_order = []
        self.box_id_checked = []
        self.buffer_name = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
        self.checked_quanlity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
        self.camera_update_count = 0
        
    def supply_check(self, orders, box_id_checked):
        self.orders2 = orders
        self.box_id_checked = box_id_checked
        
        count = 1
        correct_count = 1
        
        while self.orders2:
            self.check_buffer()
            if self.orders2:
                temp = self.box_id_checked[self.camera_update_count]
                if temp == self.orders2[0]:
                    self.order_count += 1
                    self.box_is_correct()
                    self.camera_update_count += 1
                else:
                    self.box_is_wrong(self.buffer_name, temp)
                    self.camera_update_count += 1
        
        return self.checknumberlist
            
    
    def check_buffer(self):
        while self.orders2 and self.checked_quanlity[self.buffer_name.index(self.orders2[0])] > 0:
            self.checknumber = 3
            self.checknumberlist.append(self.checknumber)
            self.checked_quanlity[self.buffer_name.index(self.orders2[0])] -= 1
            self.order_count += 1
            self.buffer_order.append(self.orders2.pop(0))
            self.camera_update_count += 1

    def box_is_correct(self):
        correct_number = 1
        self.checknumberlist.append(correct_number)
        self.orders2.pop(0)

    def box_is_wrong(self, items, temp):
        wrong_number = 2
        self.checknumberlist.append(wrong_number)
        index_buffer = items.index(temp)
        self.checked_quanlity[index_buffer] += 1


# import random
# import time

# class RobotTest():
#     def __init__(self):
#         self.order_count = 0
#         self.checknumberlist = []
#         self.buffer_order = []
#         self.box_id_checked = []
#         self.buffer_name = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
#         self.checked_quanlity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
#         self.camera_update_count = 1
#         self.detect_count = 1
        
#     def check_has_three(self, datas):
#         temp = []
#         for data in datas:
#             temp.append(data)
#             if data == 3:
#                 temp.append(2)
#         return temp
        
#     def supply_check(self):
#         orders = '7A,35,22,29,13,13,35,33,29,16A,13,18A,9,33,29,20,22,20,7A,33,29,9,22,20,26,7A,33,13,18A,26,18A,16A,18A'
#         orders = '7A,35,22,29,13,13,35,33,29'
#         self.orders = orders.split(',')
        
#         count = 1
#         correct_count = 1
        
#         for order in self.orders:
#             while True:
#                 # temp = random.sample(self.buffer_name, 2)
#                 # temp.append(self.orders[count - 1])
#                 # temp = random.choice(temp)
#                 temp = random.sample(self.buffer_name, 1)
#                 temp = random.choice(temp)
        
#                 correct_count += 1
#                 # correct_count == 4: 第三次比對結果一定對
#                 if correct_count == 4:
#                     temp = order
#                 self.box_id_checked.append(temp)
                
#                 if order == temp:
#                     count += 1
#                     correct_count = 1
#                     break
#         print("orders:", self.orders)
#         print("box_id_checked:", self.box_id_checked)
#         print(f'準備操作第 {self.detect_count} 個物件(停2秒)')
        
#         check = checknumberlist()
#         self.checknumberlist_finish = check.supply_check(orders.split(','), self.box_id_checked)
#         print('checknumberlist_finish: ', self.checknumberlist_finish)
        
#         while self.orders:
#             print('\norder_count: ', self.order_count)
#             time.sleep(1)
            
#             if self.camera_update_count <= 4:
#                 print(self.box_id_checked[:self.camera_update_count])
#                 print(self.checknumberlist_finish[:self.camera_update_count])
#                 self.camera_update_count += 1
#             else:
                
#                 if self.detect_count != 1:
#                     print(f'準備操作第 {self.detect_count} 個物件(停2秒)')
#                     time.sleep(2)
                
#                 self.check_buffer()
#                 if self.orders:
#                     temp = self.box_id_checked[self.camera_update_count - 5]
#                     print('正確答案: ', self.orders[0], '來料: ', temp)
#                     if temp == self.orders[0]:
#                         # print('與工單一樣')
#                         self.order_count += 1
#                         self.box_is_correct()
                        
#                         print(f'正在操作第 {self.detect_count} 個物件(停2秒)')
#                         visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
#                         check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
#                         check_numberlist = self.check_has_three(check_numberlist)
#                         print(visual_result)
#                         print(check_numberlist)
                        
#                         self.detect_count += 1
#                         self.camera_update_count += 1
                        
                        
#                     else:
#                         self.box_is_wrong(self.buffer_name, temp)
#                         visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
#                         check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
#                         check_numberlist = self.check_has_three(check_numberlist)
#                         print(visual_result)
#                         print(check_numberlist)
                        
#                         self.camera_update_count += 1
                        
#                         print('錯誤!! 夾至 Buffer 區(停2秒)')
#                     # print(self.box_id_checked[self.camera_update_count - 5:self.camera_update_count - 1])
#                     # print(self.checknumberlist_finish[self.camera_update_count - 5:self.camera_update_count - 1])
#                     time.sleep(2)
                    
#                 # print('checknumberlist:', self.checknumberlist)
#                 # print('buffer_order:', self.buffer_order)
#                 # print('checked_quanlity', self.checked_quanlity)
            
    
#     def check_buffer(self):
#         if self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
#             self.camera_update_count -= 1
            
#         while self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
#             # print(f'buffer 區有{self.orders[0]}')
#             print(f'從 Buffer 夾第 {self.detect_count} 個物件至棧板(停2秒)')
            
#             self.checknumber = 3
#             self.checknumberlist.append(self.checknumber)
#             self.checked_quanlity[self.buffer_name.index(self.orders[0])] -= 1
#             self.order_count += 1
#             self.buffer_order[1:]
#             self.buffer_order.append(self.orders.pop(0))
#             print('\norder_count: ', self.order_count)
#             print('buffer_order: ', self.buffer_order)
            
#             # visual_result = self.box_id_checked[self.camera_update_count - 4:self.camera_update_count]
#             # check_numberlist = self.checknumberlist_finish[self.camera_update_count - 4:self.camera_update_count]
#             # print(visual_result)
#             # print(check_numberlist)
            
#             time.sleep(2)
            
#             self.detect_count += 1
            
#             if not self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
#                 self.camera_update_count += 1
            
            
            

#     def box_is_correct(self):
#         correct_number = 1
#         self.checknumberlist.append(correct_number)
#         self.orders.pop(0)

#     def box_is_wrong(self, items, temp):
#         wrong_number = 2
#         self.checknumberlist.append(wrong_number)
#         index_buffer = items.index(temp)
#         self.checked_quanlity[index_buffer] += 1
        
# class checknumberlist():
#     def __init__(self):
#         self.order_count = 0
#         self.checknumberlist = []
#         self.buffer_order = []
#         self.box_id_checked = []
#         self.buffer_name = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
#         self.checked_quanlity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        
#         self.camera_update_count = 0
        
#     def supply_check(self, orders, box_id_checked):
#         self.orders = orders
#         self.box_id_checked = box_id_checked
        
#         count = 1
#         correct_count = 1
        
#         while self.orders:
#             self.check_buffer()
#             if self.orders:
#                 temp = self.box_id_checked[self.camera_update_count]
#                 if temp == self.orders[0]:
#                     self.order_count += 1
#                     self.box_is_correct()
#                     self.camera_update_count += 1
#                 else:
#                     self.box_is_wrong(self.buffer_name, temp)
#                     self.camera_update_count += 1
        
#         return self.checknumberlist
            
    
#     def check_buffer(self):
#         while self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
#             self.checknumber = 3
#             self.checknumberlist.append(self.checknumber)
#             self.checked_quanlity[self.buffer_name.index(self.orders[0])] -= 1
#             self.order_count += 1
#             self.buffer_order.append(self.orders.pop(0))
#             self.camera_update_count += 1

#     def box_is_correct(self):
#         correct_number = 1
#         self.checknumberlist.append(correct_number)
#         self.orders.pop(0)

#     def box_is_wrong(self, items, temp):
#         wrong_number = 2
#         self.checknumberlist.append(wrong_number)
#         index_buffer = items.index(temp)
#         self.checked_quanlity[index_buffer] += 1
            
# robot = RobotTest()
# robot.supply_check()