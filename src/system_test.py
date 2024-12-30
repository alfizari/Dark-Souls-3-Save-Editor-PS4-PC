import platform
import subprocess
import sys
from datetime import datetime
import os

def test_system_compatibility():
    # Redirect stdout to both file and console
    exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
    log_path = os.path.join(exe_dir, 'system_compatibility.log')
    log_file = open(log_path, 'w')
    original_stdout = sys.stdout
    
    # Create a custom write function to write to both outputs
    def write_both(text):
        log_file.write(text)
        original_stdout.write(text)
        
    # Add timestamp at the start of log
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    write_both(f"System Compatibility Test - {timestamp}\n")
    write_both("-" * 50 + "\n")
    
    system = platform.system()
    write_both(f"Detected Operating System: {system}\n")
    
    if system in ['Linux', 'Darwin']:
        try:
            wine_version = subprocess.run(['wine', '--version'], 
                                       capture_output=True, 
                                       text=True, 
                                       check=True)
            write_both(f"Wine is installed: {wine_version.stdout.strip()}\n")
            result = True
        except subprocess.CalledProcessError:
            write_both("Wine is not installed. Please install Wine to run Windows executables.\n")
            result = False
        except FileNotFoundError:
            install_cmd = "brew install wine" if system == "Darwin" else "install Wine"
            write_both(f"Wine is not installed or not in PATH. Please {install_cmd} to run Windows executables.\n")
            result = False
    else:
        write_both("Native Windows environment - no Wine needed\n")
        result = True
    
    write_both(f"\nSystem compatibility test {'passed' if result else 'failed'}\n")
    
    # Close the log file
    log_file.close()
    return result

if __name__ == "__main__":
    result = test_system_compatibility() 