#!/usr/bin/env python3
"""
Quick launcher script for the Technical Analysis Agent.
This script provides an easy way to launch different modes without remembering command-line arguments.
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Interactive launcher for the Technical Analysis Agent."""
    print("=" * 60)
    print("Technical Analysis Agent - Quick Launcher")
    print("=" * 60)
    print("\nSelect mode:")
    print("1. Discord Bot")
    print("2. CLI Interface")
    print("3. Run Tests")
    print("4. Validate Environment")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                print("\nStarting Discord Bot...")
                subprocess.run([sys.executable, "main.py", "discord"], check=True)
                break
            elif choice == "2":
                print("\nStarting CLI Interface...")
                subprocess.run([sys.executable, "main.py", "cli"], check=True)
                break
            elif choice == "3":
                print("\nRunning Tests...")
                subprocess.run([sys.executable, "main.py", "test"], check=True)
                break
            elif choice == "4":
                print("\nValidating Environment...")
                subprocess.run([sys.executable, "main.py", "discord", "--validate"], check=True)
                break
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except subprocess.CalledProcessError as e:
            print(f"Error running command: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    # Change to the script's directory
    script_dir = Path(__file__).parent
    if script_dir != Path.cwd():
        print(f"Changing directory to: {script_dir}")
        import os
        os.chdir(script_dir)
    
    main()
