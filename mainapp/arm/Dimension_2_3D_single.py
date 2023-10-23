import pandas as pd
import numpy as np
import cv2
import math
import time
from sklearn.linear_model import RANSACRegressor
import csv

# -------------
from django.conf import settings
import os

box_volume_path = os.path.join(settings.MEDIA_ROOT, 'camera', 'box_volume.csv')
# -------------

MIN_CONTOUR_AREA = 1000
class Dimension_2_3D():
    def __init__(self, crop = {'xmin' :320, 'xmax':1920,'ymin':50, 'ymax':1080, 'total height':790}, image = None):
        self.xmin = crop['xmin']
        self.xmax = crop['xmax']
        self.ymin = crop['ymin']
        self.ymax = crop['ymax']
        self.height = crop['total height']

        # self.boxes = self.load_boxes_from_csv('./box_volume.csv')
        self.boxes = self.load_boxes_from_csv(box_volume_path)

    def extract_white_area(self, rgb_frame):
        # 1. Extract white mask
        blurred = cv2.GaussianBlur(rgb_frame, (7,7), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        lower_thresh = np.array([75,10,130])
        upper_thresh = np.array([110,52,170])
        # lower_thresh, upper_thresh = self.get_hsv_from_trackbars()
        white_mask = cv2.inRange(hsv, lower_thresh, upper_thresh)
        # cv2.imshow('avg_mask',white_mask)

        # 2. Detect edges
        imgray = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(imgray, (7, 7), 100)
        thresh = cv2.threshold(blurred_image, 130, 255, cv2.THRESH_BINARY)[1]
        edges = cv2.Canny(thresh,50,150, L2gradient = True, apertureSize = 5)
        kernel = np.ones((1,1),np.uint8)
        edges = cv2.erode(edges, kernel, iterations=1)
        edges = cv2.dilate(edges, kernel, iterations=2)
        # 3. Average (or take median) of the masks
        avg_mask = (white_mask + edges) // 2
        # 4. Extract contours from avg_mask
        contours, _ = cv2.findContours(avg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > MIN_CONTOUR_AREA]
        desired_contour = None
        if contours:
            largest_contour = max(contours, key=cv2.contourArea)
            epsilon = 0.04 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            if len(approx) == 4:
                desired_contour = approx
            else:
                x, y, w, h = cv2.boundingRect(largest_contour)
                desired_contour = np.asarray([[x, y], [x + w, y], [x, y + h], [x + w, y + h]])
            if desired_contour is not None and len(desired_contour) > 0:
                cv2.drawContours(rgb_frame, [desired_contour], -1, (100, 255, 100), 2)

        return avg_mask, contours, desired_contour
    
    def crop_image(self, img):
        return img[self.ymin:self.ymax,self.xmin:self.xmax].copy()
    
    def extract_region_from_mask(self, original_img, mask):
        binary_mask = mask
        # Ensure that the mask is single-channel (grayscale)
        if len(binary_mask.shape) == 3:
            binary_mask = cv2.cvtColor(binary_mask, cv2.COLOR_BGR2GRAY)
        # Ensure the mask and the image have the same size
        assert binary_mask.shape == original_img.shape[:2], "The mask and the image should have the same dimensions!"
        binary_mask = binary_mask.astype(np.uint8) # mask is of type CV_8U
        extracted_region = cv2.bitwise_and(original_img, original_img, mask=binary_mask) # Extract region of interest
        return extracted_region
    def process_cropped_area(self, image,  depth_image):
        cropped = self.crop_image(image)
        depth_cropped = self.crop_image(depth_image)
        white_masked_cropped, contours, desired_contour = self.extract_white_area(cropped)
        depth_values_masked = np.zeros_like(depth_cropped)
        corners = np.array([])  # Empty array if no contour found.
        contour_mask = np.zeros_like(white_masked_cropped)
        if desired_contour is not None and len(desired_contour) > 0:
            contour_mask = cv2.drawContours(contour_mask, [desired_contour], -1, (255), thickness=cv2.FILLED)
        else:
            return [None]
        depth_values_masked = cv2.bitwise_and(depth_cropped, depth_cropped, mask=contour_mask)
        # cv2.imshow('depth_values_masked', depth_values_masked)
        corners = desired_contour.reshape(-1, 2)
        white_masked_cropped_colored = cv2.cvtColor(white_masked_cropped, cv2.COLOR_GRAY2BGR)
        
        result = np.zeros_like(depth_image)
        real_content_cropped = self.extract_region_from_mask(cropped, white_masked_cropped_colored)
        # cv2.imshow('real_content_cropped', real_content_cropped)

        # cv2.waitKey(1)

        return result, contours, depth_values_masked, corners, real_content_cropped
    
    def draw_contours_on_full_image(self, image, contours, crop_offset):
        for contour in contours:
            for point in contour:
                point[0][0] += crop_offset[0]  # adding x offset
                point[0][1] += crop_offset[1]  # adding y offset
        cv2.drawContours(image, contours, -1, (0, 255, 0), 3)
        return image
    
    def remove_outliers_using_iqr(self, data):
        Q1 = np.percentile(data, 15)
        Q3 = np.percentile(data, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        return data[(data >= lower_bound) & (data <= upper_bound)]
        
    def pixel_to_real_world_dimensions(self, masked_points):
        # Use RANSAC to fit a plane to the point cloud

        ransac = RANSACRegressor(min_samples=10, residual_threshold=1, random_state=0)
        # masked_points /= masked_points
        masked_points /= 1000

        ransac.fit(masked_points[:, :2], masked_points[:, 2])  # Using x and y to predict z
        inlier_mask = ransac.inlier_mask_
        # Filter the point cloud using inlier mask
        inlier_points = masked_points[inlier_mask]
        # Get the 3D coordinates from the inlier_points
        x_coords = inlier_points[:, 0]
        y_coords = inlier_points[:, 1]
        z_coords = inlier_points[:, 2]
        # Remove outliers using IQR
        x_coords = self.remove_outliers_using_iqr(x_coords)
        y_coords = self.remove_outliers_using_iqr(y_coords)
        z_coords = self.remove_outliers_using_iqr(z_coords)
        # Calculate the centroid of the point cloud
        centroid_x = np.mean(x_coords)
        centroid_y = np.mean(y_coords)
        centroid_z = np.mean(z_coords)
        # Calculate average distances from centroid
        # avg_distance_to_centroid_x = np.mean(np.abs(x_coords - centroid_x))
        # avg_distance_to_centroid_y = np.mean(np.abs(y_coords - centroid_y))

        avg_distance_to_centroid_x = np.abs(x_coords - centroid_x).mean()
        avg_distance_to_centroid_y = np.abs(y_coords - centroid_y).mean()


        # avg_distance_to_centroid_z = np.mean(np.abs(z_coords - centroid_z))
        
        # Use the average distances to calculate X, Y, and Z
        # X = 4* avg_distance_to_centroid_x/1000 
        # Y = 4 * avg_distance_to_centroid_y/1000
        # Z = 0.512 - centroid_z/1000  # Adjusting Z based on centroid rather than mean of all points
        # return X * 100, Y * 100, Z * 100  - 0.42


        X = 4 * avg_distance_to_centroid_x 
        Y = 4 * avg_distance_to_centroid_y
        Z = 0.512 - centroid_z  # Adjusting Z based on centroid rather than mean of all points
        return X * 100, Y * 100, Z * 100 - 0.32
    



    def identify_box(self, X, Y, Z, boxes):
        if X is None or Y is None or Z is None:
            return None
        if X < Y:
            X, Y = Y, X
        X = float(X)
        Y = float(Y)
        Z = float(Z)
        detected_area = X * Y
        detected_volume = detected_area * Z
        best_score = float('inf')
        best_match = None

        for box in boxes:
            width_difference = abs(float(box['width']) - X)
            length_difference = abs(float(box['length']) - Y)
            height_difference = abs(float(box['height']) - Z)
            volume_difference = abs(float(box['Volume']) - detected_volume)
            area_difference = abs(float(box['Area']) - detected_area)
            # Normalize differences. adjust the normalization factors based on your specific requirements.
            normalized_width_difference = width_difference / 0.98
            normalized_length_difference = length_difference / 2.6
            normalized_height_difference = height_difference / 0.25
            normalized_area_difference = area_difference / 34
            normalized_volume_difference = volume_difference /11
            
            total_score = (normalized_area_difference + 2*normalized_width_difference + 0.3*normalized_length_difference +
                        normalized_volume_difference + normalized_height_difference)
            if total_score < best_score:
                best_score = total_score
                best_match = box

        return best_match['box_id'] if best_match else None    
    def load_boxes_from_csv(self, filename):
        boxes = []
        with open(filename, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                box = {
                    'box_id': row['box_id'],
                    'width': float(row['width']),
                    'length': float(row['length']),
                    'height': float(row['height']),
                    'Area': float(row['Area']),
                    'Volume': float(row['Volume'])
                }
                boxes.append(box)
        return boxes
    
    def get_dimenssion(self, point_cloud, full_depth_mask):

        vertices =  point_cloud.reshape(-1, 3)
        vertices = vertices[::5,:]
        full_depth_mask = full_depth_mask.flatten()[::5]
        masked_points = vertices[full_depth_mask!= 0] # Flattening the mask to match vertices shape.        
        # masked_points = vertices[full_depth_mask.flatten() != 0] # Flattening the mask to match vertices shape.        
        X, Y, Z = self.pixel_to_real_world_dimensions(masked_points)

        return X, Y, Z
    
    # def get_rect_angle(self, full_depth_mask, )


    def get_rect_angle(self,full_depth_mask):
        # pts = np.where(full_depth_mask != 0)
        # full_depth_mask[pts] = 255  
        
        # contours,_ = cv2.findContours(full_depth_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) 
        contours = self.contours + np.asarray([self.xmin, self.ymin])
        if len(contours) >1 :
            contours =  np.vstack(contours)

        # cv2.drawContours(self.image, contours, -1, (0,255,255), 3)
        rbox = cv2.minAreaRect(contours[0])
        
        if rbox[1][1]>rbox[1][0]:
            angle =  90 - rbox[-1]
        else:
            angle = rbox[-1]
        if angle > 90:
            angle = 180 - angle

        if angle > 55:
            angle = 1
        else:
            angle = 0

        rbox = np.int0(rbox[:2])
        x,y = rbox[0]
        h,w = rbox[1]
        w /= 2
        h /= 2

        rectangle = [ [int(x-w) ,int(y-h)], [int(x-w), int(y+h)], [int(x+w), int(y-h)], [int(x+w), int(y+h)]]


        return rectangle, angle

    def get_result(self, image, point_cloud, depth_image):
        pc = point_cloud.copy()
        self.image = image.copy()
        result  = self.process_cropped_area(image, depth_image)
        if result[0] is None:
        # if  self.white_masked_image is None:
            return None
        else:
            self.white_masked_image, self.contours, self.masked_depth_values, self.corners, self.real_content_image = result


        # self.white_masked_image = self.draw_contours_on_full_image(self.white_masked_image, self.contours, (self.xmin, self.ymin))
        #self.real_content_image = self.draw_contours_on_full_image(self.real_content_image, self.contours, (self.xmin, self.ymin))
        #cv2.imshow('', self.real_content_image)
        full_depth_mask = np.zeros(depth_image.shape, dtype=np.uint8)
        full_depth_mask[self.ymin:self.ymax , self.xmin :self.xmax ] = (self.masked_depth_values > 0).astype(np.uint8)

        X, Y, Z = self.get_dimenssion(pc, full_depth_mask)
        rectangle, angle = self.get_rect_angle(full_depth_mask)

        box_id = self.identify_box(X,Y,Z, self.boxes)

        return {'box_id': box_id, 'angle': angle, 'rectangle':rectangle}      
