import numpy as np


class Config2d:
    # Set a fixed random seed for reproducibility
    random_seed = 42
    np.random.seed(random_seed)
    # Global Constants
    V = (220,220)
    INPUT_PATH = 'box_volume_20230705_11Items_scaled.csv' #原始工單
    SAFE_SPACE = int(5)
    TOTAL_BOXES = 11
    TOTAL_BIN = 4
    BOX_QUANTITY = 1
    container_width = 220
    container_height = 220
    container_depth = 240 
    CONTAINER_DIM2d = (container_width, container_height)
    CONTAINER_DIM3d = (container_width, container_height, container_depth)
    # Configurations
    CONFIG = {
        "Gen": 100, # num_generations
        "Ind": 10, # num_individuals
        "Eli": 0.20, # num_elites
        "Mut": 0.25, # num_mutants
        "EliCPro": 0.75, # eliteCProb
        "pat": 16, # patient
        "multi": False, # multiProcess
        "ver": True, # verbose
        "colNorm": False, # normalize_colors
        "colRand": True, # random_color
        "resTime": False # result_timeStamp
    }

class Config3d:
    # Set a fixed random seed for reproducibility
    random_seed = 42
    np.random.seed(random_seed)
    # Global Constants
    V = (220,220,240)
    INPUT_PATH = 'box_volume_20230705_11Items_scaled.csv'   #原始工單
    SAFE_SPACE = int(5)
    TOTAL_BOXES = 50
    TOTAL_BIN = 5
    container_width = 220
    container_height = 220
    container_depth = 240
    CONTAINER_DIM3d = (container_width, container_height, container_depth)
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
        "colLayer": False, # layer_colors
        "resTime": False # result_timeStamp
    }

class ConfigOnline:
    # Define container dimensions
    container_width = int(220)
    container_height = int(220)
    container_depth = int(240)
    container_data_3d = (container_width, container_height, container_depth)
    result_folder = './result'
    csv_base_name = 'buffer'
    FINAL2D_CSV, GA_CSV = './result/box_positions_2d_final.csv', './result/box_positions_layer.csv'