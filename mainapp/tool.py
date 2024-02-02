a = ["1", "1", "1", "1_insert", "1_insert", "2", "1", "2_insert"]
a = ["1", "1", "2", "1_insert", "1_insert", "2_insert", "2", "3", "3", "3","2_insert"]
a = ["1_insert", "1_insert", "1", "1", "2", "2_insert", "1_insert", "1_insert", "2", "3", "3", "3","2_insert"]


def parse_execution_data(data):
    datas = []
    insert_index = []
    data_temp = None
    insert_temp = None
    count = -1
    for i in data:
        if i.endswith('_insert'):
            data_temp = None
            insert_num = i.replace('_insert', '')
            if insert_temp:
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
                insert_temp = insert_num
                insert_index.append(count)
        else:
            insert_temp = None
            if data_temp:
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
                data_temp = i
    
    return datas, insert_index

import random
import time

class RobotTest():
    def __init__(self):
        self.order_count = 0
        self.checknumberlist = []
        self.buffer_order = []
        self.box_id_checked = []
        
    def supply_check(self):
        self.buffer_name = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
        orders = '7A,35,22,29,13,13,35,33,29,16A,13,18A,9,33,29,20,22,20,7A,33,29,9,22,20,26,7A,33,13,18A,26,18A,16A,18A'
        self.checked_quanlity = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        orders = '7A,35,22,29,13,13,35,33,29'
        self.orders = orders.split(',')
        orders_lentgh = len(self.orders)
        
        count = 1
        correct_count = 0
        
        # for order in orders:
        #     if count == 1:
        #         print('工單排序: ', self.orders)
        #     print('count:', count)
            
        while self.orders:
            print('')
            print('\norder_count: ', self.order_count)
            time.sleep(1)
            temp = random.sample(self.buffer_name, 1)
            temp = random.choice(temp)
            
            
            correct_count += 1
            if correct_count == 3:
                temp = self.orders[0]
                correct_count = 0
            self.box_id_checked.append(temp)
            print("box_id_checked:", self.box_id_checked)
            
            self.check_buffer()
            if temp == self.orders[0]:
                print('與工單一樣')
                self.order_count += 1
                self.box_is_correct()
            else:
                print('錯的放到buffer區')
                self.box_is_wrong(self.buffer_name, temp)

            print('checknumberlist:', self.checknumberlist)
            print('buffer_order:', self.buffer_order)
            print('checked_quanlity', self.checked_quanlity)
        
        count_1 = self.checknumberlist.count(1)
        count_3 = self.checknumberlist.count(3)
        total = count_1 + count_3
        print(total, orders_lentgh)

    def check_buffer(self):
        while self.orders and self.checked_quanlity[self.buffer_name.index(self.orders[0])] > 0:
            time.sleep(0.05)
            print(f'buffer 區有{self.orders[0]}')
            self.checknumber = 3
            self.checknumberlist.append(self.checknumber)
            self.checked_quanlity[self.buffer_name.index(self.orders[0])] -= 1
            self.order_count += 1
            self.buffer_order.append(self.orders.pop(0))
        

    def box_is_correct(self):
        correct_number = 1
        self.checknumberlist.append(correct_number)
        self.orders.pop(0)

    def box_is_wrong(self, items, temp):
        wrong_number = 2
        self.checknumberlist.append(wrong_number)
        index_buffer = items.index(temp)
        self.checked_quanlity[index_buffer] += 1
            
# robot = RobotTest()
# robot.supply_check()