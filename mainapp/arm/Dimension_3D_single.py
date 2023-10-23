import pandas as pd
import numpy as np
import cv2
import math
import numpy as np
# import cv2
import time

# -------------
from django.conf import settings
import os

box_volume_path = os.path.join(settings.MEDIA_ROOT, 'camera', 'box volumn.csv')
# -------------


class Dimension_3D():
    def __init__(self, crop = {'xmin' :320, 'xmax':1920,'ymin':50, 'ymax':1080, 'total height':790}, image = None):
        self.xmin = crop['xmin']
        self.xmax = crop['xmax']
        self.ymin = crop['ymin']
        self.ymax = crop['ymax']
        self.height = crop['total height']
        self.prev_  = 0
        # self.height = 656
        self.image = None
        self.method = 'np'
        if self.method == 'pd':
            # self.true = pd.read_csv(r'./box volumn.csv')
            self.true = pd.read_csv(box_volume_path)
        else:
            # true = np.genfromtxt('./box volumn.csv', delimiter = ',')
            true = np.genfromtxt(box_volume_path, delimiter = ',')
            self.true = true[1:,:-1]
        self.bg_img = np.full((900,1600,3),0).astype(np.uint8)


    def remove_outliers_advanced(self,pc, k=0.1):
        # Fit a plane using RANSAC
        
        # Calculate residuals
        
        mean_z = np.nanmean(pc[:,-1])
        lower_bound = np.percentile(pc[:,-1], 25)
        upper_bound = np.percentile(pc[:,-1], 75)
        diff = upper_bound - lower_bound


        lower_bound = mean_z - diff*k
        upper_bound = mean_z + diff*k

        pc = pc[(pc[:,-1] > lower_bound)&(pc[:,-1]<upper_bound)]

        return pc

    def depth_filter(self, point_cloud):
        
        pc_ = point_cloud[point_cloud[:,:,-1] != 0]
        size = pc_.shape[0] - 1
        if size > 50:
            size = 50            

        min_depth =  np.mean(np.partition(pc_[:,-1], size )[:size])
            # min_depth =  np.mean(np.partition(pc_[:,-1], 50)[:50])
        # max_depth = min_depth + 0.5
        max_depth = self.height - 10


        return [min_depth, max_depth]
    
    def set_data(self,pc, image):
        self.point_cloud = pc
        self.image = image[self.ymin:self.ymax, self.xmin:self.xmax]

    def find_closest_corner(self, given_point, given_mask):
        substract = np.absolute(given_mask - given_point)
        
        xy_total = substract[:,0]+ substract[:,1]
        if xy_total.min == 0:
            return given_point
        else:
            return given_mask[np.argmin(xy_total)]  
                      


    def array_sort(self,arr , axis = 'x'):
        if axis == 'x':
            return arr[np.argsort(arr[:, 0])]
        else:
            return arr[np.argsort(arr[:, 1])]
    def sort_rectangle(self,rectangle):
        left_ = self.array_sort(rectangle, axis = 'x')[:2]
        right_= self.array_sort(rectangle, axis = 'x')[2:]
        
        left_ = self.array_sort(left_, axis = 'y')
        right_ = self.array_sort(right_, axis = 'y')


        return np.asarray(
            [
                left_[0], left_[1], right_[0], right_[1]
            ]
        )    
    
    def mask_processing(self,point_cloud,min_depth, max_depth):
    
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
                cv2.fillPoly(mask_, pts = [cnt],  color = (255,255,255))
        points_ = cnt_list
        mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((13, 13), np.uint8))
        mask_ = cv2.morphologyEx(mask_.astype(np.uint8), cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))

        mask = mask_
        # rbox = cv2.minAreaRect(points_[0])
        # if rbox[1][1]>rbox[1][0]:
        #     print( 90 - rbox[-1])
        # else:
        #     print(rbox[-1])
        # kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13,13))
        # mask_ = cv2.morphologyEx(mask_, cv2.MORPH_OPEN, kernel)

        # cv2.imshow('output', mask_)
        # cv2.waitKey(1)



        if points_:
            points = points_[0][:,0,:]
        else:
            points = np.dstack([points_index[1], points_index[0]])[0]    

        # print(1/ (time.time() - start_))
        # cv2.imshow('mask_', mask)
        # cv2.waitKey(1)

        return mask, points


    def find_rectangle(self, point_cloud,min_depth, max_depth):
        # Extract non-zero depth values and their (x, y) coordinates.
        mask, points = self.mask_processing(point_cloud,min_depth, max_depth)
        x,y,w,h = cv2.boundingRect(mask.astype(np.uint8))

        rectangle = np.asarray([
                [x,y],
                [x+w, y],
                [x,y+h],
                [x+w, y+h]
                ]
        ) 

        mask_idx = points

        if len(mask_idx) >0 :
            img__, angle = self.poseDifference(mask,points)
            # print(angle)
        else:
            img__ = self.image
            angle = None
#        cv2.imshow('img',img__)
        if len(rectangle) == 0:
            rectangle = np.asarray([
                    [0,0],
                    [0 , 0],
                    [0,0],
                    [0, 0]
                    ]
            ) 

        rectangle = self.sort_rectangle(rectangle)

        base_list = []

        for p in rectangle:
            try:
                x,y = self.find_closest_corner(p, points)
                # print(1/(time.time() - start_))

            except:
                x,y = 0 ,0 
            base_list.append((x,y))

        base_array = np.asarray(base_list)        

        return base_array,angle

    def poseDifference(self, currentImg,mask):

        rows,cols = currentImg.shape[:2]
        # [vx,vy,x,y] = cv2.fitLine(np.array(finalMask), cv2.DIST_L2,0,0.01,0.01)
        [vx,vy,x,y] = cv2.fitLine(np.array(mask), cv2.DIST_L2,0,0.01,0.01)

        angle_rad = math.atan2(vy, vx)
        radFixed = math.degrees(angle_rad)

        radFixed = abs(radFixed)

        return currentImg,radFixed


    def detect_dmenssion(self):
        """
            Input:
                 point_cloud(None crop): array
            Output:
                rectangle_array: rectangle pixel location in origin image.
                center: rectangle ceter pixel location in origin image.
                object_data: dict ,  {'Width': shorest length in top view surface, 
                                                'Length': Largest length in top view surface, 
                                                'Height': Height of the box, 
                                                'Box_id': box_id}

        
        """
        point_cloud = self.point_cloud
                
        pc_crop = point_cloud[self.ymin:self.ymax, self.xmin:self.xmax]
        min_depth, max_depth = self.depth_filter(pc_crop)


        rectangle_array,angle = self.find_rectangle(pc_crop, min_depth, max_depth)
        # print(1/(time.time() - start_))
  
        pc_rectangle = pc_crop[rectangle_array[:,1], rectangle_array[:,0], :2]
        rectangle_array += np.asarray([self.xmin, self.ymin])

        return [rectangle_array, pc_rectangle, min_depth, max_depth,angle]
    
    
    def get_dimenssion(self, pc_rectangle, min_depth):
        x = np.sqrt(np.sum((pc_rectangle[2] - pc_rectangle[0])**2))       
        y = np.sqrt(np.sum((pc_rectangle[1] - pc_rectangle[0])**2))
        
        box_height = self.height - min_depth
        if x>y:
            w = y/10
            l = x/10
        else:
            w = x/10
            l = y/10

        ## For Better accuracy
        h = box_height/10 + 0.5
        return w, l, h

    def classification(self,w,l,h):
        sort_df = self.true
        if self.method == 'pd':
    
            df_ = sort_df[['width', 'length', 'height']]
        else:


            df_ = sort_df[:, 1:4]

        arr_ori = np.asarray([[w,l,h],
                    [w,h,l],
                    [h,w,l],
                    [h,l,w],
                    [l,w,h],
                    [l,h,w]

        ])

        for idx, arr in enumerate(arr_ori):
            d = np.sum((arr -  df_)**2, axis = 1)
            if idx ==0:
                min_ = d.min()
                if self.method == 'pd':

                    box_id = sort_df.iloc[np.argmin(d)]['box_id']
                else:
                    box_id = sort_df[np.argmin(d)][0]
                min_idx = np.argmin(d)
            else:
                if d.min() < min_:

                    min_ = d.min()
                    if self.method == 'pd':

                        box_id = sort_df.iloc[np.argmin(d)]['box_id']
                    else:
                        box_id = sort_df[np.argmin(d)][0]
                    min_idx = np.argmin(d)
        value =[0,1,2]
        if self.method == 'pd':

            true_box = self.true.iloc[min_idx]
            h_idx = np.argmin(abs(true_box.iloc[1:4] - h))
            h = true_box.iloc[h_idx +1 ]
            value.remove(h_idx)
            x = true_box.iloc[value[0] +1 ]
            y = true_box.iloc[value[1] +1 ]
        else:
            true_box = self.true[min_idx]
            h_idx = np.argmin(abs(true_box[1:4] - h))
            h = true_box[h_idx +1 ]
            value.remove(h_idx)
            x = true_box[value[0] +1 ]
            y = true_box[value[1] +1 ]
        
        return box_id, x,y 


    def get_result(self):

        rectangle_array, pc_rectangle, min_depth, max_depth,angle = self.detect_dmenssion()

        w,l, h = self.get_dimenssion(pc_rectangle, min_depth=min_depth)
        
        box_id, true_x, true_y = self.classification(w,l,h) 
        if not angle:
            angle = 0 
        if abs(angle) >= 50:
            angle = 1
        else:
            angle = 0
        box_id = str(int(box_id))
        return {'box_id': box_id, 'angle': angle, 'rectangle':rectangle_array}      
    
