# import modin.pandas as pd # https://www.kdnuggets.com/2019/11/speed-up-pandas-4x.html
import pandas as pd
import os
import random
# import matplotlib
# matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import imageio.v2 as imageio
from config import ConfigOnline as Config
import time
import threading
import main_camera 
import cProfile

class BoxDataManager:
    def __init__(self, final2d_csv, ga_csv):
        self.final2d_df = pd.read_csv(final2d_csv)
        self.GA_df = pd.read_csv(ga_csv)
        # Filter the GA_df DataFrame to only include boxes from Bin 1
        self.GA_df = self.GA_df[self.GA_df['bin_name'] == 1]
        self.max_depth = self.final2d_df['depth'].max()
        self.ordered_box_ids = self.GA_df['matched_box_name'].tolist()
        self.z_cog_sums = {}
        self.box_data = []
        self.GA_df['processed'] = False  # Add a new column to mark processed boxes

    def update_z_cog(self, box_id, x_cog, y_cog):
        # Use a tuple of X_cog and Y_cog as the key to identify each location
        location_key = (x_cog, y_cog)
        # If the location is new, initialize its Z_cog sum
        if location_key not in self.z_cog_sums:
            self.z_cog_sums[location_key] = 0
        # Update the Z_cog sum for this location
        z_cog_addition = self.final2d_df.loc[self.final2d_df['matched_box_name'] == box_id, 'Z_cog'].iloc[0]
        self.z_cog_sums[location_key] += z_cog_addition
        return self.z_cog_sums[location_key]

    def get_box_details_from_GA(self, box_id):
        # Rename the column
        self.GA_df.rename(columns={'matched_box_name': 'box_id'}, inplace=True)
        # Filter out processed boxes and get the row for the specified box_id
        box_row = self.GA_df[(self.GA_df['box_id'] == box_id) & (~self.GA_df['processed'])]
        if box_row.empty:
            return None
        position = box_row[['bin_name', 'box_id', 'conveyor_x', 'conveyor_y', 'conveyor_z', 'X_cog', 'Y_cog', 'Z_cog', 'orientation', 'layer', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth']].iloc[0].to_dict()
        # position = box_row.iloc[0][['bin_name', 'matched_box_name', 'conveyor_x', 'conveyor_y', 'conveyor_z', 'X_cog', 'Y_cog', 'Z_cog', 'orientation', 'layer', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth']].to_dict()
        position['bin_name'] = str(position['bin_name'])
        # Mark the box as processed
        self.GA_df.loc[box_row.index[0], 'processed'] = True
        return position
    
    def generate_error_position(self, box_id, box_row, depth):
        return {
                'bin_name': 'error',
                'box_id': box_id,
                'conveyor_x' : box_row['conveyor_x'].iloc[0],
                'conveyor_y' : box_row['conveyor_y'].iloc[0],
                'conveyor_z' : box_row['conveyor_z'].iloc[0],
                'X_cog': 0,
                'Y_cog': 0,
                'Z_cog': 0,
                'orientation': 0,
                'position_x': 0,
                'position_y': 0,
                'position_z': 0,
                'width': box_row['width'].iloc[0],
                'height': box_row['height'].iloc[0],
                'depth': depth
            }
    
    def generate_position_dict(self, box_id, box_row, new_z_cog, depth):
        return {
            'bin_name': str(box_row['bin_name'].iloc[0]),
            'box_id': box_id,
            # 'matched_box_name': box_row['matched_box_name'].iloc[0],
            'conveyor_x': box_row['conveyor_x'].iloc[0],
            'conveyor_y': box_row['conveyor_y'].iloc[0],
            'conveyor_z': box_row['conveyor_z'].iloc[0],
            'X_cog': box_row['X_cog'].iloc[0],
            'Y_cog': box_row['Y_cog'].iloc[0],
            'Z_cog': new_z_cog,
            'orientation': box_row['orientation'].iloc[0],
            'position_x': box_row['position_x'].iloc[0],
            'position_y': box_row['position_y'].iloc[0],
            'position_z': new_z_cog - depth, # Adjusting Z position to be the bottom of the box
            'width': box_row['width'].iloc[0],
            'height': box_row['height'].iloc[0],
            'depth': depth
        }

    def get_box_position(self, box_id, ordered=False):
        # Choose the DataFrame based on whether the box is ordered
        box_df = self.GA_df if ordered else self.final2d_df
        # Filter the DataFrame for the specified box_id
        box_row = box_df[box_df['matched_box_name'] == box_id]
        if box_row.empty:
            return None
        # Extract the depth for the current box
        depth = box_row.iloc[0]['depth']
        # Update the Z_cog based on previous boxes at this location
        new_z_cog = self.update_z_cog(box_id, box_row.iloc[0]['X_cog'], box_row.iloc[0]['Y_cog'])
        # Check if the new Z_cog exceeds twice the minimum depth
        if not ordered and new_z_cog > 2 * self.max_depth:
            return self.generate_error_position(box_id, box_row, depth)
        return self.generate_position_dict(box_id, box_row, new_z_cog, depth)
            
    def process_box(self, box_id):
        processed_boxes_df = pd.DataFrame(columns=self.GA_df.columns)
        box_rows = self.GA_df[(self.GA_df['matched_box_name'] == box_id) & (~self.GA_df['processed'])]
        if box_rows.empty:
            return None
        box_row = box_rows.iloc[0]
        self.GA_df.loc[box_row.name, 'processed'] = True  # Mark the box as processed
        # Remove the box from the main DataFrame
        self.GA_df = self.GA_df.drop(box_row.name)
        # Add the box to the processed boxes DataFrame
        processed_boxes_df = pd.concat([processed_boxes_df, pd.DataFrame([box_row])], ignore_index=True)
        return box_row.to_dict()

class Visualization:
    def __init__(self):
        pass

    def draw_box(self, ax, position):
        """Draws a 3D box on the provided Axes object."""
        x, y, z = position['position_x'], position['position_y'], position['position_z']
        dx, dy, dz = position['width'], position['height'], position['depth']
        ax.bar3d(x, y, z, dx, dy, dz, alpha=0.5)

    def update_visualization(self, box_data, filename):
        plt.ion()
        fig = plt.figure(figsize=(12, 6))  # Adjust as needed
        # Filter out 'error' bins
        filtered_box_data = [position for position in box_data if position['bin_name'] != 'error']
        unique_bins = set(str(position['bin_name']) for position in filtered_box_data)
        axes = {}
        for position in box_data:
            if position['bin_name'] != 'error':
                bin_name_str = str(position['bin_name'])
                if bin_name_str not in axes:
                    # If the bin does not have a subplot, create one
                    ax = fig.add_subplot(1, len(unique_bins), len(axes) + 1, projection='3d')  # Adjust subplot position dynamically
                    ax.set_title(f'Bin {bin_name_str}')
                    ax.set_xlim([0, Config.container_width])
                    ax.set_ylim([0, Config.container_height])
                    ax.set_zlim([0, Config.container_depth])
                    axes[bin_name_str] = ax

                # Draw the box in the corresponding bin
                self.draw_box(axes[bin_name_str], position)

        plt.savefig(filename)
        plt.draw()
        plt.pause(3)
        plt.close()

class Application:
    def __init__(self, box_data_manager, visualizer, result_folder):
        self.step_images = [] # Keep track of each step
        self.image_filenames = [] #keep track of filenames
        self.box_data_manager = box_data_manager
        self.visualizer = visualizer
        self.result_folder = result_folder
        if not os.path.exists(self.result_folder):
            os.makedirs(self.result_folder)

    def update_csv_file(self):
        """Update the CSV file with the current box positions."""
        box_data_df = pd.DataFrame(self.box_data_manager.box_data)
        box_data_df.to_csv('updated_box_positions.csv', index=False)
        print("Data saved to 'updated_box_positions.csv'.")

    def run(self):
        # self.box_data_manager.load_conveyor_positions(Config.FINAL2D_CSV)
        last_line_processed = 0
        while True:
            try:
                with open('detected_boxes.csv', 'r') as file:
                    lines = file.readlines()
                if len(lines) > last_line_processed + 1:  # Check for new line
                    for line in lines[last_line_processed + 1:]:
                        box_id = line.strip().split(',')[0]  # Get only the first element
                        if box_id.lower() == 'exit':
                            break
                        # Check if the box ID is the next in the order list
                        if self.box_data_manager.ordered_box_ids and box_id == self.box_data_manager.ordered_box_ids[0]:
                            ordered = True
                            # Use data directly from GA_df
                            position = self.box_data_manager.get_box_details_from_GA(box_id)
                            position['bin_name'] = str(position['bin_name'])
                            position['bin_name'] = "GA"
                            self.box_data_manager.ordered_box_ids.pop(0)  # Remove the box ID from the order list
                        else:
                            ordered = False
                            # Use your existing logic to get the position
                            position = self.box_data_manager.get_box_position(box_id)
                        if position:
                            print(position)
                            self.box_data_manager.box_data.append(position)
                            # Update the CSV file with the new box position
                            self.update_csv_file()
                            # Generate the filename for the current step
                            filename = f'{Config.result_folder}/step_{len(self.step_images) + 1}.png'
                            print(f"Saving image to: {filename}")  # Debugging line
                            self.visualizer.update_visualization(self.box_data_manager.box_data, filename)
                            if os.path.exists(filename):
                                print(f"File {filename} created successfully.")  # Debugging line
                            else:
                                print(f"Failed to create file {filename}.")  # Debugging line
                            self.step_images.append(filename)
                        else:
                            print(f"Box ID {box_id} not found. Please enter a valid box ID.")

                        last_line_processed += 1

                time.sleep(1)  # Pause for a moment to avoid continuous file reading

            except KeyError as e:
                print(f"KeyError: The field '{e.args[0]}' is missing for box ID {box_id}.")
            except Exception as e:
                print(f"Exception: {e}")
                time.sleep(1)  # Pause in case of an exception

            with imageio.get_writer(f'{Config.result_folder}/box_animation.gif', mode='I', duration=500) as writer:
                for filename in self.step_images:
                    image = imageio.imread(filename)
                    writer.append_data(image)

def run_camera():
    main_camera.main()

def main():
    camera_thread = threading.Thread(target=run_camera)
    camera_thread.start()  # Start the camera processing in a separate thread
    box_data_manager = BoxDataManager(Config.FINAL2D_CSV, Config.GA_CSV)
    visualizer = Visualization()
    app = Application(box_data_manager, visualizer, Config.result_folder)
    app.run()
    camera_thread.join()  # Optionally wait for the camera thread to finish

if __name__ == "__main__":
    try:
        main()
        # cProfile.run('main()')
    except KeyboardInterrupt:
        pass