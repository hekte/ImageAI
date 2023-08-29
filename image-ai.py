import argparse
import cv2
import hashlib
import shelve
import os
import piexif
import shutil
import uuid
from tqdm import tqdm

parser = argparse.ArgumentParser()
#parser.add_argument("directory", default='~', help="the directory containing the photos")
parser.add_argument("-r", "--rebuild", action='store_true', help="empty and rebuild the index database")
parser.add_argument("-d", "--dedupe", action='store_true', help="dedupe the index database")
parser.add_argument("-t", "--trash", help="an optional suffix for the trash directoy")
parser.add_argument("-s", "--source", help="an optional suffix for the source directoy")
args = parser.parse_args()

# Initialize the local database
index_db = os.path.join(os.path.expanduser("~"), 'index')
hashmap_db = os.path.join(os.path.expanduser("~"), 'hashmap')
library = "/Volumes/home/Photos/PhotoLibrary"
index = shelve.open(index_db)
hashmap = shelve.open(hashmap_db)
debug = True

# Function to extract the file extention of a file
def get_file_extension(filename):
    _, extension = os.path.splitext(filename)
    return extension

# Function to compute the SHA-256 hash of a file
def compute_hash(file_path):
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except hashlib.exception as e:
        print(e)
        return None

# Function to compute the perceptual hash of an image
def compute_phash(file_path):
    try:
        phash = {}
        #imread = cv2.cvtColor(cv2.imread(file_path), cv2.IMREAD_IGNORE_ORIENTATION, cv2.COLOR_BGR2GRAY)
        imread = cv2.imread(file_path, cv2.IMREAD_IGNORE_ORIENTATION)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        phash[0] = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        imread = cv2.rotate(imread, cv2.ROTATE_90_CLOCKWISE)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        phash[1] = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        imread = cv2.rotate(imread, cv2.ROTATE_180)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        phash[2] = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        imread = cv2.rotate(imread, cv2.ROTATE_90_COUNTERCLOCKWISE)
        imhash = cv2.img_hash.pHash(imread) # 8-byte hash
        phash[3] = int.from_bytes(imhash.tobytes(), byteorder='big', signed=False)
        return phash
    except cv2.error as e:
        print(e)
        return None

# function to check if an image was taken with a camera
def is_camera(filename):
    try:
        exif_dict = piexif.load(filename)
        if piexif.ImageIFD.Make in exif_dict['0th'] and piexif.ImageIFD.Model in exif_dict['0th']:
            return True
        else:
            print(exif_dict)
            return False
    except Exception as e:
        print(f"Error loading EXIF data: {e}")
        return False

def rebuild_index(directory):
    index.clear()
    # Iterate through directories and files recursively and exclude hidden
    file_count = sum(len([f for f in files if not f[0] == '.']) for _, _, files in os.walk(directory))
    with tqdm(total=file_count, ncols=100) as pbar:
        for root, _, files in os.walk(directory):
            files = [f for f in files if not f[0] == '.']
            for filename in files:
                pbar.update(1)
                file_uuid = str(uuid.uuid4())
                file_path = os.path.join(root, filename)
                file_ext = str.upper(get_file_extension(filename))
                file_hash = compute_hash(file_path)
                if file_ext == ".JPG":
                    file_phash = compute_phash(file_path)
                else:
                    file_phash = None
                try:
                    # Store file information in the local database
                    index[file_uuid] = {
                        'filename': filename,
                        'extension': file_ext,
                        'path': file_path,
                        'hash': file_hash,
                        'phash': file_phash
                    }
                except KeyError as e:
                    print(e)

def dedupe_index():
    dd = {}
    # Check for duplicate files by using the hash as the key
    for key, value in index.items():
        dd_key = value['hash']
        dd_value = key
        if dd_key in dd:
            print("--")
            print("A: " + str(index.get(dd[dd_key])['path']))
            print("B: " + str(index.get(key)['path']))
            print("--")
            print("Enter A/B to delete or any other key to ignore")
            user_input = input("> ")
            if (user_input == "A" or user_input == "a"):
                del index[dd[dd_key]]
            elif (user_input == "B" or user_input == "b"):
                del index[key]
            else:
                print("Ignoring")
        else:
            dd[dd_key] = dd_value

def hashmap_index():
    # Create a map of file hashes
    print("├ Total Index Count: " + str(len(index.keys())))
    if debug == True:
        print("└─ // DEBUG")
        print(next(iter(index.items())))
        print("┌─")
    hashmap.clear()
    dupe_count = 0
    for key, value in index.items():
        hashmap_key = value['hash']
        hashmap_value = key
        if hashmap_key in hashmap:
            dupe_count += 1
        else:
            hashmap[hashmap_key] = hashmap_value
    if debug == True:
        print("└─ // DEBUG")
        print(next(iter(hashmap.items())))
        print("┌─")
    print("├ Duplicate Index File Hashes: " + str(dupe_count))
    # Create a map of perceptual hashes
    hashmap.clear()
    dupe_count = 0
    for key, value in index.items():
        if not value['phash'] == None:
            for phash_key, phash_value in value['phash'].items():
                hashmap_key = str(phash_value)
                hashmap_value = str(key)
                if hashmap_key in hashmap:
                    dupe_count += 1
                else:
                    hashmap[hashmap_key] = hashmap_value

    if debug == True:
        print("└─ // DEBUG")
        print(next(iter(hashmap.items())))
        print("┌─")
    print("├ Duplicate Perceptual Hashes: " + str(dupe_count))


def dedupe_source(directory):
    file_count = sum(len([f for f in files if not f[0] == '.']) for _, _, files in os.walk(directory))
    for root, _, files in os.walk(directory):
        files = [f for f in files if not f[0] == '.']
        for filename in files:
            file_path = os.path.join(root, filename)
            file_hash = compute_hash(file_path)
            print(file_hash)

def detect_trash():
    item_count = len(index.items())
    with tqdm(total=item_count, ncols=100) as pbar:
        for key, value in index.items():
            pbar.update(1)
            #print(value['path'])
            if not is_camera(value['path']):
                src = value['path']
                dst = args.trash
                shutil.move(src, dst)

def main():
    os.system('clear')
    print("")
    print("SSSSS                                                            .sSSSSs.")
    print("SSSSS .sSSSsSS SSsSSSSS .sSSSSs.    .sSSSSs.    .sSSSSs.         SSSSSSSSSs. SSSSS")
    print("S SSS S SSS  SSS  SSSSS S SSSSSSSs. S SSSSSSSs. S SSSSSSSs.      S SSS SSSSS S SSS")
    print("S  SS S  SS   S   SSSSS S  SS SSSSS S  SS SSSS' S  SS SSSS'      S  SS SSSSS S  SS")
    print("S..SS S..SS       SSSSS S..SSsSSSSS S..SS       S..SS            S..SSsSSSSS S..SS")
    print("S:::S S:::S       SSSSS S:::S SSSSS S:::S`sSSs. S:::SSSS         S:::S SSSSS S:::S")
    print("S;;;S S;;;S       SSSSS S;;;S SSSSS S;;;S SSSSS S;;;S            S;;;S SSSSS S;;;S")
    print("S%%%S S%%%S       SSSSS S%%%S SSSSS S%%%S SSSSS S%%%S SSSSS      S%%%S SSSSS S%%%S")
    print("SSSSS SSSSS       SSSSS SSSSS SSSSS SSSSSsSSSSS SSSSSsSS;:'      SSSSS SSSSS SSSSS v0.01")
    print("┌─────────────────────────────────────────────────────────────────────────────────")
    # Directory containing the files
    directory = library
    # Directory to move files from
    source = args.source
    if args.rebuild:
        rebuild_index(directory)
        print("")
    else:
        print("├ Rebuild Index? No")
    if args.dedupe:
        dedupe_index()
    else:
        print("├ Detect Duplicates? No")
    if args.source:
        hashmap_index()
        dedupe_source(source)
    else:
        print("├ Import Source? No")
    # if args.trash:
    #     detect_trash()
    # else:
    #     print("Detect Trash? No")

if __name__ == '__main__':
    main()
    index.close()
    hashmap.close()
