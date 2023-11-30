import os
import time
import csv
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from collections import defaultdict, Counter
from .model_speed_3d import PlacementProcedure, BRKGA
from .config import Config3d as Config
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

    def distribute_randomly(self, num_items):
        """Distribute the total quantity into num_items parts randomly."""
        div_points = sorted(np.random.choice(range(1, self.total_boxes), num_items - 1, replace=False))
        result = np.split(np.array(range(self.total_boxes)), div_points)
        return [int(len(x)) for x in result]

    def load_and_process_data(self, csv_file_path, randomize_quantity=False):
        """Loads and processes the data from a CSV file."""
        inputs = {
        'v': [],  # boxes with different shape
        'V': [self.container_dims] * self.total_bins   # containers with fixed shape
        }
        # Random Quantity
        quantityR = self.distribute_randomly(11) if randomize_quantity else None
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for idx, row in enumerate(reader):
                width, height, depth = int(row['width']), int(row['height']), int(row['depth'])
                box_data = (width + self.safe_space, 
                            height + self.safe_space, 
                            depth)
                quantity = quantityR[idx] if randomize_quantity else int(row['quantity'])
                inputs['v'].extend([box_data] * quantity)
        return inputs
    
    def process_boxes_from_csv(self, csv_path):
        """Processes box dimensions from a CSV file."""
        baseline_boxes = pd.read_csv(csv_path)
        baseline_boxes.rename(columns={'name': 'box_name'}, inplace = True)
        baseline_boxes.loc[:, ['width', 'height', 'depth']]  = baseline_boxes[['width', 'height', 'depth']].astype(int)
        baseline_boxes.loc[:, ['width', 'height']] = (baseline_boxes[['width', 'height']]) + Config.SAFE_SPACE
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
            writer.writerow(['bin_name', 'box_name', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth'])
            writer.writerows(box_data)

class Visualize3DBoxes:
    def __init__(self, colormap='tab10', elev=75, azim=35):
        self.colormap = plt.get_cmap(colormap)
        self.elev = elev
        self.azim = azim

    def draw_box(self, ax, position, size, color='b', alpha=0.1):
        """Draws a 3D box on the given axes."""
        px, py, pz = position
        sx, sy, sz = size
        return ax.bar3d(px, py, pz, sx, sy, sz, color, shade=False, alpha=alpha, edgecolor='black', linewidth=1.5)

    def draw_cog(self, ax, position, size, color='r'):
        """Draws a 3D center of gravity point."""
        cx, cy, cz = position[0] + size[0]/2, position[1] + size[1]/2, position[2] + size[2]
        ax.scatter([cx], [cy], [cz], c=color, marker='o', s=100)

    def layer_to_color(self, layer):
        """Maps a layer number to a unique color."""
        return self.colormap(layer % 10)

    def visualize_boxes(self, box_data, container_data, result_folder, csv_base_name, normalize_colors=False, layer_color=False): 
        """Visualizes boxes in a 3D plot and saves images and GIFs."""
        ax, fig = None, None
        images, drawn_boxes_objects = [], []
        current_bin_name = None

        for index, row in box_data.iterrows():
            bin_name = row.get('bin_name')
            if bin_name != current_bin_name:
                if fig:
                    self.save_gif(fig, result_folder, csv_base_name, current_bin_name, images)
                fig, ax = self.create_new_figure(container_data, bin_name)
                images, drawn_boxes_objects = [], []
                current_bin_name = bin_name

            position = row['position_x'], row['position_y'], row['position_z']
            size = row['width'], row['height'], row['depth']
            if normalize_colors:
                # Get the color from normalization color row
                self.draw_box(ax, position, size, color=row['color'], alpha=1)
            elif layer_color:
                box_color = self.layer_to_color(row['layer']) if 'layer' in box_data.columns else 'red'
                box_obj = self.draw_box(ax, position, size, color=box_color, alpha=1)
                drawn_boxes_objects.append(box_obj)
            else:
                # Change color of the last drawn box to red and others blue for UI
                if drawn_boxes_objects:
                    drawn_boxes_objects[-1].set_facecolors('blue')
                box_obj = self.draw_box(ax, position, size, color='red', alpha=1)
                drawn_boxes_objects.append(box_obj)
            self.draw_cog(ax, position, size, color='g')
            img_path = self.save_image(fig, result_folder, index, bin_name)
            images.append(imageio.imread(img_path))

        if fig:
            self.save_gif(fig, result_folder, csv_base_name, current_bin_name, images)

    def create_new_figure(self, container_data, bin_name):
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

    def save_gif(self, fig, result_folder, csv_base_name, bin_name, images):
        """Saves the figure as a GIF."""
        gif_name = f'all_boxes_{csv_base_name}_bin_{bin_name}.gif'
        imageio.mimsave(os.path.join(result_folder, gif_name), images, duration=500)

    def save_image(self, fig, result_folder, index, bin_name):
        """Saves an image of the current state of the figure."""
        img_path = os.path.join(result_folder, f'box_{index+1}_bin_{bin_name}.png')
        plt.savefig(img_path)
        return img_path

class CSVgenerator:
    def __init__(self, tolerance=0.01, colormap='bwr'):
        self.tolerance = tolerance
        self.colormap = plt.get_cmap(colormap)

    def match_box_name(self, width, height, depth, baseline_boxes):
        """Matches the box name and orientation based on width, height, and depth."""
        for _, baseline_row in baseline_boxes.iterrows():
            if not self.is_within_tolerance(baseline_row['depth'], depth):
                continue
            if self.is_within_tolerance(width, baseline_row['width']) and self.is_within_tolerance(height, baseline_row['height']):
                return baseline_row['box_name'], 0
            elif self.is_within_tolerance(width, baseline_row['height']) and self.is_within_tolerance(height, baseline_row['width']):
                return baseline_row['box_name'], 1
        return None, None

    def is_within_tolerance(self, a, b):
        """Checks if two values are within a specified tolerance."""
        return abs(a - b) <= self.tolerance

    def normalize_colors(self, box_volumes):
        """Generates a list of normalized colors."""
        max_volume, min_volume = box_volumes.max(), box_volumes.min()
        return [self.colormap(0.1 + 0.9 * (vol - min_volume) / (max_volume - min_volume)) if max_volume != min_volume else self.colormap(1) for vol in box_volumes]

    def prepare_box_data(self, box_data, baseline_boxes):
        """Prepares and enriches box data."""
        box_data = box_data.assign(
            width=lambda df: df['width'].astype(int),
            height=lambda df: df['height'].astype(int),
            depth=lambda df: df['depth'].astype(int),
            X_cog=lambda df: df['position_x'] + df['width'] / 2,
            Y_cog=lambda df: df['position_y'] + df['height'] / 2,
            Z_cog=lambda df: df['position_z'] + df['depth']
        )
        box_volumes = box_data.eval('width * height * depth')
        box_data['color'] = self.normalize_colors(box_volumes)
        box_data = self.match_and_sort_box_data(box_data, baseline_boxes)
        return box_data

    def match_and_sort_box_data(self, box_data, baseline_boxes):
        """Matches box names and sorts the data."""
        for index, row in box_data.iterrows():
            matched_box_name, orientation = self.match_box_name(row['width'], row['height'], row['depth'], baseline_boxes)
            box_data.at[index, 'matched_box_name'] = matched_box_name
            box_data.at[index, 'orientation'] = orientation if matched_box_name is not None else None

        sort_columns = ['bin_name', 'layer', 'position_z', 'position_y', 'position_x'] if 'bin_name' in box_data.columns else ['layer', 'position_z', 'position_y', 'position_x']
        return box_data.sort_values(by=sort_columns).reset_index(drop=True)
  
    def is_overlapping(self, a, b):
        return not (a['position_x'] + a['width'] <= b['position_x'] or
                    b['position_x'] + b['width'] <= a['position_x'] or
                    a['position_y'] + a['height'] <= b['position_y'] or
                    b['position_y'] + b['height'] <= a['position_y'])

    def assign_layers_to_boxes(self, box_data, result_folder, csv_base_name):
        box_data['layer'] = 0  # Initialize all layers to 0

        for bin_name, group in box_data.groupby('bin_name'):
            # Sort boxes based on z position to handle them in order
            group = group.sort_values('position_z')

            layers = []  # Each layer will have a list of boxes
            for _, box in group.iterrows():
                assigned = False
                current_layer = 0

                for layer_boxes in layers:
                    # If box overlaps with any box in the current layer, move to next layer
                    if any(self.is_overlapping(box, other_box) for other_box in layer_boxes):
                        current_layer += 1
                        continue
                    else:
                        layer_boxes.append(box)
                        box_data.at[box.name, 'layer'] = current_layer
                        assigned = True
                        break

                # If the box was not assigned to any existing layers, create a new layer
                if not assigned:
                    layers.append([box])
                    box_data.at[box.name, 'layer'] = current_layer
        return box_data

    def generate_packed_unpacked_counts(self, box_data, bin_num, baseline_boxes):
        """Generates the counts of packed and unpacked_boxes."""
        baseline_df = pd.DataFrame(baseline_boxes, columns=['box_name'])
        bin_boxes = box_data[box_data['bin_name'] == bin_num]
        packed_counts = bin_boxes['matched_box_name'].value_counts()
        packed_df = pd.DataFrame({'box_name': packed_counts.index, 'packed_boxes': packed_counts.values})
        other_boxes = box_data[box_data['bin_name'] != bin_num]
        unpacked_counts = other_boxes['matched_box_name'].value_counts()
        unpacked_df = pd.DataFrame({'box_name': unpacked_counts.index, 'unpacked_boxes': unpacked_counts.values})
        counts_df = pd.merge(packed_df, unpacked_df, on='box_name', how='outer').fillna(0)
        result = pd.merge(baseline_df, counts_df, on='box_name', how='left').fillna(0)
        result[['packed_boxes', 'unpacked_boxes']] = result[['packed_boxes', 'unpacked_boxes']].astype(int)
        result['quantity'] = result['packed_boxes'] + result['unpacked_boxes']
        return result[['box_name', 'quantity', 'packed_boxes', 'unpacked_boxes']]

    def count_quantity(self, df, baseline_boxes):
        """Counts the amount of boxes."""
        # Get unique bin names and box names
        bins = df['bin_name'].unique()
        count_dict = defaultdict(dict)
        for bin in bins:
            for _, box in baseline_boxes.iterrows():
                box_name = box['box_name']
                count = len(df[(df['bin_name'] == bin) & (df['matched_box_name'] == box_name)])
                count_dict[box_name][bin] = count
        new_df = pd.DataFrame(count_dict).T.reset_index()
        # Rename the first column to 'name'
        new_df.rename(columns={'index': 'box_name'}, inplace=True)
        # Rename the bin columns to have 'bin_' prefix
        bin_columns = {col: 'bin_' + str(col) for col in new_df.columns if col != 'box_name'}
        new_df.rename(columns=bin_columns, inplace=True)
        return new_df
    
    def count_input(self, box_data, baseline_boxes):
        """Counts the amount of boxes to generate input file."""
        baseline_boxes_copy = baseline_boxes.copy() # Create copy to avoid modifying original data
        box_count = Counter(box_data['matched_box_name'])
        for box_name in baseline_boxes_copy['box_name']:
            if box_name not in box_count:
                box_count[box_name] = 0
        quantity_df = pd.DataFrame({'box_name': list(box_count.keys()), 'quantity': list(box_count.values())})
        # merge with baseline_boxes to get the dimensions
        result = pd.merge(quantity_df, baseline_boxes_copy, on='box_name')
        # Use the reindex method to keep the original order
        result = result.set_index('box_name').reindex(baseline_boxes['box_name']).reset_index()
        return result

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
        # add cog
        save_path = os.path.join(result_folder, f'{csv_base_name}')
        # Adjust 'width' and 'height' by reducing the SAFE_SPACE
        box_data['width'] = box_data['width'] - SAFE_SPACE
        box_data['height'] = box_data['height'] - SAFE_SPACE
        # Adjust 'position_x' and 'position_y' by adding half of the SAFE_SPACE
        box_data['position_x'] = box_data['position_x'] + SAFE_SPACE / 2
        box_data['position_y'] = box_data['position_y'] + SAFE_SPACE / 2

        # Add other columns for the position of taking box from conveyor
        box_data['conveyor_x'] = box_data['width']/2
        box_data['conveyor_y'] = box_data['height']/2
        box_data['conveyor_z'] = box_data['depth']
        rotation_mask = box_data['orientation'] == 1
        box_data.loc[rotation_mask, ['conveyor_x', 'conveyor_y']] = box_data.loc[rotation_mask, ['conveyor_y', 'conveyor_x']].values
        
        # Create a new DataFrame with only the columns for position of putting box in the palette
        output_data = box_data[['bin_name', 'matched_box_name', 'conveyor_x', 'conveyor_y', 'conveyor_z', 'X_cog', 'Y_cog', 'Z_cog', 'orientation', 'layer', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth']]
        final_save_path = save_path.rsplit('.', 1)[0] + '_layer.csv'
        print(f"Saving file to {final_save_path}")
        output_data.to_csv(final_save_path, index=False)

class BoxOptimizationTrainer:
    def __init__(self):
        pass

    def calculate_total_boxes(self, inputs):
        """Calculates the total quantity of boxes on the given inputs."""
        return len(inputs['v'])
    
    def model_training(self, inputs, CONFIG):
        """Train the model."""
        start_time = time.time()
        total_boxes = self.calculate_total_boxes(inputs)
        # num_individuals = CONFIG["Ind"] * total_boxes
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
    box_processor = BoxProcessor(Config.TOTAL_BOXES, Config.TOTAL_BIN, Config.CONTAINER_DIM3d, Config.SAFE_SPACE)
    decode_boxes = DecodeBoxes()
    visualize_3Dboxes = Visualize3DBoxes(colormap='tab10', elev=75, azim=35)
    CSV_generator = CSVgenerator()
    save_CSV = SaveCSV()
    box_optimizationTrainer = BoxOptimizationTrainer()

    # result_folder = save_CSV.create_results_directory()
    # ------------------------
    result_folder = save_CSV.create_results_directory_django(worklist_id)
    # ------------------------
    inputs = box_processor.load_and_process_data(input_csv, randomize_quantity=Config.CONFIG["RandQuant"])
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
    OUTPUT_GENERATION = 'box_positions.csv'
    output_file = os.path.join(result_folder, OUTPUT_GENERATION)
    decode_boxes.decode_box(decoder, output_file)
    # Read the decode file to generate figures and csv files
    csv_base_name = os.path.splitext(os.path.basename(output_file))[0]
    box_data = pd.read_csv(output_file)
    box_layer = CSV_generator.assign_layers_to_boxes(box_data, result_folder, csv_base_name)
    box_data = CSV_generator.prepare_box_data(box_data, baseline_boxes)
    box_data = CSV_generator.match_and_sort_box_data(box_data, baseline_boxes)
    # Visualization and CSV Saving
    visualize_3Dboxes.visualize_boxes(box_data, container_data, result_folder, csv_base_name, normalize_colors=Config.CONFIG["colNorm"],layer_color=Config.CONFIG["colLayer"])
    save_CSV.save_data_to_csv(box_data, result_folder, csv_base_name, baseline_boxes, Config.SAFE_SPACE)
    # Show the final figure
    # plt.show()

# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         pass