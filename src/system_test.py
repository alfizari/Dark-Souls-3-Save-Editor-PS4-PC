import platform
import subprocess

def test_system_compatibility():
    """Test system compatibility for running executables"""
    system = platform.system()
    print(f"Detected Operating System: {system}")
    
    if system == 'Linux':
        try:
            wine_version = subprocess.run(['wine', '--version'], 
                                       capture_output=True, 
                                       text=True, 
                                       check=True)
            print(f"Wine is installed: {wine_version.stdout.strip()}")
            return True
        except subprocess.CalledProcessError:
            print("Wine is not installed. Please install Wine to run Windows executables.")
            return False
        except FileNotFoundError:
            print("Wine is not installed or not in PATH. Please install Wine to run Windows executables.")
            return False
    else:
        print("Native Windows environment - no Wine needed")
        return True

if __name__ == "__main__":
    # This will run when the script is executed directly
    result = test_system_compatibility()
    print(f"\nSystem compatibility test {'passed' if result else 'failed'}") 