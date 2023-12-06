import cv2
from pyzbar import pyzbar

from pyzbar.pyzbar import decode
import numpy as np
import math
import dbr
from dbr import *
import re


class qrClass():
    def __init__(self,crop):
        #self.qrcodedic={}
        self.crop = crop
        self.dbr_reader = BarcodeReader()
        license_key = "DLS2eyJoYW5kc2hha2VDb2RlIjoiMjAwMDAxLTE2NDk4Mjk3OTI2MzUiLCJvcmdhbml6YXRpb25JRCI6IjIwMDAwMSIsInNlc3Npb25QYXNzd29yZCI6IndTcGR6Vm05WDJrcEQ5YUoifQ==" # if you have LICENSE key, write here 
        self.dbr_reader.init_license(license_key)


    def crop_array(self, array):
        xmin = self.crop['xmin']
        xmax = self.crop['xmax']
        ymin = self.crop['ymin']
        ymax = self.crop['ymax']
        return array[ymin:ymax, xmin:xmax]
    
    # add other detect and count
    def decode_dbrcount(self,frame):
        self.frame = frame
        frame = self.crop_array(frame)

        decoded_qrs = self.dbr_reader.decode_buffer(frame)
        if decoded_qrs !=None:
            qrscount=len(decoded_qrs)
            return qrscount
        return 0

    def decode_pyzbarcount(self,image):
        self.image = image
        image = self.crop_array(image)
  
        decoded_objects = pyzbar.decode(image)
        if decoded_objects !=None:
            qrspyzbarcount = len(decoded_objects)
            return qrspyzbarcount
        return 0    
    #
    
    
    def decode2(self,image, pc):
        self.image = image
        image = self.crop_array(image)
        pc = self.crop_array(pc)
        decoded_objects = pyzbar.decode(image)
        angle_list = []
        qrcodelist = []
        self.pts = np.where(pc[:,:,2]>0)
        self.qrcodedic = {}
        qrcodedic = {}

        for idx,obj in enumerate(decoded_objects):
            qrcodedic[idx]= obj.rect.left
        sorted_dict_by_value_desc = dict(sorted(qrcodedic.items(), key=lambda item: item[1], reverse=True))
        
        BoxIDList = []
        #去除字母
        for k,v in sorted_dict_by_value_desc.items():
            obj = decoded_objects[k]
            datadecode = re.sub(r'[a-zA-Z]', '', obj.data.decode("utf-8"))            

            image = self.draw_barcode(obj, image)
            self.id = datadecode
            angle = self.get_angle(obj, pc)
            if '20' in datadecode or '35' in datadecode:
                angle = 0
            angle_list.append(angle)
            BoxIDList.append(datadecode)

        # return image, self.qrcodedic, angle_list
        return image, BoxIDList, angle_list

    def draw_barcode(self, decoded, image):
        image = cv2.rectangle(image, (decoded.rect.left, decoded.rect.top), 
                                (decoded.rect.left + decoded.rect.width, decoded.rect.top + decoded.rect.height),
                                color=(0, 255, 0),
                                thickness=5)
        cv2.putText(image, str(decoded.data.decode("utf-8")), (decoded.rect.left, decoded.rect.top) ,
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0 ,255), 2)
        return image

    def mask_angle_processing(self,point_cloud,min_depth, max_depth):
        # point_cloud = point_cloud[point_cloud[:,:,2]>0]
        points_index = np.where((point_cloud[:,:,2] >min_depth )& (point_cloud[:,:,2] <max_depth))

        mask = np.zeros(point_cloud.shape[:2], dtype = np.uint8)
        
        mask[points_index[0], points_index[1]] = 255 
        
        # mask_ = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        # mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

        mask_ = np.zeros_like(self.image[:,:,0])
        

        points_,_ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_L1)
        
        # points_ = self.merge_nearby_contours(mask)
        cnt_list = []
        angle_list = []
        count = 0
        for idx, cnt in enumerate(points_):
            if cv2.contourArea(cnt) > 7500:
                count += 1
                cnt = cnt + np.asarray([ self.crop['xmin'], 0 ])
                mask_angle = np.zeros_like(self.image[:,:, 0])
                # cnt += np.asarray([self.crop['xmin'], 1, self.crop['xmax']])
                cnt_list.append(cnt)
                
                cv2.drawContours(mask_, [cnt], -1 , (255,255,255),cv2.FILLED)
                cv2.drawContours(mask_angle, [cnt], -1 , (255,255,255),cv2.FILLED)

                # cv2.imwrite('mask_angle.jpg',mask_angle)
                angle = self.get_moment_angle(mask_angle, cnt)
                # angle = self.poseDifference(mask_angle, cnt)
                
                cv2.putText(mask_angle, f"{angle}", (5,55), 1,cv2.FONT_HERSHEY_COMPLEX_SMALL, (255,255,255),1)
                cv2.putText(mask_angle, f"{self.id}", (950,55), 1,cv2.FONT_HERSHEY_COMPLEX_SMALL, (255,255,255),1)
                # cv2.imshow(f'mask_angle', mask_angle)

                

        points_ = cnt_list

        # cv2.imshow('mask_', mask_)
        # cv2.waitKey(0)
        mask = mask_
        
        if points_:
            points = points_[0][:,0,:]
        else:
            points = np.dstack([points_index[1], points_index[0]])[0]    
        if len(points_) <= 0:
            angle = None

        return mask, points, angle
    def poseDifference(self, currentImg,mask):
        """
            Found points angle by cv2 fitline function.
            Input:
                 currentImg: array -> image(it would be mask image normally)
                 mask: array -> list of points
            Output:
                currentImg:  array -> image
                radFixed : float -> degree of the current points.       
        """
        rows,cols = currentImg.shape[:2]
        # [vx,vy,x,y] = cv2.fitLine(np.array(finalMask), cv2.DIST_L2,0,0.01,0.01)

        [vx,vy,x,y] = cv2.fitLine(np.array(mask), cv2.DIST_L2,0,0.01,0.01)
        lefty = int((-x*vy/vx) + y)
        righty = int(((cols-x)*vy/vx)+y)        
        cv2.line(currentImg,(cols-1,righty),(0,lefty),(0,255,0),3)
        angle_rad = math.atan2(vy, vx)
        radFixed = math.degrees(angle_rad)
        # cv2.imshow('mask,', currentImg)
        radFixed = abs(radFixed)

        return radFixed



    def get_moment_angle(self, binary_mask,cnt):
        # Get the rotated rectangle around the contour
        rect = cv2.minAreaRect(cnt)
        _, (width, height), angle = rect
        
        # Correct the angle based on width and height
        if width > height:
            angle = (90 + angle) % 180  # Transform to [0, 180]
            if angle > 90:  # Transform to [-90, 90]
                angle -= 180
        angle = 90 - abs(angle)
        return angle

    def find_rectangle(self, point_cloud,min_depth, max_depth):
        # Extract non-zero depth values and their (x, y) coordinates.
        _, _, angle = self.mask_angle_processing(point_cloud,min_depth, max_depth)

        return angle    

	

    def get_angle(self,decoded ,pc):

        x =  decoded.rect.left
        y = decoded.rect.top
        w = decoded.rect.width
        h = decoded.rect.height
        

        # p0 = [decoded.polygon[0].x, decoded.polygon[0].y]
        # p1 = [decoded.polygon[1].x, decoded.polygon[1].y]
        # p2 = [decoded.polygon[2].x , decoded.polygon[2].y]
        # p3 = [decoded.polygon[3].x, decoded.polygon[3].y]

        # pts = np.asarray([p0,p1,p2,p3])

        # pts = pts[np.argsort(pts,axis = 0)[:,0]]

        # # pts[0] = pts[0] - np.asarray([30,0])
        # # pts[1] = pts[1] - np.asarray([30,0])
        # mask = np.zeros_like(pc[:,:,0])
        # interval = 0

        # cv2.circle(mask, tuple(pts[0]), 1, (255,255,255), 1)
        # cv2.circle(mask, tuple(pts[1]), 1, (255,255,255), 1)
        # cv2.circle(mask, tuple(pts[2]), 1, (255,255,255), 1)
        # cv2.circle(mask, tuple(pts[3]), 1, (255,255,255), 1)

        # cnt = pts


        
        # angle = self.get_moment_angle(None, cnt)


        # cv2.putText(mask, f"{angle}", (20,20), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (255,255,255), 1)
        # cv2.imshow('mask', mask)

        pc_depth = pc[y:y+h, x:x+w, -1]
        pc_depth = pc_depth[pc_depth >0]
        min_depth = np.nanmean(pc_depth)
        # max_depth = min_depth + (20 - 1/(700 -min_depth)*750)
        max_depth = min_depth + 10
        #interval = 10000
        # pc = pc[y-interval:y+h+interval, x-interval:x+w+interval]
        # pc = pc[self.crop['ymin']:self.crop['ymax'], x- 10 :x+w+ 20]
        if x <100:
            x = 100

        pc = pc[:, x - 100 :x+w+75]

        angle = self.find_rectangle(pc, min_depth -5 , max_depth)
        

        if not angle:
            angle = 0 
        if abs(angle) >= 55:
            angle = 1
        else:
            angle = 0        
        return angle
    

    def qr_result(self, image, pc):
        # image_qr,+qrcodedic, angle_list = self.decode2(image, pc)
        # sorted_dict_by_value_desc = dict(sorted(qrcodedic.items(), key=lambda item: item[1], reverse=True))
        
        #靠近夾取位置的id
        # boxID_list = list(sorted_dict_by_value_desc.keys())
#        num_items = len(qrcodedic)
        image_qr,BoxIDList, angle_list = self.decode2(image, pc)
        # return image_qr, boxID_list,sorted_dict_by_value_desc , angle_list
        
        return image_qr, BoxIDList,{} , angle_list
 