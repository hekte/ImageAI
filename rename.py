import os
import datetime
from PIL import Image
import argparse
# import filecmp
import hashlib
import piexif
# import shutil
import subprocess
from skimage.metrics import structural_similarity as ssim
import cv2

# Set up command line argument parser
parser = argparse.ArgumentParser()
parser.add_argument("directory", help="the directory containing the photos")
parser.add_argument("--suffix", help="an optional suffix to append to the new filename")
parser.add_argument("--dedupe", action='store_true', help="an optional directory to dedupe photos")
parser.add_argument("--compare", action='store_true', help="an optional suffix to compare files")
parser.add_argument("--target", help="an optional suffix for the target directoy")
parser.add_argument("--trash", help="an optional suffix for the trash directoy")
args = parser.parse_args()


# Function to check if file has image extension
def is_image(filename):
    return filename.lower().endswith((".jpg", ".jpeg"))

# Function to check if file has image extension
def is_video(filename):
    return filename.lower().endswith(".mp4")

# function to check if an image was taken with a camera
def is_camera(filename):
    try:
        exif_dict = piexif.load(filename)
        if piexif.ImageIFD.Make in exif_dict['0th'] and piexif.ImageIFD.Model in exif_dict['0th']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error loading EXIF data: {e}")
        return False

# Function to check and fix exif tags
def check_exif(exif_dict):
    for tag in [41728, 41729]:
        try:
            if type(exif_dict['Exif'][tag]) is int:
                exif_dict['Exif'][tag] = exif_dict['Exif'][tag].to_bytes(1, 'big')
        except KeyError as e:
            print(f"\033[33m\u25E6 INFO: {e}. Missing exif_dict tag\033[0m")
    return exif_dict

def get_mp4_creation_time(filename):
    output = subprocess.check_output(['exiftool', '-CreateDate', '-b', filename])
    return output.decode('utf-8').strip()

# function to return the sha256 hash for a given file
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

# function to return the perceptual hash for an image https://www.hackerfactor.com/blog/?/archives/432-Looks-Like-It.html
def perceptual_hash(filename):
    try:
        imread = cv2.cvtColor(cv2.imread(filename), cv2.IMREAD_IGNORE_ORIENTATION, cv2.COLOR_BGR2GRAY)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        perceptual_hash = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        return perceptual_hash
    except cv2.error as e:
        print(e)

def rotate_hash(filename):
    try:
        #imread = cv2.cvtColor(cv2.imread(filename), cv2.IMREAD_IGNORE_ORIENTATION, cv2.COLOR_BGR2GRAY)
        src = cv2.imread(filename, cv2.IMREAD_IGNORE_ORIENTATION)
        imread = cv2.rotate(src, cv2.ROTATE_90_CLOCKWISE)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        rotated_hash = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        print(rotated_hash)
        imread = cv2.rotate(src, cv2.ROTATE_180)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        rotated_hash = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        print(rotated_hash)
        imread = cv2.rotate(src, cv2.ROTATE_90_COUNTERCLOCKWISE)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        rotated_hash = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        print(rotated_hash)
        return
    except cv2.error as e:
        print(e)

def is_empty_string(s):
    return s.isspace()

def main():
    # Initialize image counter
    image_count = 0
    video_count = 0
    skip_count = 0
    dupe_count = 0
    file_dict = {}
    img_dict = {}

    # Loop through all files in the directory
    image_total = len([f for f in os.listdir(args.directory) if is_image(f)])

    for index, filename in enumerate(sorted(os.listdir(args.directory))):    
        if is_image(filename):
            # Increment image count
            image_count += 1
            print(f"\033[32mProcessing: {image_count} of {image_total} ({filename})\033[0m")
            if args.compare:
                if args.target:
                    output_path = os.path.join(args.target, filename)
                    if os.path.exists(output_path):
                        print(f"\033[35m\u25E6 WARN: Filename already exists: {filename}\033[0m")
                        if hash_file(filename) == hash_file(output_path):
                            print(f"\033[33m\u25E6 Hash match?: True\033[0m")
                            os.remove(filename)
                            dupe_count += 1
                            print(f"\033[35m\u25E6 WARN: Removed identical source file {filename}\033[0m")
                        else:
                            print(f"\033[33m\u25E6 Hash match?: False\033[0m")
                            try:
                                #src = cv2.cvtColor(cv2.imread(filename), cv2.IMREAD_IGNORE_ORIENTATION, cv2.COLOR_BGR2GRAY)
                                #dst = cv2.cvtColor(cv2.imread(output_path), cv2.IMREAD_IGNORE_ORIENTATION, cv2.COLOR_BGR2GRAY)
                                src = cv2.imread(filename, cv2.IMREAD_IGNORE_ORIENTATION)
                                dst = cv2.imread(output_path, cv2.IMREAD_IGNORE_ORIENTATION)
                                print(src.shape)
                                print(dst.shape)
                                ss = ssim(src, dst)
                                if ss == 1.0:
                                    print(f"\033[33m\u25E6 Structural similarity?: True\033[0m")
                                    dupe_count += 1
                                    os.remove(filename)
                                    print(f"\033[33m\u25E6 Removed identical source file {filename}\033[0m")
                                else:
                                    print(f"\033[33m\u25E6 Structural similarity: {ss}\033[0m")
                            except ValueError as e:
                                print(e)
                                print(f"\033[33m\u25E6 Structural Similarity: Not calculated\033[0m")
            elif args.dedupe:
                # Create a dictionary to store hashes and corresponding file paths
                #cv2_file = cv2.imread(filename, cv2.IMREAD_IGNORE_ORIENTATION)
                #cv2_hash = cv2.img_hash.BlockMeanHash_create()
                #cv2_hash = cv2_hash.compute(cv2_file)
                #print(is_exif(filename))
                if is_camera(filename):
                    #print(f"\033[33m\u25E6 Exif: ✓ Camera: ✓ \033[0m")
                    file_hash = hash_file(filename)
                    img_hash = perceptual_hash(filename)
                    print(img_hash)
                    rotate_hash(filename)
                    if file_hash in file_dict:
                        dupe_count += 1
                        print(f"\033[33m\u25E6 File hash found: {filename} and {file_dict[file_hash]}")
                    else:
                        file_dict[file_hash] = filename
                    if img_hash in img_dict:
                        dupe_count += 1
                        print(f"\033[33m\u25E6 Image hash found: {filename} and {img_dict[img_hash]}")
                    else:
                        img_dict[img_hash] = filename
                else:
                    print("Send this image to trash for review")
                # if file_hash in hash_dict:
                #     # Duplicate found, print the paths of both files
                #     dupe_count += 1
                #     print(f"\033[33m\u25E6 Duplicate found: {filename} and {hash_dict[file_hash]}")
                # else:
                #     hash_dict[file_hash] = filename
                # if cv2_hash in cv2_dict:
                #     # Duplicate found, print the paths of both files
                #     dupe_count += 1
                #     print(f"\033[33m\u25E6 Rotated duplicate found: {filename} and {cv2_hash[file_hash]}")
                # else:
                #     cv2_hash[file_hash] = filename
                #print(f"\033[33m\u25E6 Filename: {filename}\033[0m")
            else:
                # Open the image and get the original date and time from the EXIF metadata
                with Image.open(os.path.join(args.directory, filename)) as image:
                    exif_dict = None
                    try:
                        exif_dict = piexif.load(image.info["exif"])
                        exif_dict = check_exif(exif_dict)
                    except KeyError as e:
                        print(f"\033[31m\u25E6 ERROR: KeyError {e} \033[0m")
                    if exif_dict is None:
                        # If the EXIF metadata is missing, skip the image
                        skip_count += 1
                        print(f"\033[35m\u25E6 WARN: Skipped file {new_filename}\033[0m")
                    else:
                        if exif_dict and piexif.ExifIFD.DateTimeOriginal in exif_dict["Exif"]:
                            date_time_str = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode("utf-8")
                            # Handle exception when original data time is missing
                            if is_empty_string(date_time_str):
                                print(f"\033[35m\u25E6 WARN: original date time missing from EXIF metadata\033[0m")
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
                            print(f"\033[31m\u25E6 ERROR: KeyError {e}\033[0m")
                        try:
                            # Convert the exif_dict to a byte array
                            exif_bytes = piexif.dump(exif_dict)
                        # If an error occurs, remove the exif_dict and convert it to a byte array
                        except ValueError as e:
                            print(f"\033[31m\u25E6 ERROR: ValueError {e}\033[0m")
                            # Remove the exif_dict from the exif_dict
                            exif_dict = piexif.remove(exif_dict)
                            # Convert the exif_dict to a byte array
                            exif_bytes = piexif.dump(exif_dict)
            
                        # Construct the new file name and path
                        suffix = args.suffix if args.suffix else ""
                        new_filename = f"{date}{suffix}{os.path.splitext(filename)[1]}"
                        new_file_path = os.path.join(args.directory, new_filename)

                        # Handle conflicts by skipping the file on this run
                        if os.path.exists(new_file_path):
                            skip_count += 1
                            print(f"\033[35m\u25E6 WARN: Filename already exists: {new_file_path}\033[0m")
                        else:
                            # Rename the file and move it to the new path
                            os.rename(os.path.join(args.directory, filename), new_file_path)
                            # Write the original file name to the EXIF metadata of the new file
                            with Image.open(new_file_path) as image:
                                try:
                                    image.save(new_file_path, exif=exif_bytes)
                                    print(f"\033[36m\u25E6 OK: Renamed {filename} to {new_filename}\033[0m")
                                except IOError:
                                    raise IOError(f"\033[31m\u25E6 ERROR: failed to write EXIF metadata to {new_file_path}\033[0m")
                                
                            # Move the file to a new directory if specified
                            if args.target:
                                output_path = os.path.join(args.target, new_filename)
                                os.makedirs(args.target, exist_ok=True)
                                if os.path.exists(output_path):
                                    print(f"\033[35m\u25E6 WARN: Filename already exists: {new_filename}\033[0m")
                                    if os.stat(new_file_path) == os.stat(output_path):
                                        print(f"\033[33m\u25E6 Stat match?: True\033[0m")
                                        raise FileExistsError(f"Identical file exists in taarget directory: {new_filename}")
                                    else:
                                        print(f"\033[33m\u25E6 Stat match?: False\033[0m")
                                    if hash_file(new_file_path) == hash_file(output_path):
                                        print(f"\033[33m\u25E6 Hash match?: True\033[0m")
                                        os.remove(new_file_path)
                                        dupe_count += 1
                                        print(f"\033[35m\u25E6 WARN: Removed identical source file {new_filename}\033[0m")
                                    else:
                                        print(f"\033[33m\u25E6 Hash match?: False\033[0m")
                                        try:
                                            src = cv2.cvtColor(cv2.imread(new_file_path), cv2.COLOR_BGR2GRAY)
                                            dst = cv2.cvtColor(cv2.imread(output_path), cv2.COLOR_BGR2GRAY)
                                            ss = ssim(src, dst)
                                            if ss == 1.0:
                                                print(f"\033[33m\u25E6 Structural similarity?: True\033[0m")
                                                dupe_count += 1
                                                os.remove(new_file_path)
                                                print(f"\033[33m\u25E6 Removed identical source file {new_filename}\033[0m")
                                            else:
                                                print(f"\033[33m\u25E6 Structural similarity: {ss}\033[0m")
                                        except ValueError:
                                            print(f"\033[33m\u25E6 Structural Similarity: Not calculated\033[0m")
                                    # Increment skipped image count
                                    skip_count += 1
                                    print(f"\033[35m\u25E6 WARN: Skipped file {new_filename}\033[0m")
                                else:
                                    os.rename(new_file_path, output_path)
                                    print(f"\033[36m\u25E6 OK: Moved {new_filename} to {args.target}\033[0m")

        elif is_video(filename):
            video_count += 1
            creation_time = get_mp4_creation_time(filename)
            print(f"MP4 Filename: {filename} Creation Time: {creation_time}")

    # Print skipped image count
    print(f"\033[32mTotal Images: {image_total}\033[0m")
    print(f"\033[33mSkipped: {skip_count}\033[0m")
    print(f"\033[33mDuplicates: {dupe_count}\033[0m")
    print(f"\033[32mTotal Videos: {video_count}\033[0m")

if __name__ == "__main__":
    main()