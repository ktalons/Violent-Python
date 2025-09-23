# Kyle Versluis, 09/07/2025, Assignment 3
# Title: File Hashing
# Purpose: Creates a dictionary of file hashes from a list of files. \
# Iterates through the dictionary and prints out the key, value pairs.

# Imports
import os
import hashlib
# Constants. Sets directory to the current directory
directory = "."
# initialize list of files and dictionary for file hashes
fileList   = []
fileHashes = {}

# Walk the directory. top to bottom.
for root, dirs, files in os.walk(directory):

    for fileName in files:
        path = os.path.join(root, fileName)
        fullPath = os.path.abspath(path)
        fileList.append(fullPath)
        # add files to fileList
        fileList.append(fullPath)

# Iterate through the list of files to calculate hashes and adds \
# filepath-hash pair to the dictionary
for filePath in fileList:
    with open(filePath, 'rb') as file:
        fileContent = file.read()
        fileHash = hashlib.md5(fileContent).hexdigest()
        fileHashes[fileHash] = filePath

# Iterate through the dictionary and print key, value pairs
for key, value in fileHashes.items():
    print(key, value)