import os
import time
import csv
import numpy as np
import pandas as pd
from .model_speed import PlacementProcedure, BRKGA
import matplotlib.pyplot as plt
import matplotlib.pyplot as plt
import imageio.v2 as imageio

from django.conf import settings
import os

# box_positions.csv
# figure_folder



V = (220,220,240)
# CSV_PATH = 'box_volume_11items.csv'
SAFE_SPACE = 5

def decode_box(decoder, output_file):
    box_data = []
    for i in range(decoder.num_opend_bins):
        for j, box in enumerate(decoder.Bins[i].load_items):
            position = box[0]  # Get the box position
            dimensions = box[1] - box[0]  # Calculate box dimensions
            box_data.append([
                f'Bin {i+1}',  # Add container information
                f'Box {j+1}',
                position[0],
                position[1],
                position[2],
                dimensions[0],
                dimensions[1],
                dimensions[2],
            ])
    # Save box data to a CSV file
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['bin_name', 'box_name', 'position_x', 'position_y', 'position_z', 'width', 'height', 'depth'])
        writer.writerows(box_data)


def draw_box(ax, position, size, color='b', alpha=0.9):
    px, py, pz = position
    sx, sy, sz = size
    ax.bar3d(px, py, pz, sx, sy, sz, color, shade=False, alpha=alpha, edgecolor='black', linewidth=1.5)

def draw_cog(ax, position, size, color='r'):
    cx, cy, cz = position[0] + size[0]/2, position[1] + size[1]/2, position[2] + size[2]
    ax.scatter([cx], [cy], [cz], c=color, marker='o', s=100)

def match_box_name(width, height, depth, baseline_boxes):
    '''This function will return back matched_box_name and orientation of the boxes based on the 
    order of width and height'''
    for i, baseline_row in baseline_boxes.iterrows():
        # If depth is not matching, no need to proceed further for this row
        if baseline_row['depth'] != depth:
            continue
        # Check for exact match
        if width == baseline_row['width'] and height == baseline_row['height'] and depth == baseline_row['depth']:
            return baseline_row['box_name'], 0
        # Check for swapped width and height
        elif width == baseline_row['height'] and height == baseline_row['width'] and depth == baseline_row['depth']:
            return baseline_row['box_name'], 1
    return None, None

def generate_packed_unpacked_counts(box_data, bin_num, baseline_boxes):
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
    result['frequency'] = result['packed_boxes'] + result['unpacked_boxes']
    return result[['box_name', 'frequency', 'packed_boxes', 'unpacked_boxes']]

# if __name__ == "__main__":
def activate_cal(worklist_id):
    global SAFE_SPACE
    CSV_PATH = os.path.join(settings.MEDIA_ROOT, f'box_data_{worklist_id}.csv')
    inputs = {
        'v': [],  # boxes with different shape
        'V': []   # containers with fixed shape
    }
    csv_file_path = CSV_PATH
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            width = (int(row['width'])*2)+ SAFE_SPACE
            height = (int(row['height'])*2)+ SAFE_SPACE
            depth = int(row['depth'])*2
            box_data = (width, height, depth)
            quantity = int(row['quantity'])
            # Add the box_data to 'v' list 'quantity' times
            inputs['v'].extend([box_data] * quantity)
    # Add container data to 'V' list (assuming the container data is the same for all rows)
    container_width = 220
    container_height = 220
    container_depth = 240
    container_data = (container_width, container_height, container_depth)
    inputs['V'] = [container_data] * 7
    print(len(inputs['v']))
    print(len(inputs['V']))
    print(inputs)
    start_time = time.time()
    # model = BRKGA(inputs, num_generations = 50, num_individuals=50, num_elites = 20, num_mutants = 20, eliteCProb = 0.8, multiProcess = True)
    model = BRKGA(inputs, num_generations = 100, num_individuals=400, num_elites = 40, num_mutants = 40, eliteCProb = 0.8, multiProcess = True)
    model.fit(patient = 16,verbose = True)
    print('used bins:',model.used_bins)
    print('time:',time.time() - start_time)
    inputs['solution'] = model.solution
    decoder = PlacementProcedure(inputs, model.solution)
    print('fitness:',decoder.evaluate())
    # output_file = 'box_positions.csv'
    output_file = os.path.join(settings.MEDIA_ROOT, 'box_positions.csv')
    decode_box(decoder, output_file)

    csv_path = CSV_PATH
    baseline_from_csv = pd.read_csv(csv_path)
    baseline_from_csv = baseline_from_csv.rename(columns={'name': 'box_name'})
    baseline_boxes = baseline_from_csv[['box_name', 'width', 'height', 'depth']]
    baseline_boxes.loc[:, 'width']  = baseline_boxes['width'].astype(float)
    baseline_boxes.loc[:, 'height'] = baseline_boxes['height'].astype(float)
    baseline_boxes.loc[:, 'depth'] = baseline_boxes['depth'].astype(float)
    # Multiply each dimension by 2 and add SAFE_SPACE (For depth, just multiply by 2)
    baseline_boxes.loc[:, 'width']  = (baseline_boxes['width'] * 2) + SAFE_SPACE
    baseline_boxes.loc[:, 'height'] = (baseline_boxes['height'] * 2) + SAFE_SPACE
    baseline_boxes.loc[:, 'depth']  = baseline_boxes['depth'] * 2

    # Get the script directory
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    script_dir = settings.MEDIA_ROOT
    file_path = os.path.join(script_dir, 'box_positions.csv')

    box_data = pd.read_csv(file_path)
    csv_base_name = os.path.splitext(os.path.basename(file_path))[0]
    box_data['width'] = np.ceil(box_data['width'].astype(float))
    box_data['height'] = np.ceil(box_data['height'].astype(float))
    box_data['depth'] = np.ceil(box_data['depth'].astype(float))

    # Create a folder for saving the figures
    figure_folder = os.path.join(script_dir, f'Figures_{worklist_id}')
    # figure_folder = os.path.join(script_dir, f'Figures_{csv_base_name}')
    os.makedirs(figure_folder, exist_ok=True)

    # Calculate box volumes and normalize colors
    box_volumes = box_data['width'] * box_data['height'] * box_data['depth']
    max_volume = box_volumes.max()
    min_volume = box_volumes.min()
    normalized_colors = []
    colormap = plt.get_cmap('bwr')
    for volume in box_volumes:
        if max_volume != min_volume:
            normalized_volume = 0.1 + 0.9 * (volume - min_volume) / (max_volume - min_volume)
        else:
            # Handle the case where all weights are the same
            normalized_volume = 1 
        color = colormap(normalized_volume)
        normalized_colors.append(color)

    # List to save all the images
    images = []
    box_data['color'] = normalized_colors
    box_data['X_cog'] = np.ceil(box_data['position_x'] + box_data['width'] / 2)
    box_data['Y_cog'] = np.ceil(box_data['position_y'] + box_data['height'] / 2)
    box_data['Z_cog'] = np.ceil(box_data['position_z'] + box_data['depth'])

    # Sort the boxes by bin_name (if available) and then by z-position (bottom to top),
    # then by y-position (back to front), and then by x-position (left to right)
    if 'bin_name' in box_data.columns:
        box_data = box_data.sort_values(by=['bin_name', 'position_z', 'position_y', 'position_x']).reset_index(drop=True)
    else:
        box_data = box_data.sort_values(by=['position_z', 'position_y', 'position_x']).reset_index(drop=True)

    current_bin_name = None
    current_figure_num = 1

    for index, row in box_data.iterrows():
        # Add the matched box name from baseline boxes to a new column in the DataFrame
        matched_box_name, orientation = match_box_name(row['width'], row['height'], row['depth'], baseline_boxes)
        box_data.loc[index, 'matched_box_name'] = matched_box_name

        # Add '0' to a new column if all dimensions match, leave it empty otherwise
        if matched_box_name is not None:
            box_data.loc[index, 'orientation'] = orientation
        if 'bin_name' in box_data.columns:
            bin_name = row['bin_name']
            if bin_name != current_bin_name:
                if current_figure_num > 1:
                    gif_name = f'all_boxes_{csv_base_name}_bin_{current_bin_name}.gif'
                    imageio.mimsave(os.path.join(figure_folder, gif_name), images, duration=500)
                # Create a new figure for the new bin
                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')
                ax.set_box_aspect([1,1,1])  # Make the scale of x, y, and z axes the same
                ax.set_xlim([0, container_data [0]])  # Set x limit
                ax.set_ylim([0, container_data [1]])  # Set y limit
                ax.set_zlim([0, container_data [2]])  # Set z limit
                ax.view_init(elev=75., azim=35)  # Change the viewpoint
                draw_box(ax, [0, 0, 0], container_data , color='grey', alpha=0)
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
        color = row['color']

        draw_box(ax, position, size, color=color, alpha=1)
        ax.set_title(f'Box {index+1} in Bin: {bin_name}')
        draw_cog(ax, position, size, color='g')

        img_path = os.path.join(figure_folder, f'box_{index+1}_bin_{bin_name}.png')
        plt.savefig(img_path)

        # Add to the list of images
        images.append(imageio.imread(img_path))

    # Save the figure of the last bin
    if current_figure_num > 1:
        gif_name = f'all_boxes_{csv_base_name}_bin_{current_bin_name}.gif'
        imageio.mimsave(os.path.join(figure_folder, gif_name), images, duration=500)

    # Save the DataFrame to a CSV file
    save_path = os.path.join(figure_folder, f'{csv_base_name}')
    cog_save_path = save_path.rsplit('.', 1)[0] + '_cog.csv'
    print(f"Saving file to {save_path}")
    with open(cog_save_path, 'w', encoding='utf-8') as file:
        box_data.to_csv(file, index=False)

    # Create a new DataFrame for the position of taking box from convey
    baseline_widths = baseline_boxes.set_index('box_name')['width'].to_dict()
    output_data_convey = box_data.copy()  # Create a copy to avoid changing the original DataFrame
    output_data_convey['pos_x'] = output_data_convey['matched_box_name'].apply(lambda x: (baseline_widths[x] - SAFE_SPACE) / 2)
    output_data_convey['pos_y'] = 0
    output_data_convey['pos_z'] = output_data_convey['depth']
    output_data = output_data_convey[['bin_name', 'matched_box_name', 'pos_x', 'pos_y', 'pos_z']]
    convey_save_path = save_path.rsplit('.', 1)[0] + '_convey.csv'
    print(f"Saving file to {convey_save_path}")
    with open(convey_save_path, 'w', newline='', encoding='utf-8') as file:
        output_data.to_csv(file, index=False)

    # Create a new DataFrame with only the columns for position of putting box in the palette
    output_data = box_data[['bin_name', 'matched_box_name', 'depth', 'X_cog', 'Y_cog', 'Z_cog', 'orientation']]
    final_save_path = save_path.rsplit('.', 1)[0] + '_final.csv'
    print(f"Saving file to {final_save_path}")
    with open(final_save_path, 'w', newline='', encoding='utf-8') as file:
        output_data.to_csv(file, index=False)

    # Count pack and unpacked boxes
    box_packUnpack = generate_packed_unpacked_counts(box_data, 'Bin 1', baseline_boxes)
    packUnpack_save_path = save_path.rsplit('.', 1)[0] + '_packUnpack.csv'
    print(f"Saving file to {final_save_path}")
    box_packUnpack.to_csv(packUnpack_save_path, index=False)

# Show the final figure
# plt.show()