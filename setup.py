#!/usr/bin/env python3
import sys
import subprocess
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent
    
    # Locate the setup.py within the skill directory tree
    candidates = list(root.glob("**/scripts/setup.py"))
    
    # Exclude this file itself if it matches (it shouldn't since it's not under a scripts/ folder)
    candidates = [c for c in candidates if c != root / "setup.py"]
    
    if not candidates:
        print("Error: Could not find the actual setup script (scripts/setup.py) under the skills folder.")
        sys.exit(1)
        
    setup_script = candidates[0]
    print(f"Auto-detected setup script at: {setup_script}")
    
    # Run the setup script with the same interpreter and arguments
    cmd = [sys.executable, str(setup_script)] + sys.argv[1:]
    try:
        sys.exit(subprocess.run(cmd).returncode)
    except KeyboardInterrupt:
        print("\nSetup cancelled.")
        sys.exit(1)

if __name__ == "__main__":
    main()
