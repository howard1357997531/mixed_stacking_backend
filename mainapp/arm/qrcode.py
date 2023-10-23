import cv2
from pyzbar import pyzbar
import numpy as np
import math
class qrClass():
    def __init__(self,crop):
        #self.qrcodedic={}
        self.crop = crop

    def crop_array(self, array):
        xmin = self.crop['xmin']
        xmax = self.crop['xmax']
        ymin = self.crop['ymin']
        ymax = self.crop['ymax']
        return array[ymin:ymax, xmin:xmax]
    
    def decode2(self,image, pc):
        image = self.crop_array(image)
        pc = self.crop_array(pc)
        decoded_objects = pyzbar.decode(image)
        angle_list = []
        self.pts = np.where(pc[:,:,2]>0)
        self.qrcodedic = {}
        for idx,obj in enumerate(decoded_objects):
            # draw the barcode
            
            #image = self.draw_barcode(obj, image)
            angle = self.get_angle(obj, pc)
            angle_list.append(angle)
            self.qrcodedic[obj.data.decode("utf-8")]= obj.rect.left


        return image, self.qrcodedic, angle_list

    def draw_barcode(self, decoded, image):
        image = cv2.rectangle(image, (decoded.rect.left, decoded.rect.top), 
                                (decoded.rect.left + decoded.rect.width, decoded.rect.top + decoded.rect.height),
                                color=(0, 255, 0),
                                thickness=5)
        cv2.putText(image, str(decoded.data.decode("utf-8")), (decoded.rect.left, decoded.rect.top) ,
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0 ,255), 2)
        return image
    
    def mask_processing(self,point_cloud,min_depth, max_depth):
        # point_cloud = point_cloud[point_cloud[:,:,2]>0]
        points_index = np.where((point_cloud[:,:,2] >min_depth )& (point_cloud[:,:,2] <max_depth))

        mask = np.zeros(point_cloud.shape[:2], dtype = np.uint8)
        
        mask[points_index[0], points_index[1]] = 255 
        
        # start_ = time.time()
        # mask_ = cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
        # mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))

        mask_ = np.zeros_like(mask)

        points_,_ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_TC89_L1)

        cnt_list = []
        for cnt in points_:
            if cv2.contourArea(cnt) > 2000:
                cnt_list.append(cnt)
                # cv2.fillPoly(mask_, [cnt], -1, (255,255,255), 1)
                # cv2.fillPoly(mask_, pts = [cnt],  color = (255,255,255))
                cv2.drawContours(mask_, [cnt], -1 , (255,255,255),cv2.FILLED)
        points_ = cnt_list
        # mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        # mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = mask_
        
        if points_:
            points = points_[0][:,0,:]
        else:
            points = np.dstack([points_index[1], points_index[0]])[0]    
        
        # print(1/ (time.time() - start_))


        return mask, points
    def poseDifference(self, currentImg,mask):

        rows,cols = currentImg.shape[:2]
        # [vx,vy,x,y] = cv2.fitLine(np.array(finalMask), cv2.DIST_L2,0,0.01,0.01)
        [vx,vy,x,y] = cv2.fitLine(np.array(mask), cv2.DIST_L2,0,0.01,0.01)
        lefty = int((-x*vy/vx) + y)
        righty = int(((cols-x)*vy/vx)+y)        
        cv2.line(currentImg,(cols-1,righty),(0,lefty),(0,255,0),3)
        angle_rad = math.atan2(vy, vx)
        radFixed = math.degrees(angle_rad)

        radFixed = abs(radFixed)

        return currentImg,radFixed

    def find_rectangle(self, point_cloud,min_depth, max_depth):
        # Extract non-zero depth values and their (x, y) coordinates.
        mask, points = self.mask_processing(point_cloud,min_depth, max_depth)
        # cv2.imshow('mask_', mask)
        mask_idx = points

        if len(mask_idx) >0 :
            img__, angle = self.poseDifference(mask,points)
            # print(angle)
        else:
            img__ = None
            angle = None

    

        return angle    

    def get_angle(self,decoded ,pc):

        x =  decoded.rect.left
        y = decoded.rect.top
        w = decoded.rect.width
        h = decoded.rect.height

        pc_depth = pc[y:y+h, x:x+w, -1]
        pc_depth = pc_depth[pc_depth >0]
        min_depth = np.nanmean(pc_depth)
        max_depth = min_depth + 10
        angle = self.find_rectangle(pc, min_depth -5 , max_depth)
     
        if not angle:
            angle = 0 
        if abs(angle) >= 50:
            angle = 1
        else:
            angle = 0        
        return angle
    

    def qr_result(self, image, pc):
        image_qr,qrcodedic, angle_list = self.decode2(image, pc)
        sorted_dict_by_value_desc = dict(sorted(qrcodedic.items(), key=lambda item: item[1], reverse=True))
        
        #靠近夾取位置的id
        boxID_list = list(sorted_dict_by_value_desc.keys())
#        num_items = len(qrcodedic)
        
        return image_qr, boxID_list,sorted_dict_by_value_desc , angle_list
        



