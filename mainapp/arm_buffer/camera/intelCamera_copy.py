
import pyrealsense2 as rs
import numpy as np
import time


class L515:
    def __init__(self):
        self.cameraStatus = False
        self.configure_camera_settings()

    @property
    def depth_sensor(self):
        return self.pipeline_profile.get_device().first_depth_sensor()

    @property
    def camera_sensor(self):
        return self.pipeline_profile.get_device().query_sensors()[1]

    def configure_camera_settings(self):
        """Configures camera settings."""
        pipeline = rs.pipeline() # creates a new RealSense pipeline (manage streaming from RealSense devices)
        config = rs.config() # new configuration object for the pipeline (to define which streams to be used and the stream's properties)
        config.enable_stream(rs.stream.depth, 1024, 768, rs.format.z16, 30) # z16 format (16-bit depth)
        #config.enable_stream(rs.stream.color, 1920, 1080, rs.format.bgr8, 30) # bgr8 format (8-bit color in BGR format)
        config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 15)
        config.enable_stream(rs.stream.infrared, 1024, 768,  rs.format.y8, 30)
        self.config = config
        self.pipeline = pipeline        
        self.pipeline_wrapper = rs.pipeline_wrapper(self.pipeline)
        self.pipeline_profile = self.config.resolve(self.pipeline_wrapper) # resulting in a profile that will be compatible with the connected RealSense device
        
        
        device = self.pipeline_profile.get_device() # gives access to the actual RealSense device
        # Depth sensor settings
        depth_sensor = device.first_depth_sensor() # retrieves the first depth sensor of the device
        depth_sensor.set_option(rs.option.visual_preset, 5) # 5 is short range, 3 is low ambient light
        depth_sensor.set_option(rs.option.enable_max_usable_range, 0) # 0 is for disabling
        depth_sensor.set_option(rs.option.receiver_gain,18)
        depth_sensor.set_option(rs.option.laser_power,30)
        depth_sensor.set_option(rs.option.confidence_threshold, 3) # Adjustable between 0-3
        depth_sensor.set_option(rs.option.noise_filtering, 6) # 6 is the highest I think
        depth_scale = depth_sensor.get_depth_scale() # convert depth values to real-world units
        self.pc = rs.pointcloud()
        align_to = rs.stream.color
        self.align = rs.align(align_to)

    def capture_frames(self, pipeline, align, skip=5): # Skip 5 first frames to give the Auto-Exposure time to adjust
        for _ in range(skip):
            pipeline.wait_for_frames()
        frames = pipeline.wait_for_frames()
        return align.process(frames) # Align the depth frame to color frame
    

        
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
#                frames = self.pipeline.wait_for_frames()
                aligned_frames = self.capture_frames(self.pipeline, self.align)
                colorFrame = aligned_frames.get_color_frame()
                colorImage = np.asanyarray(colorFrame.get_data())


                depthFrame = aligned_frames.get_depth_frame()
                depthFrame = self.depth_filter(depthFrame)
                pc = rs.pointcloud()
                pointCloudData = pc.calculate(depthFrame)
                pointCloudData = pointCloudData.get_vertices()
                pointCloudData = np.asanyarray(pointCloudData).view(np.float32).reshape(720, 1280,3)*1000
                #pointCloudData = np.asanyarray(pointCloudData).view(np.float32).reshape(1080, 1920,3)*1000

                endTime = time.time()-startTime
                yield [colorImage,pointCloudData, np.asarray(depthFrame.get_data()).reshape(720,1280)]
                #yield [colorImage,pointCloudData, np.asarray(depthFrame.get_data()).reshape(1080,1920)]
                # yield [colorImage,pointCloudData, depth_image]
            else:
                yield []