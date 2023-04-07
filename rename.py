import os
import datetime

# Set the directory where your photos are located
directory = "/path/to/photos"

# Loop through all files in the directory
for filename in os.listdir(directory):
    if filename.endswith(".jpg"):
        
        # Get the creation time of the file
        timestamp = os.path.getctime(os.path.join(directory, filename))
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        # Construct the new file name
        new_filename = f"{date}_{filename}"
        
        # Handle conflicts by appending a suffix
        counter = 1
        while os.path.exists(os.path.join(directory, new_filename)):
            new_filename = f"{date}_{counter}_{filename}"
            counter += 1
        
        # Rename the file
        os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
