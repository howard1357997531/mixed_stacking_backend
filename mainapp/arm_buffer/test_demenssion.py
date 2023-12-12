
import time
from Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from camera import intelCamera
from yaskawa import Yaskawa_control
from qrcode import qrClass

robot_ip = '192.168.1.15'
port = 10040
camera = intelCamera.L515({'SerialNumber':'f1230465'}) 
camera.openCamera()

crop = {'xmin' :100, 'xmax':1400,'ymin':450, 'ymax':780, 'total height':495}
dimenssion_object = Dimension_3D(crop = crop)
qr_object = qrClass()
robot = Yaskawa_control(server_ip=robot_ip, server_port=port)
count = 0
def main():
    for idx_, i in enumerate(camera.getData()):	
        if not i :
            continue
        image, pc , _ =  i
        image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
        if robot.request_sensor11():
            if count < 5:
                count += 1
                continue
            
            dimenssion_object.set_data(pc)


            # Get angle
            #rectangle_array, pc_rectangle, min_depth, max_depth,angle = dimenssion_object.detect_dmenssion()
            
            # Get qr id
            image_qr, boxID_list,sorted_dict_by_value_desc = qr_object.qr_result(image)


            # Classfication
            result = dimenssion_object.get_result()

            box_id, angle, rectangle = result['box_id'], result['angle'], result['rectangle']
        

            #cv2.putText(image, f"{box_id}, angle: {angle}", tuple(rectangle[0]), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))
            #cv2.imshow('image',image)
            #cv2.waitKey(1)        
    #        print(box_id, angle)
            return box_id, angle, boxID_list
        else:
            #cv2.imshow('image', image_crop) 
            #cv2.waitKey(1)
            return None, None, None