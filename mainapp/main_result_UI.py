import os
import time
import csv
import numpy as np
import pandas as pd
from .model_speed import PlacementProcedure, BRKGA
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import imageio.v2 as imageio
from collections import defaultdict, Counter

from django.conf import settings
# Set a fixed random seed for reproducibility
random_seed = 42
np.random.seed(random_seed)
# Global Constants
V = (220,220,240)
INPUT_PATH = 'box_volume_11items_20230829.csv'
OUTPUT_GENERATION = 'box_positions.csv'
SAFE_SPACE = int(5)
TOTAL_BOXES = 50
TOTAL_BIN = 15
container_width = 220
container_height = 220
container_depth = 240
# Configurations
CONFIG = {
    "Gen": 100, # num_generations
    "Ind": 10, # num_individuals
    "Eli": 0.20, # num_elites
    "Mut": 0.25, # num_mutants
    "EliCPro": 0.75, # eliteCProb
    "pat": 16, # patient
    "multi": True, # multiProcess
    "ver": True, # verbose
    "RandQuant": False, # randomize_quantity
    "colNorm": False, # normalize_colors
    "colLayer": False # layer_colors
}


def distribute_randomly(total, num_items):
    """Distribute the total quantity into num_items parts randomly."""
    div_points = sorted(np.random.choice(range(1, total), num_items - 1, replace=False))
    result = np.split(np.array(range(total)), div_points)
    return [int(len(x)) for x in result]


def load_and_process_data(csv_file_path, randomize_quantity=False):
    """Loads and processes the data from a CSV file."""
    inputs = {
    'v': [],  # boxes with different shape
    'V': []   # containers with fixed shape
    }
    # Random Quantity
    quantityR = distribute_randomly(TOTAL_BOXES, 11)
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for idx, row in enumerate(reader):
            width = (int(row['width'])*2)+ SAFE_SPACE
            height = (int(row['height'])*2)+ SAFE_SPACE
            depth = int(row['depth'])*2
            box_data = (width, height, depth)
            if randomize_quantity:
                # Use random quantity
                inputs['v'].extend([box_data] * quantityR[idx])
            else:
                # Use quantity from CSV
                quantity = int(row['quantity'])
                inputs['v'].extend([box_data] * quantity)
    container_data = (container_width, container_height, container_depth)
    inputs['V'] = [container_data] * TOTAL_BIN
    return inputs


def calculate_total_boxes(inputs):
    """Calculates the total quantity of boxes on the given inputs."""
    return len(inputs['v'])


def create_results_directory(base_name='result'):
    """Creates a directory for saving results, with date and time as a unique identifier"""
    date_str = time.strftime("%Y%m%d_%H%M%S")
    results_dir = f'{base_name}_{date_str}'
    os.makedirs(results_dir, exist_ok=True)
    return results_dir

#----------------------------------
def create_results_directory_django(worklist_id):
    results_dir = os.path.join(settings.MEDIA_ROOT, f'ai_figure/Figures_{worklist_id}')
    os.makedirs(results_dir, exist_ok=True)
    return results_dir
#----------------------------------

def process_boxes_from_csv(csv_path):
    """Processes box dimensions from a CSV file."""
    baseline_from_csv = pd.read_csv(csv_path)
    baseline_from_csv = baseline_from_csv.rename(columns={'name': 'box_name'})
    baseline_boxes = baseline_from_csv[['box_name', 'width', 'height', 'depth']]
    baseline_boxes.loc[:, ['width', 'height', 'depth']]  = baseline_boxes[['width', 'height', 'depth']].astype(int)
    baseline_boxes.loc[:, ['width', 'height']] = (baseline_boxes[['width', 'height']] * 2) + SAFE_SPACE
    baseline_boxes.loc[:, 'depth'] = baseline_boxes['depth'] * 2
    return baseline_boxes


def decode_box(decoder, output_file):
    """Decodes the boxes from a CSV file and save them to another CSV file."""
    box_data = []
    for i in range(decoder.num_opend_bins):
        for j, box in enumerate(decoder.Bins[i].load_items):
            position = box[0]  # Get the box position
            dimensions = box[1] - box[0]  # Calculate box dimensions
            box_data.append([
                f'{i+1}',  # Add container information
                f'{j+1}',  # Add box information
                int(np.round(position[0])), int(np.round(position[1])), int(np.round(position[2])),
                int(dimensions[0]), int(dimensions[1]), int(dimensions[2]),
            ])
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['bin_name', 'box_name', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth'])
        writer.writerows(box_data)


def draw_box(ax, position, size, color='b', alpha=0.1):
    px, py, pz = position
    sx, sy, sz = size
    box_obj = ax.bar3d(px, py, pz, sx, sy, sz, color, shade=False, alpha=alpha, edgecolor='black', linewidth=1.5)
    return box_obj  # Return the drawn object


def draw_cog(ax, position, size, color='r'):
    """Draws a 3D cog."""
    cx, cy, cz = position[0] + size[0]/2, position[1] + size[1]/2, position[2] + size[2]
    ax.scatter([cx], [cy], [cz], c=color, marker='o', s=100)


def match_box_name(width, height, depth, baseline_boxes, tolerance=0.01):
    """Matches the matched_box_name and orientation of boxes based on width and height order."""
    for i, baseline_row in baseline_boxes.iterrows():
        # If depth is not matching within tolerance, no need to proceed further for this row
        if abs(baseline_row['depth'] - depth) > tolerance:
            continue
        # Check for exact match within tolerance
        if abs(width - baseline_row['width']) <= tolerance and abs(height - baseline_row['height']) <= tolerance:
            return baseline_row['box_name'], 0
        # Check for swapped width and height within tolerance
        elif abs(width - baseline_row['height']) <= tolerance and abs(height - baseline_row['width']) <= tolerance:
            return baseline_row['box_name'], 1
    return None, None


def generate_packed_unpacked_counts(box_data, bin_num, baseline_boxes):
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


def count_quantity(df, baseline_boxes):
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


def count_input(box_data, baseline_boxes):
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


def match_box_data(box_data, baseline_boxes):
    """Generating a DataFrame with the matched boxes."""
    box_data.loc[:, ['width', 'height', 'depth']]  = box_data[['width', 'height', 'depth']].astype(int)
    # Calculate box volumes and normalize colors
    box_volumes = box_data['width'] * box_data['height'] * box_data['depth']
    normalized_colors = normalize_colors(box_volumes)
    box_data['color'] = normalized_colors
    box_data['X_cog'] = box_data['position_x'] + box_data['width'] / 2
    box_data['Y_cog'] = box_data['position_y'] + box_data['height'] / 2
    box_data['Z_cog'] = box_data['position_z'] + box_data['depth']
    # Sort the boxes by bin_name (if available) and then by z-position (bottom to top),
    # then by y-position (back to front), and then by x-position (left to right)
    if 'bin_name' in box_data.columns:
        box_data = box_data.sort_values(by=['bin_name', 'layer', 'position_z', 'position_y', 'position_x']).reset_index(drop=True)
    else:
        box_data = box_data.sort_values(by=['layer', 'position_z', 'position_y', 'position_x']).reset_index(drop=True)
    for index, row in box_data.iterrows():
        # Add the matched box name from baseline boxes to a new column in the DataFrame
        matched_box_name, orientation = match_box_name(int(row['width']), int(row['height']), int(row['depth']), baseline_boxes, tolerance = 1)
        box_data.loc[index, 'matched_box_name'] = matched_box_name
        # Add '0' to a new column if all dimensions match, leave it empty otherwise
        if matched_box_name is not None:
            box_data.loc[index, 'orientation'] = orientation
    return box_data


def assign_layers_to_boxes(box_data, is_overlapping, result_folder, csv_base_name):
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
                if any(is_overlapping(box, other_box) for other_box in layer_boxes):
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

    # Save to new CSV
    save_path = os.path.join(result_folder, f'{csv_base_name}')
    layer_save_path = save_path.rsplit('.', 1)[0] + '_layer.csv'
    print(f"Saving file to {layer_save_path}")
    box_data.to_csv(layer_save_path, index=False)

    return box_data


def normalize_colors(box_volumes):
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


def is_overlapping(a, b):
    return not (a['position_x'] + a['width'] <= b['position_x'] or
                b['position_x'] + b['width'] <= a['position_x'] or
                a['position_y'] + a['height'] <= b['position_y'] or
                b['position_y'] + b['height'] <= a['position_y'])


def layer_to_color(layer):
    """Maps a layer number to a unique color."""
    colormap = plt.get_cmap('tab10') # 'tab10' provides 10 distinct colors
    return colormap(layer % 10) # Use modulo to loop back to the first color after 10 layers


def visualize_boxes(box_data, container_data, result_folder, csv_base_name, normalize_colors=False, layer_color=False): 
    """Visualizes the boxes in a 3D plot."""
    drawn_boxes_objects = [] 
    images = []
    current_bin_name = None
    current_figure_num = 1
    for index, row in box_data.iterrows():
        if 'bin_name' in box_data.columns:
            bin_name = row['bin_name']
            if bin_name != current_bin_name:
                if current_figure_num > 1:
                    gif_name = f'all_boxes_{csv_base_name}_bin_{current_bin_name}.gif'
                    imageio.mimsave(os.path.join(result_folder, gif_name), images, duration=500)
                # Create a new figure for the new bin
                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')
                ax.set_box_aspect([1,1,1])  # Make the scale of x, y, and z axes the same
                ax.set_xlim([0, container_data[0][0]])  # Set x limit
                ax.set_ylim([0, container_data[0][1]])  # Set y limit
                ax.set_zlim([0, container_data[0][2]])  # Set z limit
                ax.view_init(elev=75., azim=35)         # Change the viewpoint
                draw_box(ax, [0, 0, 0], container_data[0] , color='grey', alpha=0)
                ax.set_xlabel('X')
                ax.set_ylabel('Y')
                ax.set_zlabel('Z')
                ax.set_title(f'Boxes in Bin: {bin_name}')
                # Reset the image list for the new bin
                images = []
                current_bin_name = bin_name
                current_figure_num += 1
        position = row['position_x'], row['position_y'], row['position_z']
        size = row['width'], row['height'], row['depth']
        if normalize_colors:
            # Get the color from normalization color row
            draw_box(ax, position, size, color=row['color'], alpha=1)
        elif layer_color:
            box_color = layer_to_color(row['layer']) if 'layer' in box_data.columns else 'red'
            box_obj = draw_box(ax, position, size, color=box_color, alpha=1)
            drawn_boxes_objects.append(box_obj)
        else:
            # Change color of the last drawn box to red and others blue for UI
            if drawn_boxes_objects:
                drawn_boxes_objects[-1].set_facecolors('blue')
            box_obj = draw_box(ax, position, size, color='red', alpha=1)
            drawn_boxes_objects.append(box_obj)
        ax.set_title(f'Box {index+1} in Bin: {bin_name}')
        draw_cog(ax, position, size, color='g')
        img_path = os.path.join(result_folder, f'box_{index+1}_bin_{bin_name}.png')
        plt.savefig(img_path)
        # Add to the list of images
        images.append(imageio.imread(img_path))
    # Save the figure of the last bin
    if current_figure_num > 1:
        gif_name = f'all_boxes_{csv_base_name}_bin_{current_bin_name}.gif'
        imageio.mimsave(os.path.join(result_folder, gif_name), images, duration=500)


def save_data_to_csv(box_data, result_folder, csv_base_name, baseline_boxes, SAFE_SPACE):
    """Saves the data to different CSV files for different aims."""
    # add cog
    save_path = os.path.join(result_folder, f'{csv_base_name}')
    cog_save_path = save_path.rsplit('.', 1)[0] + '_cog.csv'
    print(f"Saving file to {save_path}")
    box_data.to_csv(cog_save_path, index=False)
    # Create a new DataFrame for the position of taking box from conveyor
    baseline_widths = baseline_boxes.set_index('box_name')['width'].to_dict()
    baseline_height = baseline_boxes.set_index('box_name')['height'].to_dict()
    output_data_convey = box_data.copy()  # Create a copy to avoid changing the original DataFrame
    output_data_convey['pos_x'] = output_data_convey['matched_box_name'].apply(lambda x: (baseline_widths[x] - SAFE_SPACE) / 2)
    output_data_convey['pos_y'] = output_data_convey['matched_box_name'].apply(lambda x: (baseline_height[x] - SAFE_SPACE) / 2)
    output_data_convey['pos_z'] = output_data_convey['depth']
    output_data = output_data_convey[['bin_name', 'matched_box_name', 'pos_x', 'pos_y', 'pos_z']]
    convey_save_path = save_path.rsplit('.', 1)[0] + '_conveyor.csv'
    print(f"Saving file to {convey_save_path}")
    output_data.to_csv(convey_save_path, index=False)
    # Create a new DataFrame with only the columns for position of putting box in the palette
    output_data = box_data[['bin_name', 'matched_box_name', 'depth', 'X_cog', 'Y_cog', 'Z_cog', 'orientation', 'layer']]
    final_save_path = save_path.rsplit('.', 1)[0] + '_final.csv'
    print(f"Saving file to {final_save_path}")
    output_data.to_csv(final_save_path, index=False)
    # Create a new DataFrame to count pack and unpacked boxes
    box_packUnpack = generate_packed_unpacked_counts(box_data, 1, baseline_boxes)
    packUnpack_save_path = save_path.rsplit('.', 1)[0] + '_packUnpack.csv'
    print(f"Saving file to {packUnpack_save_path}")
    box_packUnpack.to_csv(packUnpack_save_path, index=False)
    # Create a new DataFrame to count the quantity of each box in each bin
    box_quantity = count_quantity(box_data, baseline_boxes)
    binBox_save_path = save_path.rsplit('.', 1)[0] + '_binBoxQuantity.csv'
    print(f"Saving file to {binBox_save_path}")
    box_quantity.to_csv(binBox_save_path, index=False)
    # Create a new DataFrame to count the quantity of each box in all bin
    box_input = count_input(box_data, baseline_boxes)
    input_save_path = save_path.rsplit('.', 1)[0] + '_input.csv'
    print(f"Saving file to {input_save_path}")
    box_input.to_csv(input_save_path, index=False)

    
def model_training(inputs, CONFIG):
    """Train the model."""
    start_time = time.time()
    total_boxes = calculate_total_boxes(inputs)
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


def ai_calculate(worklist_id, unique_code):
    #------------------
    input_path = os.path.join(settings.MEDIA_ROOT, 'input_csv', f'{unique_code}.csv')
    result_folder = create_results_directory_django(worklist_id)
    #------------------
    """Main function."""
    # result_folder = create_results_directory()
    inputs = load_and_process_data(input_path, randomize_quantity=CONFIG["RandQuant"])
    baseline_boxes = process_boxes_from_csv(input_path)
    container_data = inputs['V']
    print(len(inputs['v']))
    print(len(inputs['V']))
    print(inputs)
    # Train model
    model, _ = model_training(inputs, CONFIG)
    print('used bins:',model.used_bins)
    inputs['solution'] = model.solution
    decoder = PlacementProcedure(inputs, model.solution)
    print('fitness:',decoder.evaluate())
    # define the output file
    output_file = os.path.join(result_folder, OUTPUT_GENERATION)
    decode_box(decoder, output_file)
    # Read the decode file to generate figures and csv files
    csv_base_name = os.path.splitext(os.path.basename(output_file))[0]
    box_data = pd.read_csv(output_file)
    box_layer = assign_layers_to_boxes(box_data, is_overlapping, result_folder, csv_base_name)
    box_data = match_box_data(box_layer, baseline_boxes)
    visualize_boxes(box_data, container_data, result_folder, csv_base_name, normalize_colors=CONFIG["colNorm"],layer_color=CONFIG["colLayer"])
    save_data_to_csv(box_data, result_folder, csv_base_name, baseline_boxes, SAFE_SPACE)
    # Show the final figure
    # plt.show()


# if __name__ == "__main__":
#     try:
#         main()
#     except KeyboardInterrupt:
#         pass