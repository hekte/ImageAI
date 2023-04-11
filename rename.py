import os
import datetime
from PIL import Image
import argparse
import filecmp
import hashlib
import piexif
import shutil
from skimage.metrics import structural_similarity as ssim
import cv2

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="the directory containing the photos")
parser.add_argument("--suffix", help="an optional suffix to append to the new filename")
parser.add_argument("--move", help="an optional directory to move the new files into")
args = parser.parse_args()


# Function to check if file has image extension
def is_image(filename):
    return filename.lower().endswith((".jpg", ".jpeg"))

# Function to check and fix exif tags
def check_exif(exif_dict):
    for tag in [41728, 41729]:
        try:
            if type(exif_dict['Exif'][tag]) is int:
                exif_dict['Exif'][tag] = exif_dict['Exif'][tag].to_bytes(1, 'big')
        except KeyError as e:
            print(f"\033[33m\u25E6 INFO: {e}. Missing exif_dict tag\033[0m")
    return exif_dict

def hash_file(filename):
    # Open the file in binary mode
    with open(filename, 'rb') as f:
        # Create a SHA-256 hash object
        hasher = hashlib.sha256()

        # Loop over the file, feeding it into the hash object in chunks
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            hasher.update(chunk)

        # Return the hexadecimal representation of the hash
        return hasher.hexdigest()

def is_empty_string(s):
    return s.isspace()

def main():
    # Initialize image counter
    image_count = 0
    skip_count = 0

    # Loop through all files in the directory
    image_total = len([f for f in os.listdir(args.directory) if is_image(f)])

    for index, filename in enumerate(os.listdir(args.directory)):    
        if is_image(filename):
            print(f"\033[32mProcessing: {filename}\033[0m")
            # Open the image and get the original date and time from the EXIF metadata
            with Image.open(os.path.join(args.directory, filename)) as image:
                try:
                    exif_dict = piexif.load(image.info["exif"])
                    exif_dict = check_exif(exif_dict)
                except KeyError as e:
                    print(f"\033[31m\u25E6 ERROR: {e}\033[0m")
                if exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                    date_time_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
                    # Handle exception when original data time is missing
                    if is_empty_string(date_time_str):
                        print(f"\033[31m\u25E6 WARN: original date time missing from EXIF metadata\033[0m")
                        date_time_str = exif_dict["0th"][piexif.ImageIFD.DateTime].decode("utf-8")
                    print(f"\033[32m\u25E6 Image Date/Time: {date_time_str}\033[0m")
                    #input("Press Enter to continue...")
                    date_time_obj = datetime.datetime.strptime(date_time_str, '%Y:%m:%d %H:%M:%S')
                    date = date_time_obj.strftime('%Y-%m-%d_%H%M%S')
                else:
                    # If no EXIF data is available, use the file's creation time instead
                    timestamp = os.path.getctime(os.path.join(args.directory, filename))
                    date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H%M%S')
                # Get the original file name and store it in the EXIF metadata
                try:
                    original_filename = exif_dict["0th"][piexif.ImageIFD.ImageDescription].decode("utf-8")
                except KeyError:
                    # If the ImageDescription tag is not present, use the original filename instead
                    original_filename = os.path.basename(filename)
                try:
                    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = original_filename.encode("utf-8")
                except KeyError as e:
                    print(f"\033[31m\u25E6 ERROR: {e}\033[0m")
                try:
                    # Convert the exif_dict to a byte array
                    exif_bytes = piexif.dump(exif_dict)
                # If an error occurs, remove the exif_dict and convert it to a byte array
                except ValueError as e:
                    print(f"\033[31m\u25E6 ERROR: {e}\033[0m")
                    # Remove the exif_dict from the exif_dict
                    exif_dict = piexif.remove(exif_dict)
                    # Convert the exif_dict to a byte array
                    exif_bytes = piexif.dump(exif_dict)
           
            # Construct the new file name and path
            suffix = args.suffix if args.suffix else ""
            new_filename = f"{date}{suffix}{os.path.splitext(filename)[1]}"
            new_file_path = os.path.join(args.directory, new_filename)
            
            # Handle conflicts by appending a suffix
            counter = 1
            while os.path.exists(new_file_path):
                new_filename = f"{date}_{counter}{suffix}{os.path.splitext(filename)[1]}"
                new_file_path = os.path.join(args.directory, new_filename)
                counter += 1
            
            # Rename the file
            os.rename(os.path.join(args.directory, filename), new_file_path)

            # Write the original file name to the EXIF metadata of the new file
            with Image.open(new_file_path) as image:
                try:
                    image.save(new_file_path, exif=exif_bytes)
                except IOError:
                    raise IOError(f"\033[31m\u25E6 ERROR: failed to write EXIF metadata to {new_file_path}\033[0m")
            # Move the file to a new directory if specified
            if args.move:
                output_path = os.path.join(args.move, new_filename)
                os.makedirs(args.move, exist_ok=True)
                if os.path.exists(output_path):
                    print(f"\033[31m\u25E6 WARN: Filename already exists: {new_filename}\033[0m")
                    if os.stat(new_file_path) == os.stat(output_path):
                        print(f"\033[31m\u25E6 Stat match?: True\033[0m")
                        raise FileExistsError(f"Identical file exists in output directory: {new_filename}")
                    else:
                        print(f"\033[31m\u25E6 Stat match?: False\033[0m")
                    if hash_file(new_file_path) == hash_file(output_path):
                        print(f"\033[33m\u25E6 Hash match?: True\033[0m")
                        os.remove(new_file_path)
                        print(f"\033[31m\u25E6 Removed identical source file {new_filename}\033[0m")
                        #raise FileExistsError(f"Identical file exists in output directory: {new_filename}")
                    else:
                        print(f"\033[31m\u25E6 Hash match?: False\033[0m")
                        try:
                            src = cv2.cvtColor(cv2.imread(new_file_path), cv2.COLOR_BGR2GRAY)
                            dst = cv2.cvtColor(cv2.imread(output_path), cv2.COLOR_BGR2GRAY)
                            ss = ssim(src, dst)
                            if ss == 1.0:
                                print(f"\033[33m\u25E6 Structural similarity?: True\033[0m")
                                os.remove(new_file_path)
                                print(f"\033[31m\u25E6 Removed identical source file {new_filename}\033[0m")
                            else:
                                print(f"\033[34m\u25E6 Structural similarity: {ss}\033[0m")
                        except ValueError:
                            print(f"\033[34m\u25E6 Structural Similarity: Not calculated\033[0m")
                    # Increment skipped image count
                    skip_count += 1
                else:
                    os.rename(new_file_path, output_path)
                    print(f"\033[32m\u25E6 Moved {new_filename} to {args.move}\033[0m")

            # Increment image count
            image_count += 1
            
            # Print progress and image count
            print(f"\033[32m\u25E6 Processed {image_count} of {image_total} images. Renamed {filename} to {new_filename}\033[0m")
        
    # Print skipped image count
    print(f"\033[36mSkipped {skip_count} of {image_total} images. Review manually\033[0m")

if __name__ == "__main__":
    main()