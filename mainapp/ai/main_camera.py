import time
from Dimension_2_3D_single import Dimension_2_3D
from Dimension_3D_single import Dimension_3D
import cv2
import numpy as np
from camera import intelCamera_copy
#from camera import azuredkCamera, intelCamera_copy
from yaskawa import Yaskawa_control
from qrcode import qrClass
import csv
import os



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
            "resolution":"1080p",
            "fps":"15",
            "depthMode":"WFOV",
            "algin":"color"
        }
        

#camera = azuredkCamera.azureDK(config)
try:
	camera.openCamera()
except :
    process = False
        
    print('No Camera')

crop = {'xmin' :150, 'xmax':1920,'ymin':450, 'ymax':790, 'total height':495}

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

def write_to_csv(file_path, box_id, angle):
    # Skip writing to CSV if box_id is '0'
    if box_id == '0':
        return
    # Check if box_id is a list and extract the first element if it is
    if isinstance(box_id, list) and len(box_id) > 0:
        box_id = box_id[0]
    # Add '#' to the box_id
    box_id_with_hash = f"#{box_id}"
    with open(file_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([box_id_with_hash, angle])


def main():
    count = 0
    last_box_id = None  # Variable to keep track of the last box id
    csv_file_path = "detected_boxes.csv"  # Path for the CSV file
    # Open the CSV file in write mode to overwrite any existing file
    with open(csv_file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Box_id", "Angle"])  # Column headers
    #out_raw = cv2.VideoWriter(f"recording.avi", cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 3, (1920, 1080))
    if not process:
        return None
    for idx_, i in enumerate(camera.getData()):	
        if not i :
            continue
        start_ = time.time()

        image, pc , depth_image =  i
        image_crop = image[crop['ymin']:crop['ymax'], crop['xmin']:crop['xmax']]    
        # cv2.imshow('image_crop', image_crop)
        cv2.waitKey(1)
        # if robot.request_sensor11():
        if True:

            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image_copy = np.copy(image)
            
            startdecodetime = time.time()
            dbrcount = qr_object.decode_dbrcount(image)
            pyzbarcount = qr_object.decode_pyzbarcount(image_copy)
            enddecodetime =  time.time()
            print(dbrcount, pyzbarcount)
            twodecodetime=enddecodetime -startdecodetime
            # print( "Time taken twodecodetime: {0} seconds".format(twodecodetime))
            # # Calculate frames per second
            fps2  = 1 / twodecodetime
            # print( "Estimated  twodecodetime cv2 frames per second : {0}".format(fps2))

            # two detect count equal can show
            if dbrcount == pyzbarcount:
                
                #image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image.copy(), pc)
                image_qr, boxID_list,sorted_dict_by_value_desc,angle_list = qr_object.qr_result(image, pc)

                if boxID_list and angle_list:
                    qr_dict = {'box_id': boxID_list, 'angle': angle_list}
                else:
                    qr_dict = {'box_id': '0', 'angle': '-1'}

                box_id = qr_dict['box_id']
                angle = qr_dict['angle']

                # Check if the detected box is new
                if box_id != last_box_id:
                    last_box_id = box_id
                    write_to_csv(csv_file_path, last_box_id, angle)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                cv2.putText(image, f"ID: {box_id}",(1550,70), cv2.FONT_HERSHEY_TRIPLEX,2,(0,0,255,1),3)
                cv2.imshow('image',image)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
