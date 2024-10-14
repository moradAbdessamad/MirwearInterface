import os

def rename_and_remove_images(folder_path):
    # Get a list of all files in the folder
    files = os.listdir(folder_path)
    
    # Define the allowed extensions
    allowed_extensions = ('.jpg', '.jpeg', '.png')
    
    # Filter out only image files with allowed extensions
    image_files = [file for file in files if file.endswith(allowed_extensions)]
    
    # Rename each image file
    for index, filename in enumerate(image_files, start=1):
        # Get the file extension
        file_extension = os.path.splitext(filename)[1]
        
        # Create a new filename
        new_filename = f'image{index}{file_extension}'
        new_file_path = os.path.join(folder_path, new_filename)
        
        # Increment the index if the filename already exists
        while os.path.exists(new_file_path):
            index += 1
            new_filename = f'image{index}{file_extension}'
            new_file_path = os.path.join(folder_path, new_filename)
        
        # Get the full path of the old file
        old_file_path = os.path.join(folder_path, filename)
        
        # Rename the file
        os.rename(old_file_path, new_file_path)
        print(f'Renamed: {filename} -> {new_filename}')
    
    # Remove files with other extensions
    for file in files:
        if not file.endswith(allowed_extensions):
            file_to_remove = os.path.join(folder_path, file)
            os.remove(file_to_remove)
            print(f'Removed: {file}')

# Folder path
folder_path = "./static/imagesformcam"

# Call the function to rename and remove images
rename_and_remove_images(folder_path)
