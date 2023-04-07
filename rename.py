import os
import datetime
from PIL import Image
import argparse

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="the directory containing the photos")
parser.add_argument("--suffix", help="an optional suffix to append to the new filename")
args = parser.parse_args()

# Initialize image counter
image_count = 0

# Loop through all files in the directory
for index, filename in enumerate(os.listdir(args.directory)):
    if filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
        
        # Open the image and get the original date and time from the EXIF metadata
        with Image.open(os.path.join(args.directory, filename)) as image:
            exif_data = image._getexif()
            if exif_data is not None and 36867 in exif_data:
                date_time_str = exif_data[36867]
                date_time_obj = datetime.datetime.strptime(date_time_str, '%Y:%m:%d %H:%M:%S')
                date = date_time_obj.strftime('%Y-%m-%d_%H%M%S')
            else:
                # If no EXIF data is available, use the file's creation time instead
                timestamp = os.path.getctime(os.path.join(args.directory, filename))
                date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H%M%S')
        
        # Construct the new file name
        suffix = args.suffix if args.suffix else ""
        new_filename = f"{date}{suffix}{os.path.splitext(filename)[1]}"
        
        # Handle conflicts by appending a suffix
        counter = 1
        while os.path.exists(os.path.join(args.directory, new_filename)):
            new_filename = f"{date}_{counter}{suffix}{os.path.splitext(filename)[1]}"
            counter += 1
        
        # Rename the file
        os.rename(os.path.join(args.directory, filename), os.path.join(args.directory, new_filename))
        
        # Increment image count
        image_count += 1
        
        # Print progress and image count
        print(f"Processed {image_count} of {len([f for f in os.listdir(args.directory) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])} images. Renamed {filename} to {new_filename}")
