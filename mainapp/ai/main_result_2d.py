import os
import time
import csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import imageio.v2 as imageio
import random
from collections import defaultdict
from .model_speed_2d import PlacementProcedure, BRKGA
from .config import Config2d as Config
# -------------------------
from django.conf import settings
import os
# -------------------------
class BoxProcessor:
    def __init__(self, total_boxes, total_bins, container_dims, safe_space):
        self.total_boxes = total_boxes
        self.total_bins = total_bins
        self.container_dims = container_dims
        self.safe_space = safe_space

    def load_and_process_data(self, csv_file_path):
        """Loads and processes the data from a CSV file."""
        inputs = {
        'v': [],  # boxes with different shape
        'V': [self.container_dims] * self.total_bins   # containers with fixed shape
        }
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            box_depths = {}  # This will map box types to their depths
            for idx, row in enumerate(reader):
                width, height = int(row['width']), int(row['height'])
                box_data = (width + self.safe_space, 
                            height + self.safe_space)
                quantity = int(Config.BOX_QUANTITY)
                inputs['v'].extend([box_data] * quantity)
        return inputs
    
    def process_boxes_from_csv(self, csv_path):
        """Processes box dimensions from a CSV file."""
        baseline_boxes = pd.read_csv(csv_path)
        baseline_boxes.rename(columns={'name': 'box_name'}, inplace = True)
        baseline_boxes.loc[:, ['width', 'height', 'depth']]  = baseline_boxes[['width', 'height', 'depth']].astype(int)
        baseline_boxes.loc[:, ['width', 'height']] = baseline_boxes[['width', 'height']] + Config.SAFE_SPACE
        # baseline_boxes.loc[:, 'depth'] = baseline_boxes['depth']
        return baseline_boxes

class DecodeBoxes:
    def __init__(self):
        pass
    def decode_box(self, decoder, output_file):
        """Decodes the boxes from a CSV file and save them to another CSV file."""
        box_data = []
        for bin_index in range(decoder.num_opend_bins):
            for box_index, box in enumerate(decoder.Bins[bin_index].load_items):
                position = box[0]  # Get the box position
                dimensions = box[1] - box[0]  # Calculate box dimensions
                box_data.append([
                    f'{bin_index+1}',  # Add container information
                    f'{box_index+1}',  # Add box information
                    *map(int, np.round(position)), 
                    *map(int, dimensions)])
        with open(output_file, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['bin_name', 'box_name', 'position_x', 'position_y', 'width', 'height'])
            writer.writerows(box_data)

class VisualizeBoxes:
    def __init__(self, colormap='tab10', elev=75, azim=35):
        self.colormap = plt.get_cmap(colormap)
        self.elev = elev
        self.azim = azim

    def draw_box_2d(self, ax, position, size, facecolor='b', edgecolor='black', alpha=0.1, linewidth=1.5):
        px, py = position
        sx, sy = size
        return ax.add_patch(plt.Rectangle((px, py), sx, sy, facecolor=facecolor, edgecolor=edgecolor, alpha=alpha, linewidth=linewidth))
    
    def generate_random_color(self):
        """Generates a random color."""
        return [random.random() for _ in range(4)]
    
    def visualize_boxes_2d(self, box_data, container_data, result_folder, csv_base_name, normalize_colors=False, random_colors=False): 
        """Visualizes the boxes in a 2D plot."""
        images, drawn_boxes_objects = [], []
        current_bin_name, current_figure_num = None, 1
        ax, fig = None, None
        for index, row in box_data.iterrows():
            if 'bin_name' in box_data.columns:
                bin_name = row['bin_name']
                if bin_name != current_bin_name:
                    if current_figure_num > 1:
                        gif_name = f'all_boxes2d_{csv_base_name}_bin_{current_bin_name}.gif'
                        imageio.mimsave(os.path.join(result_folder, gif_name), images, duration=500)
                    # Create a new figure for the new bin
                    fig, ax= self.create_new_figure2d(container_data, bin_name)
                    # Reset the image list for the new bin
                    images = []
                    current_bin_name = bin_name
                    current_figure_num += 1
            position = row['position_x'], row['position_y']
            size = row['width'], row['height']
            matched_box_name = row['matched_box_name']  # Get the matched box name
            if normalize_colors:
                # Get the color from normalization color row
                self.draw_box_2d(ax, position, size, facecolor=row['color'], edgecolor = 'black', alpha=1)
            elif random_colors:
                random_color = self.generate_random_color()
                self.draw_box_2d(ax, position, size, facecolor=random_color, edgecolor = 'black', alpha=1)
            else:
                # Change color of the last drawn box to red and others blue for UI
                if drawn_boxes_objects:
                    drawn_boxes_objects[-1].set_facecolor('blue')
                box_obj = self.draw_box_2d(ax, position, size, facecolor='red', edgecolor = 'black', alpha=1)
                drawn_boxes_objects.append(box_obj)
            ax.set_title(f'Box2d {index+1} in Bin: {bin_name}')
            # Add text annotation for matched_box_name
            ax.text(position[0] + size[0]/2, position[1] + size[1]/2, matched_box_name,
                    ha='center', va='center', fontsize=18, color='black', alpha=1)
            img_path = os.path.join(result_folder, f'box2d{index+1}_bin_{bin_name}.png')
            plt.savefig(img_path)
            # Add to the list of images
            images.append(imageio.imread(img_path))
        # Save the figure of the last bin
        if current_figure_num > 1:
            self.save_gif2d(result_folder, csv_base_name, current_bin_name, images)

    def create_new_figure2d(self, container_data, bin_name):
        """Creates a new matplotlib figure for a bin."""
        fig, ax = plt.subplots()
        ax.set_aspect('equal', 'box')  # Make the scale of x, y, and z axes the same
        ax.set_xlim([0, container_data[0][0]])  # Set x limit
        ax.set_ylim([0, container_data[0][1]])  # Set y limit
        self.draw_box_2d(ax, [0, 0], container_data[0] , facecolor='grey', edgecolor='grey', alpha=0)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_title(f'Boxes in Bin: {bin_name}')
        return fig, ax

    def save_gif2d(self, result_folder, csv_base_name, bin_name, images):
        gif_name = f'all_boxes2d_{csv_base_name}_bin_{bin_name}.gif'
        imageio.mimsave(os.path.join(result_folder, gif_name), images, duration=500)

    def save_image2d(self, result_folder, index, bin_name, prefix):
        img_path = os.path.join(result_folder, f'{prefix}{index+1}_bin_{bin_name}.png')
        plt.savefig(img_path)
        return img_path
    
    def draw_box_3d(self, ax, position, size, color='b', alpha=0.1):
        px, py, pz = position
        sx, sy, sz = size
        box_obj = ax.bar3d(px, py, pz, sx, sy, sz, color=color, shade=False, alpha=alpha, edgecolor='black', linewidth=1.5)
        return box_obj  # Return the drawn object

    def visualize_boxes_3d(self, box_data, container_data, result_folder, csv_base_name, normalize_colors=False, random_colors=False): 
        """Visualizes the boxes in a 3D plot."""
        current_bin_name = None
        for index, row in box_data.iterrows():
            bin_name = row['bin_name']
            if bin_name != current_bin_name:
                # Create a new figure for the new bin
                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')
                ax.set_box_aspect([1,1,1])  # Make the scale of x, y, and z axes the same
                ax.set_xlim([0, container_data[0]])  # Set x limit
                ax.set_ylim([0, container_data[1]])  # Set y limit
                ax.set_zlim([0, container_data[2]])  # Set z limit
                ax.view_init(elev=75., azim=35)  # Change the viewpoint
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_title(f'Boxes in Bin: {bin_name}')
                current_bin_name = bin_name

            position = (row['position_x'], row['position_y'], row['position_z'])
            size = (row['width'], row['height'], row['depth'])

            if normalize_colors:
                color = row['color']
            elif random_colors:
                color = self.generate_random_color()
            else:
                color = 'red'  # Default color if neither normalization nor random colors are used

            self.draw_box_3d(ax, position, size, color=color, alpha=1)

            if index == len(box_data) - 1 or box_data.iloc[index + 1]['bin_name'] != bin_name:
                # Save the figure when the last box of the bin is processed
                plt.savefig(os.path.join(result_folder, f'{csv_base_name}_bin_{bin_name}.png'))
                plt.close(fig)
        # print("3D visualizations saved.")

    def create_new_figure3d(self, container_data, bin_name):
        """Creates a new matplotlib figure for a bin."""
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_box_aspect([1,1,1])
        ax.set_xlim([0, container_data[0][0]])
        ax.set_ylim([0, container_data[0][1]])
        ax.set_zlim([0, container_data[0][2]])
        ax.view_init(elev=self.elev, azim=self.azim)
        ax.set_title(f'Boxes in Bin: {bin_name}')
        self.draw_box(ax, [0, 0, 0], container_data[0], color='grey', alpha=0)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        return fig, ax

class CSVgenerator:
    def __init__(self, tolerance=0.01, colormap='bwr'):
        self.tolerance = tolerance
        self.colormap = plt.get_cmap(colormap)

    def match_box_name(self, width, height, baseline_boxes, tolerance=0.01, used_counts=None):
        """Matches the matched_box_name and orientation of boxes based on width and height order."""
        if used_counts is None:
            used_counts = defaultdict(lambda: 0)  # Tracks the count of each name used

        potential_matches = []
        for i, baseline_row in baseline_boxes.iterrows():
            if abs(width - baseline_row['width']) <= tolerance and abs(height - baseline_row['height']) <= tolerance:
                potential_matches.append((baseline_row['box_name'], 0))
            elif abs(width - baseline_row['height']) <= tolerance and abs(height - baseline_row['width']) <= tolerance:
                potential_matches.append((baseline_row['box_name'], 1))

        # Filter potential matches to those that have been used less than twice
        potential_matches = [match for match in potential_matches if used_counts[match[0]] < Config.BOX_QUANTITY]

        if potential_matches:
            selected_match = np.random.choice([match[0] for match in potential_matches])
            orientation = next(match[1] for match in potential_matches if match[0] == selected_match)
            used_counts[selected_match] += 1  # Increment the count for this name
            return selected_match, orientation
        return None, None

    def match_box_data(self, box_data, baseline_boxes):
        """Generating a DataFrame with the matched boxes."""
        used_counts = defaultdict(lambda: 0)
        box_data.loc[:, ['width', 'height']] = box_data[['width', 'height']].astype(int)
        # Calculate box volumes and normalize colors
        box_volumes = box_data['width'] * box_data['height'] 
        normalized_colors = self.normalize_colors(box_volumes)
        box_data['color'] = normalized_colors
        box_data['X_cog'] = box_data['position_x'] + box_data['width'] / 2
        box_data['Y_cog'] = box_data['position_y'] + box_data['height'] / 2
        # Sort the boxes
        if 'bin_name' in box_data.columns:
            box_data = box_data.sort_values(by=['bin_name', 'position_y', 'position_x']).reset_index(drop=True)
        else:
            box_data = box_data.sort_values(by=['position_y', 'position_x']).reset_index(drop=True)

        for index, row in box_data.iterrows():
            matched_box_name, orientation = self.match_box_name(int(row['width']), int(row['height']), baseline_boxes, tolerance=1, used_counts=used_counts)
            box_data.loc[index, 'matched_box_name'] = matched_box_name
            if matched_box_name is not None:
                box_data.loc[index, 'orientation'] = orientation
                # Find the depth from the baseline_boxes DataFrame
                matched_depth = baseline_boxes[baseline_boxes['box_name'] == matched_box_name]['depth'].values[0]
                box_data.loc[index, 'depth'] = matched_depth
        box_data['Z_cog'] = box_data['depth']
        return box_data

    def normalize_colors(self, box_volumes):
        """Generating a list of normalized colors."""
        max_volume = box_volumes.max()
        min_volume = box_volumes.min()
        normalized_colors = []
        colormap = plt.get_cmap('bwr')
        for volume in box_volumes:
            if max_volume != min_volume:
                normalized_volume = 0.1 + 0.9 * (volume - min_volume) / (max_volume - min_volume)
            else:
                normalized_volume = 1 
            color = colormap(normalized_volume)
            normalized_colors.append(color)
        return normalized_colors

class SaveCSV:
    def __init__(self):
        CSV_generator = CSVgenerator()
        self.CSV_generator = CSV_generator

    def create_results_directory(self, base_name='result', use_timestamp=Config.CONFIG["resTime"]):
        """Creates a directory for saving results, with date and time as a unique identifier"""
        results_dir = f'{base_name}_{time.strftime("%Y%m%d_%H%M%S")}' if use_timestamp else base_name
        os.makedirs(results_dir, exist_ok=True)
        return results_dir
    
    #----------------------------------
    def create_results_directory_django(self, worklist_id):
        results_dir = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{worklist_id}')
        os.makedirs(results_dir, exist_ok=True)
        return results_dir
    #----------------------------------
    
    def save_data_to_csv(self, box_data, result_folder, csv_base_name, baseline_boxes, SAFE_SPACE):
        """Saves the data to different CSV files for different aims."""
        save_path = os.path.join(result_folder, f'{csv_base_name}')
        
        # Adjust 'width' and 'height' by reducing the SAFE_SPACE
        box_data['width'] = box_data['width'] - SAFE_SPACE
        box_data['height'] = box_data['height'] - SAFE_SPACE

        # Adjust 'position_x' and 'position_y' by adding half of the SAFE_SPACE
        box_data['position_x'] = box_data['position_x'] + SAFE_SPACE / 2
        box_data['position_y'] = box_data['position_y'] + SAFE_SPACE / 2
        # Add 'position_z' column with a default value of 0
        box_data['position_z'] = 0

        # Add other columns for the position of taking box from conveyor
        box_data['conveyor_x'] = box_data['width']/2
        box_data['conveyor_y'] = box_data['height']/2
        box_data['conveyor_z'] = box_data['depth']
        rotation_mask = box_data['orientation'] == 1
        box_data.loc[rotation_mask, ['conveyor_x', 'conveyor_y']] = box_data.loc[rotation_mask, ['conveyor_y', 'conveyor_x']].values

        # Create a new DataFrame with only the columns for position of putting box in the palette
        output_data = box_data[['bin_name', 'matched_box_name', 'conveyor_x', 'conveyor_y', 'conveyor_z', 'X_cog', 'Y_cog', 'Z_cog', 'orientation', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth']]
        final_save_path = save_path.rsplit('.', 1)[0] + '_final.csv'
        print(f"Saving file to {final_save_path}")
        output_data.to_csv(final_save_path, index=False)

class BoxOptimizationTrainer:
    def __init__(self):
        pass      

    def model_training(self, inputs, CONFIG):
        """Train the model."""
        start_time = time.time()
        num_individuals = 500
        num_elites = int(CONFIG["Eli"] * num_individuals)
        num_mutants = int(CONFIG["Mut"] * num_individuals)
        model = BRKGA(
            inputs, 
            num_generations=CONFIG["Gen"], 
            num_individuals=num_individuals, 
            num_elites=num_elites, 
            num_mutants=num_mutants, 
            eliteCProb=CONFIG["EliCPro"], 
            multiProcess=CONFIG["multi"])
        model.fit(patient=CONFIG["pat"], verbose=CONFIG["ver"])
        final_time = print('time:',time.time() - start_time)
        return model, final_time

def main(worklist_id, unique_code):
    # ----------------------
    input_csv = os.path.join(settings.MEDIA_ROOT, 'input_csv', f'{unique_code}.csv')
    # ----------------------
    """Main function."""
    box_processor = BoxProcessor(Config.TOTAL_BOXES, Config.TOTAL_BIN, Config.CONTAINER_DIM2d, Config.SAFE_SPACE)
    decode_boxes = DecodeBoxes()
    visualizer = VisualizeBoxes(colormap='tab10', elev=75, azim=35)
    CSV_generator = CSVgenerator()
    save_CSV = SaveCSV()
    box_optimizationTrainer = BoxOptimizationTrainer()
    
    # result_folder = save_CSV.create_results_directory()
    # ------------------------
    result_folder = save_CSV.create_results_directory_django(worklist_id)
    # ------------------------
    inputs = box_processor.load_and_process_data(input_csv)
    baseline_boxes = box_processor.process_boxes_from_csv(input_csv)
    
    container_data = inputs['V']
    print(len(inputs['v']))
    print(len(inputs['V']))
    print(inputs)
    # Train model
    model, _ = box_optimizationTrainer.model_training(inputs, Config.CONFIG)
    print('used bins:',model.used_bins)
    inputs['solution'] = model.solution
    decoder = PlacementProcedure(inputs, model.solution)
    print('fitness:',decoder.evaluate())
    # define the output file
    OUTPUT_GENERATION = 'box_positions_2d.csv'
    output_file = os.path.join(result_folder, OUTPUT_GENERATION)
    decode_boxes.decode_box(decoder, output_file)
    # Read the decode file to generate figures and csv files
    csv_base_name = os.path.splitext(os.path.basename(output_file))[0]
    box_data = pd.read_csv(output_file)
    box_data = CSV_generator.match_box_data(box_data, baseline_boxes)
    visualizer.visualize_boxes_2d(box_data, container_data, result_folder, csv_base_name, normalize_colors=Config.CONFIG["colNorm"], random_colors=Config.CONFIG["colRand"])
    save_CSV.save_data_to_csv(box_data, result_folder, csv_base_name, baseline_boxes, Config.SAFE_SPACE)
    visualizer.visualize_boxes_3d(box_data, Config.CONTAINER_DIM3d, result_folder, csv_base_name, normalize_colors=Config.CONFIG["colNorm"], random_colors=Config.CONFIG["colRand"])
    # Show the final figure
    # plt.show()

# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         pass