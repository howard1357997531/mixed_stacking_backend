
import pyrealsense2 as rs
import numpy as np
import time


class L515:
    def __init__(self,config):
        #init setting
        self.resolution=[1920,1080]
        self.cameraStatus=False
        self.serialNumber=None
        #income setting
        if 'resolution' in config:
            self.resolution=config['resolution']
        if 'SerialNumber' in config:
            self.serialNumber=config['SerialNumber']
        #camera init
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.pc = rs.pointcloud()

        self.pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        self.pipeline_profile = self.config.resolve(self.pipeline_wrapper)
        self.device = self.pipeline_profile.get_device()
        self.device_product_line = str(self.device.get_info(rs.camera_info.product_line))


        #Camera setting
#        self.config.enable_stream(rs.stream.depth,self.resolution[0], self.resolution[1], rs.format.z16, 30)
        self.config.enable_stream(rs.stream.depth, 1024, 768, rs.format.z16, 30)

        self.config.enable_stream(rs.stream.color, self.resolution[0], self.resolution[1], rs.format.rgb8, 30)
        self.config.enable_stream(rs.stream.infrared, 1024, 768,  rs.format.y8, 30)

        if self.serialNumber is not None:
            self.config.enable_device(self.serialNumber)

        self.cameraSensor = self.device.query_sensors()[1]

        self.depth_sensor = self.device.first_depth_sensor()
        
 
        self.depth_sensor.set_option(rs.option.visual_preset, 5) # 5 is short range, 3 is low ambient light
        self.depth_sensor.set_option(rs.option.enable_max_usable_range, 0) # 0 is for disabling
        self.depth_sensor.set_option(rs.option.receiver_gain,18)
        self.depth_sensor.set_option(rs.option.laser_power,30)
        self.depth_sensor.set_option(rs.option.confidence_threshold, 3) # Adjustable between 0-3
        self.depth_sensor.set_option(rs.option.noise_filtering, 6) # 6 is the highest I think
        self.depth_scale = self.depth_sensor.get_depth_scale() # convert depth values to real-world units

        #self.cameraSensor.set_option(rs.option.exposure,300)
        self.align_to = rs.stream.color
        self.align = rs.align(self.align_to)
        
    def openCamera(self):
        try:          
            self.pipeline.start(self.config)
            # Skip 5 first frames to give the Auto-Exposure time to adjust
            for x in range(5):
                self.pipeline.wait_for_frames()
            self.cameraStatus=True
        except:
            print('open camera error')
            raise
    
    def closeCamera(self):
        try:
            self.pipeline.stop()
            self.cameraStatus=False
        except:
            print('close camera error')
            raise
    def capture_frames(self, pipeline, align, skip=5): # Skip 5 first frames to give the Auto-Exposure time to adjust
        for _ in range(skip):
            pipeline.wait_for_frames()
        frames = pipeline.wait_for_frames()
        return align.process(frames) # Align the depth frame to color frame            
    def depth_filter(self, depth_frame):
        threshold_filter = rs.threshold_filter(min_dist=0.3, max_dist=0.49)
        depth_frame = threshold_filter.process(depth_frame)
        decimation = rs.decimation_filter(magnitude=1)
        depth_frame = decimation.process(depth_frame)
        spatial = rs.spatial_filter(smooth_alpha= 0.25, smooth_delta= 20, magnitude= 1, hole_fill= 0)
        depth_frame = spatial.process(depth_frame)
        temporal = rs.temporal_filter(smooth_alpha=1, smooth_delta=90, persistence_control=7)
        depth_frame = temporal.process(depth_frame)     

        return depth_frame  
    def getData(self):
        while True:
            if self.cameraStatus:
                
                startTime = time.time()
                aligned_frames = self.capture_frames(self.pipeline, self.align)
#                frames = self.pipeline.wait_for_frames()
#                aligned_frames = self.align.process(frames)
                colorFrame = aligned_frames.get_color_frame()
                colorImage = np.asanyarray(colorFrame.get_data())


                depthFrame = aligned_frames.get_depth_frame()
                depthFrame = self.depth_filter(depthFrame)

                pointCloudData = self.pc.calculate(depthFrame)
                pointCloudData = pointCloudData.get_vertices()
                pointCloudData = np.asanyarray(pointCloudData).view(np.float32).reshape(self.resolution[1],self.resolution[0],3)*1000

                endTime = time.time()-startTime
                yield [colorImage,pointCloudData, np.asarray(depthFrame.get_data()).reshape(self.resolution[::-1])]
                # yield [colorImage,pointCloudData, depth_image]
            else:
                yield []
