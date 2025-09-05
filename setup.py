#!/usr/bin/env python3
"""
Setup script for YouTube Downloader Pro

This script sets up the complete development environment including:
- Virtual environment creation
- Dependency installation
- FFmpeg setup (Windows)
- Project validation
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors gracefully."""
    print(f"📋 {description}...")
    try:
        if isinstance(command, list):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
        else:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def create_venv():
    """Create virtual environment."""
    if Path("venv").exists():
        print("📁 Virtual environment already exists")
        return True
    
    return run_command([sys.executable, "-m", "venv", "venv"], "Creating virtual environment")

def install_dependencies():
    """Install Python dependencies."""
    if platform.system() == "Windows":
        python_path = "venv\\Scripts\\python.exe"
    else:
        python_path = "venv/bin/python"
    
    commands = [
        ([python_path, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"),
        ([python_path, "-m", "pip", "install", "--only-binary=:all:", "-r", "requirements.txt"], "Installing Python dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    return True

def setup_ffmpeg_windows():
    """Download and setup FFmpeg for Windows."""
    ffmpeg_dir = Path("venv/ffmpeg")
    
    if ffmpeg_dir.exists() and (ffmpeg_dir / "ffmpeg.exe").exists():
        print("🎬 FFmpeg already installed in venv")
        return True
    
    print("🎬 Setting up FFmpeg for Windows...")
    
    try:
        # Create ffmpeg directory
        ffmpeg_dir.mkdir(parents=True, exist_ok=True)
        
        # Download FFmpeg (using a smaller, essential build)
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = "ffmpeg-temp.zip"
        
        print("📥 Downloading FFmpeg (this may take a few minutes)...")
        urllib.request.urlretrieve(ffmpeg_url, zip_path)
        
        print("📦 Extracting FFmpeg...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Extract only the essential binaries
            for member in zip_ref.namelist():
                if member.endswith(('ffmpeg.exe', 'ffprobe.exe')):
                    # Extract to venv/ffmpeg/
                    member_path = Path(member)
                    target_path = ffmpeg_dir / member_path.name
                    
                    with zip_ref.open(member) as source:
                        with open(target_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
        
        # Cleanup
        os.remove(zip_path)
        
        # Verify installation
        if (ffmpeg_dir / "ffmpeg.exe").exists():
            print("✅ FFmpeg installed successfully in venv/ffmpeg/")
            return True
        else:
            print("❌ FFmpeg installation verification failed")
            return False
            
    except Exception as e:
        print(f"❌ FFmpeg setup failed: {e}")
        print("ℹ️  The app will still work without FFmpeg (audio-only downloads)")
        return False

def setup_ffmpeg():
    """Setup FFmpeg based on platform."""
    system = platform.system()
    
    if system == "Windows":
        return setup_ffmpeg_windows()
    elif system == "Darwin":  # macOS
        print("🍎 On macOS, install FFmpeg with: brew install ffmpeg")
        print("ℹ️  Or the app will work without it (audio-only downloads)")
        return True
    elif system == "Linux":
        print("🐧 On Linux, install FFmpeg with your package manager:")
        print("   Ubuntu/Debian: sudo apt install ffmpeg")
        print("   CentOS/RHEL: sudo yum install ffmpeg")
        print("ℹ️  Or the app will work without it (audio-only downloads)")
        return True
    else:
        print(f"❓ Unknown platform: {system}")
        print("ℹ️  Please install FFmpeg manually, or the app will work without it")
        return True

def validate_setup():
    """Validate that everything is set up correctly."""
    print("🔍 Validating setup...")
    
    checks = [
        (Path("venv").exists(), "Virtual environment exists"),
        (Path("venv/ffmpeg/ffmpeg.exe").exists() if platform.system() == "Windows" 
         else True, "FFmpeg available (Windows)"),
        (Path("youtube_downloader.py").exists(), "Main application exists"),
        (Path("requirements.txt").exists(), "Requirements file exists")
    ]
    
    all_good = True
    for check, description in checks:
        if check:
            print(f"✅ {description}")
        else:
            print(f"❌ {description}")
            all_good = False
    
    return all_good

def main():
    """Main setup function."""
    print("🚀 YouTube Downloader Pro - Automatic Setup")
    print("=" * 50)
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    steps = [
        (create_venv, "Virtual Environment"),
        (install_dependencies, "Python Dependencies"), 
        (setup_ffmpeg, "FFmpeg Setup"),
        (validate_setup, "Setup Validation")
    ]
    
    failed_steps = []
    
    for step_func, step_name in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 30)
        
        if not step_func():
            failed_steps.append(step_name)
    
    print("\n" + "=" * 50)
    
    if not failed_steps:
        print("🎉 Setup completed successfully!")
        print("\n📜 Ready to use:")
        print("The application will now start automatically...")
    else:
        print(f"⚠️  Setup completed with issues in: {', '.join(failed_steps)}")
        print("ℹ️  The app may still work with limited functionality")
        
    print("\n🔄 Environment setup complete!")
    print("📚 See README.md for usage instructions")

if __name__ == "__main__":
    main()
