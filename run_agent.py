#!/usr/bin/env python3

"""
Script to run the Day 7 Food & Grocery Ordering Voice Agent
"""

import sys
import subprocess
import os

def main():
    print("Starting Day 7 Food & Grocery Ordering Voice Agent...")
    
    # Change to the src directory
    src_dir = os.path.join(os.path.dirname(__file__), "src")
    if not os.path.exists(src_dir):
        print("Error: src directory not found!")
        return 1
        
    # Run the agent in dev mode
    try:
        subprocess.run([sys.executable, "-m", "agent", "dev"], cwd=src_dir)
    except KeyboardInterrupt:
        print("\nAgent stopped by user.")
    except Exception as e:
        print(f"Error running agent: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(main())