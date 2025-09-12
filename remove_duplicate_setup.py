#!/usr/bin/env python
"""
Remove Duplicate Setup Calls
Remove the setup calls that were added in the wrong location
"""

def main():
    print("Removing duplicate setup calls...")
    
    main_window_path = "src/gui/enhanced_main_window.py"
    
    # Read the file
    with open(main_window_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and remove the first occurrence (wrong location)
    new_lines = []
    skip_lines = 0
    
    for i, line in enumerate(lines):
        # Skip the wrong setup calls (around line 740)
        if i > 730 and i < 750 and "# Setup enhanced features" in line:
            print(f"Removing setup calls starting at line {i+1}")
            skip_lines = 4  # Skip this line and the next 4 setup calls
            continue
        
        if skip_lines > 0:
            if line.strip().startswith("self.setup_"):
                skip_lines -= 1
                continue
            else:
                skip_lines = 0
        
        new_lines.append(line)
    
    # Write back the cleaned content
    with open(main_window_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"Removed duplicate setup calls. File now has {len(new_lines)} lines (was {len(lines)})")

if __name__ == "__main__":
    main()