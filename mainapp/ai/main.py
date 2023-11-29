from main_result_2d import main as main_2d
from main_result_3d import main as main_3d
# from main_packing_camera import main as main_camera_online

def run_all():
    # Run the main function from main_result_2d.py
    main_2d()

    # Run the main function from main_result_UI.py
    main_3d()

    # Run the main function from main_packing_camera.py
    # main_camera_online()

if __name__ == "__main__":
    try:
        run_all()
    except KeyboardInterrupt:
        print("Execution was interrupted by the user.")
