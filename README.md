# ImageAI
An image (and movie) processor created with the help of AI tools such as [ChatGPT](https://chat.openai.com/) and [CodeGeeX](https://codegeex.cn/) developed in [Visual Studio Code](https://code.visualstudio.com/)

## Background

In the process of renaming, sorting, deduplicating and moving tens of thousands of photos from a cloud platform I couldn't find an off the shelf tool which could assist the way I wanted.

To begin I asked ChatGPT the following;

**Prompt:** What is the best file name format for thousands of photos?

**ChatGPT:** There are many different file naming formats that can work well for organizing thousands of photos. Here are a few common options:

Date-based file names: You can use a format that includes the date the photo was taken, such as "YYYY-MM-DD_filename.jpg". This can be helpful for sorting photos chronologically.
Sequential file names: You can use a format that includes a sequence number for each photo, such as "00001_filename.jpg", "00002_filename.jpg", and so on. This can be helpful for keeping track of the order in which photos were taken or processed.
Descriptive file names: You can use a format that includes a brief description of the photo, such as "beach_sunset_filename.jpg" or "family_vacation_001.jpg". This can be helpful for quickly identifying the contents of each photo.
Regardless of the format you choose, it's important to be consistent and use the same naming convention for all of your photos. This will make it easier to search for and find specific photos later on.

**Prompt:** I will choose a date-based file name format for my photos. How should I manage a conflict?

**ChatGPT:** If you are using a date-based file name format for your photos and encounter a conflict, such as two or more photos taken on the same day, you can add a suffix to differentiate between them.

One approach is to add a time stamp to the file name, such as "YYYY-MM-DD_HHMMSS_filename.jpg". This will create a unique file name for each photo, based on the precise time it was taken.

For example, if you have two photos taken on January 1st, 2023, you could name them "2023-01-01_121500_filename.jpg" and "2023-01-01_140200_filename.jpg" to reflect the time they were taken.

Another approach is to add a letter or number suffix, such as "YYYY-MM-DD_filename-a.jpg" and "YYYY-MM-DD_filename-b.jpg". This can work well if you only have a few conflicting photos.

**Prompt:** Can you crate a python script which can be used to perform this?

**ChatGPT:** Yes, I can help you create a Python script to perform the file naming using the date-based format you've chosen. Here's an example script that renames all `.jpg` files in a directory to use the format `YYYY-MM-DD_filename.jpg`:

```python
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
        
        # Rename the file
        os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
```

In this script, the `os` module is used to access and manipulate files and directories, and the `datetime` module is used to format the date from the file's creation timestamp.

You can modify the script to adjust the file name format or directory path to suit your needs. Additionally, you may want to add error handling or confirmation prompts to ensure that the script renames files correctly and safely.


## Fuctions

- Iterate through a source directory and rename to the desired format
- Handle duplicate filename by appending a suffix
- Move files to a destination directory for further processing
- Compare image metadata to detect and remove duplicates

## Usage

