import subprocess
import sys

def install_package(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    print("Installing django-jalali-date...")
    install_package("django-jalali-date")
    print("Package installed successfully!")
    
    # Test import
    try:
        from jalali_date.fields import JalaliDateField
        print("Import test successful!")
    except ImportError as e:
        print(f"Import failed: {e}")
        
except Exception as e:
    print(f"Installation failed: {e}")