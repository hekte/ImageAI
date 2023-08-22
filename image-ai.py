import argparse
import cv2
import hashlib
import shelve
import os
import uuid
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument("directory", help="the directory containing the photos")
parser.add_argument("-r", "--rebuild", action='store_true', help="empty and rebuild the index database")
parser.add_argument("-d", "--dedupe", action='store_true', help="dedupe the index database")
args = parser.parse_args()

# Initialize the local database
index = os.path.join(os.path.expanduser("~"), 'index')
db = shelve.open(index)

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

# Function to compute the perceptual hash of a file
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

def rebuild_index(directory):
    db.clear()
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
                    db[file_uuid] = {
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
    for key, value in db.items():
        dd_key = value['hash']
        dd_value = key
        if dd_key in dd:
            print("--")
            print("A: " + str(db.get(dd[dd_key])['path']))
            print("B: " + str(db.get(key)['path']))
            print("--")
            print("Enter A/B to delete or any other key to ignore")
            user_input = input("> ")
            if (user_input == "A" or user_input == "a"):
                del db[dd[dd_key]]
            elif (user_input == "B" or user_input == "b"):
                del db[key]
            else:
                print("Ignoring")
        else:
            dd[dd_key] = dd_value


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
    print("SSSSS SSSSS       SSSSS SSSSS SSSSS SSSSSsSSSSS SSSSSsSS;:'      SSSSS SSSSS SSSSS")
    print("v0.01")
    print("")
    # Directory containing the files
    directory = args.directory
    if args.rebuild:
        rebuild_index(directory)
    else:
        print("no rebuild")
    if args.dedupe:
        dedupe_index()
    else:
        print("no dedupe")

if __name__ == '__main__':
    main()
    db.close()
