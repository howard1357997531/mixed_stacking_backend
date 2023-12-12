import time
from Dimension_2_3D_single import Dimension_2_3D
from Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from camera import intelCamera_copy
#from camera import azuredkCamera, intelCamera_copy
from yaskawa import Yaskawa_control
from qrcode import qrClass

import datetime




robot_ip = '192.168.1.15'
port = 10040
# camera = intelCamera_copy.L515({'SerialNumber':'f1230465'}) 
process = True
try:
    camera = intelCamera_copy.L515() 
except:
     process = False
     pass
config =  {
            "resolution":"720p",
            "fps":"15",
            "depthMode":"WFOV",
            "algin":"color"
        }
        

#camera = azuredkCamera.azureDK(config)
try:
	camera.openCamera()
except :
    process = False
        
    print('No Camera camera.openCamera')

#crop = {'xmin' :150, 'xmax':1920,'ymin':450, 'ymax':790, 'total height':495}  resolution 1920*1280    *******

crop = {'xmin' :70, 'xmax':1280,'ymin':280, 'ymax':550, 'total height':270} # resolution 1280*720      *******

dimenssion_object = Dimension_2_3D(crop = crop)
qr_object = qrClass(crop = crop)

dimenssion_3D_object = Dimension_3D(crop = crop)
robot = Yaskawa_control(server_ip=robot_ip, server_port=port)

def voting_preprocess(dst, src, key):

    dst[src[key]] = dst.get(src[key], 0) + 1
    return dst
def voting(result, key_list, data_list):
            
    for key in key_list:
        for src in data_list:
            result_dict = voting_preprocess(result_dict, src, key)
            
    return result


def main():
    count = 0
    
    if not process:
        return None
    for idx_, i in enumerate(camera.getData()):	
        if not i :
            continue
        start_time = time.time()

        image, pc , depth_image =  i
        image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
        #
        # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # adjustedimage = cv2.convertScaleAbs(gray, alpha=1.8, beta=255-240)
        
        startdecodetime = time.time()
        dbrcount = qr_object.decode_dbrcount(image)
        
        #image = qr_object.reduce_glare(image)
        image = qr_object.reduce_highlights(image)         
        
        pyzbarcount = qr_object.decode_pyzbarcount(image)


        print(dbrcount, pyzbarcount)

        # if dbrcount !=pyzbarcount:
        #     continue
           
        if dbrcount == pyzbarcount:

            #
            
            image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image, pc)
            
            end_time = time.time()

            # 計算執行時間，換算成 FPS
            elapsed_time = end_time - start_time
            fps = 1 / elapsed_time

            if boxID_list and angle_list:
                qr_dict = {'box_id': boxID_list, 'angle': angle_list}
            else:
                qr_dict = {'box_id': '0', 'angle': '-1'}

            
            
            box_id = qr_dict['box_id']
            angle = qr_dict['angle']

            cv2.putText(image, f"ID: {box_id}, angle: {angle}, FPS:{fps:.2f}",(50,50), cv2.FONT_HERSHEY_COMPLEX_SMALL,1,(0,0,255,1))

            cv2.imshow('image',image)

            
            k = cv2.waitKey(1)
           

                
            if k == ord('q'):
                break


main()