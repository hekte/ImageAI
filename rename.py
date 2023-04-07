import os
import datetime
from PIL import Image

# Set the directory where your photos are located
directory = "/path/to/photos"

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".jpg"):
        
        # Open the image and get the original date and time from the EXIF metadata
        with Image.open(os.path.join(directory, filename)) as image:
            exif_data = image._getexif()
            if exif_data is not None and 36867 in exif_data:
                date_time_str = exif_data[36867]
                date_time_obj = datetime.datetime.strptime(date_time_str, '%Y:%m:%d %H:%M:%S')
                date = date_time_obj.strftime('%Y-%m-%d_%H%M%S')
            else:
                # If no EXIF data is available, use the file's creation time instead
                timestamp = os.path.getctime(os.path.join(directory, filename))
                date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H%M%S')
        
        # Construct the new file name
        new_filename = f"{date}.jpg"
        
        # Handle conflicts by appending a suffix
        counter = 1
        while os.path.exists(os.path.join(directory, new_filename)):
            new_filename = f"{date}_{counter}.jpg"
            counter += 1
        
        # Rename the file
        os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
