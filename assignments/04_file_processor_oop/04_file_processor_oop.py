# Kyle Versluis, 09/15/2025, Assignment 5
# Title: File Processor with Object-oriented Programming (OOP)
# Purpose: Extracts and displays file metadata and header information

# Import Python Standard Libraries

import os  # File system library
import time  # Time Conversion Library
from binascii import hexlify  # hexlify module

# FileProcessor Class Definition and Methods
# Class Constructor Method: extracts file metadata and stores as instance attributes

class FileProcessor:

    def __init__(self, path):

        try:
            self.filePath = path

            if os.path.isfile(self.filePath) and os.access(self.filePath, os.R_OK):

                # pulls the file metadata
                stats = os.stat(self.filePath)

                # store each as an instance attribute
                self.fileSize = stats.st_size
                self.fileCreatedTime = time.ctime(stats.st_ctime)
                self.fileModifiedTime = time.ctime(stats.st_mtime)
                self.fileAccessTime = time.ctime(stats.st_atime)
                self.fileMode = '{:016b}'.format(stats.st_mode)
                self.fileUID = stats.st_uid
                self.fileHeader = ''
                self.status = "OK"
            else:
                self.status = "File not accessible"

        # catch any exceptions and store the results in the status attribute
        except Exception as err:

            self.status = err
    # extract the first 20 bytes of the file header
    def GetFileHeader(self):
        try:
            with open(self.filePath, 'rb') as fileObject:
                header = fileObject.read(20)
                self.fileHeader = hexlify(header)
                self.status = "OK"
        except Exception as err:
            self.status = err

    def PrintFileDetails(self):

        try:
            print("\n================== File Details ========================")
            print("Path:          ", self.filePath)
            print("Size:          ", self.fileSize)
            print("Last Modified: ", self.fileModifiedTime)
            print("Last Accessed: ", self.fileAccessTime)
            print("Created:       ", self.fileCreatedTime)
            print("Mode:          ", self.fileMode)
            print("UserID:        ", self.fileUID)
            print("Header:        ", self.fileHeader)
            print("=========================================================")
            self.status = "OK"

        except Exception as err:
            self.status = err

    def PrintException(self):
        print("\n Exception: ", self.filePath, self.status)


print("\nWeek 3 Assignment\n")
print("Let's process some files using the objects method!\n")

while True:
    # prompt user for a directory path
    dirPath = input("Enter a Directory to Scan or Q to Quit: ")

    if dirPath.upper() == 'Q':
        print("\n\nUser Terminated the Script \n\n")
        break

    # validate that the directory exists
    if not os.path.isdir(dirPath):
        # If not force user to re-enter a proper directory
        print("Invalid Directory ... please try again")
        continue
    else:
        # pull the list of items in the directory path
        fileList = os.listdir(dirPath)

        for possibleFile in fileList:

            # convert the simple filename to the full and absolute path
            fullPath = os.path.join(dirPath, possibleFile)
            absPath = os.path.abspath(fullPath)

            # Only process files that we have rights to read
            fileObj = FileProcessor(absPath)
            if fileObj.status == 'OK':

                # verify that the fileObj was created successfully
                if fileObj.status == 'OK':
                    # invoke the GetFileHeader method
                    fileObj.GetFileHeader()
                    if fileObj.status == "OK":
                        fileObj.PrintFileDetails()
                        if fileObj.status == "OK":
                            continue
                        else:
                            fileObj.PrintException()
                    else:
                        fileObj.PrintException()
                else:
                    fileObj.PrintException()
            else:
                if os.path.isfile(absPath):
                    print("\nAccess Denied ", absPath)
                else:
                    print("\nEntry not a File ", absPath)
