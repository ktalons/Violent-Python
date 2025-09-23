# Kyle Versluis, 09/07/2025, Assignment 2
# Title: Simple File Processing
# Purpose: Extracts and displays a sorted list of names found in a log file

# Import Python Standard Libraries
import os

uniqueWorms = set()
# reads the file (redhat.txt) then splits each line into columns
try:
    with open("redhat.txt", 'r') as logFile:
        for eachLine in logFile:
            columns = eachLine.split()
            # iterate through columns to find "worm"
            for eachCol in columns:
                if "worm" in eachCol.lower():
                    uniqueWorms.add(eachCol)
                else:
                    continue
#print error if the file (redhat.txt) cannot be opened
except:
    print("Error opening file", logFile)
    quit()

# Sort the set
sortedWorms = sorted(uniqueWorms)
# iterate through set and print
for eachWorm in sortedWorms:
    print(eachWorm)