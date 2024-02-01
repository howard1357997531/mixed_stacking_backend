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

items = ['7A', '9', '13', '16A', '18A', '20', '22', '26', '29', '33', '35']
orders = '7A,35,22,29,13,13,35,33,29,16A,13,18A,9,33,29,20,22,20,7A,33,29,9,22,20,26,7A,33,13,18A,26,18A,16A,18A'
orders = '7A,35,22,29'
orders = orders.split(',')

count = 0
correct_count = 0

for order in orders:
    print('count:', count)
    print('order:', order)
    while True:
        temp = random.sample(items, 2)
        temp.append(orders[count])
        temp = random.choice(temp)
        print(temp)
        if order == temp:
            count += 1
            break