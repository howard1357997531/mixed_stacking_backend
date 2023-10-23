
import time
from .Dimension_2_3D_single import Dimension_2_3D
from .Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from .camera import intelCamera_copy
from .yaskawa import Yaskawa_control
from .qrcode import qrClass


robot_ip = '192.168.1.15'
port = 10040
# camera = intelCamera_copy.L515({'SerialNumber':'f1230465'}) 
camera = intelCamera_copy.L515() 
camera.openCamera()

crop = {'xmin' :350, 'xmax':1410,'ymin':450, 'ymax':790, 'total height':495}
dimenssion_object = Dimension_2_3D(crop = crop)
qr_object = qrClass(crop = crop)

dimenssion_3D_object = Dimension_3D(crop = crop)
robot = Yaskawa_control(server_ip=robot_ip, server_port=port)

def cameraCheck():
    count = 0
    #out_raw = cv2.VideoWriter(f"recording.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 3, (1920, 1080))

    for idx_, i in enumerate(camera.getData()):	
        if not i :
            continue
        image, pc , depth_image =  i
        image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
        
        if robot.request_sensor11():
        #if True:
            # if count < 5:
            #     count += 1
            #     continue
            
            result_dict = {}
            # total = 3
            # Get angle
            #rectangle_array, pc_rectangle, min_depth, max_depth,angle = dimenssion_object.detect_dmenssion()
            
            # Get qr id
            image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image.copy(), pc)
            if boxID_list and angle_list:


                qr_dict = {'box_id': boxID_list[0], 'angle': angle_list[0]}
            else:
                qr_dict = {'box_id': '0', 'angle': '-1'}

            # Classfication
            # result = dimenssion_object.get_result(image, pc, depth_image)

            # dimenssion_3D_object.set_data(pc, image )
            # result_3D = dimenssion_3D_object.get_result()
            # if result is None:
            #     cv2.imshow('image', image) 
            #     cv2.waitKey(1)                
            #     continue
            
            # result_dict[qr_dict['box_id']] = result_dict.get(qr_dict['box_id'], 0) + 1
            # result_dict[result['box_id']] = result_dict.get(result['box_id'], 0) + 1
            # result_dict[result_3D['box_id']] = result_dict.get(result_3D['box_id'], 0) + 1
            
            # angle_dict = {}
            # angle_dict[qr_dict['angle']] = angle_dict.get(qr_dict['angle'], 0) + 1
            # angle_dict[result['angle']] = angle_dict.get(result['angle'], 0) + 1
            # angle_dict[result_3D['angle']] = angle_dict.get(result_3D['angle'], 0) + 1
            # rectangle = result_3D['rectangle']

            # if len(set(result_dict.keys() ))== total:
            #     box_id = result['box_id']
            #     angle  = result['angle']
            # else:

            #     # box_id = sorted(result_dict.keys(),reverse = True)[0]
            #     box_id = sorted(result_dict.items(), key = lambda x:x[1], reverse = True)[0][0]
            #     # angle = sorted(angle_dict.keys(),reverse = True)[0]
            #     angle = sorted(angle_dict.items(), key = lambda x:x[1], reverse= True)[0][0]

            # box_id, angle, rectangle = result['box_id'], result['angle'], result['rectangle']
            #print('QR:',qr_dict['box_id'])
            # cv2.putText(image, f"ID: {box_id}, angle: {angle}", tuple(rectangle[0])+ np.asarray([0,0]), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))
            # if boxID_list and angle_list:
                # cv2.putText(image, f"QR: {boxID_list[0]}, angle: {angle_list[0]}", tuple(rectangle[0]+ np.asarray([0,200])), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))
            # cv2.imshow('image',image)
            # cv2.waitKey(1)
            QR_ID=qr_dict['box_id']
            angle = qr_dict['angle']
            # BOX_id = '#'+ box_id
            if QR_ID[-1].isdigit():
                QR_id='#'+QR_ID
            else:
                QR_id='#'+QR_ID[:-1]
            print(QR_id, angle)
            return  QR_id,angle    
    
            # return box_id, angle, boxID_list
        else:
            cv2.imshow('image', image) 
            cv2.waitKey(1)
            #return None, None, None
        #out_raw.write(image)
   

# cameraCheck()    
     
