#!/usr/bin/env python3
import sys
import time

def main():
    print("Showcase demo script starting...")
    for i in range(1, 6):
        print(f"Working... step {i}/5")
        sys.stdout.flush()
        time.sleep(0.8)
    print("All done!")

if __name__ == "__main__":
    main()
