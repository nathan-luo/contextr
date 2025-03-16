#!/usr/bin/env python3
"""
Installation script for contextr.
Creates symlinks to make commands available globally without PATH manipulation.
"""
import os
import platform
import shutil
import site
import subprocess
import sys
from pathlib import Path

def get_scripts_dir():
    """Get platform-appropriate scripts directory."""
    system = platform.system()
    if system == "Windows":
        return Path(site.USER_SITE).parent / "Scripts"
    else:  # Unix-like (macOS, Linux)
        return Path(os.path.expanduser("~/.local/bin"))

def create_symlinks():
    """Create symlinks to the contextr entry points."""
    venv_dir = Path(__file__).resolve().parent
    
    # Make sure we're in a contextr directory
    if not (venv_dir / "src" / "contextr").exists():
        print("Error: This script must be run from the contextr root directory.")
        return False
    
    # First, install in development mode if not already
    subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."])
    
    scripts_dir = get_scripts_dir()
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    system = platform.system()
    
    # Find entry points created by the install
    if system == "Windows":
        # For Windows, we need to look for the .exe files
        source_ctxr = next(Path(sys.prefix).rglob("Scripts/ctxr.exe"), None)
        source_contextr = next(Path(sys.prefix).rglob("Scripts/contextr.exe"), None)
        
        # Create .bat files in a PATH location
        if source_ctxr:
            with open(scripts_dir / "ctxr.bat", "w") as f:
                f.write(f'@echo off\n"{source_ctxr}" %*')
            
        if source_contextr:
            with open(scripts_dir / "contextr.bat", "w") as f:
                f.write(f'@echo off\n"{source_contextr}" %*')
    else:
        # For Unix, create symlinks to the Python scripts
        source_ctxr = next(Path(sys.prefix).rglob("bin/ctxr"), None)
        source_contextr = next(Path(sys.prefix).rglob("bin/contextr"), None)
        
        if source_ctxr:
            target_ctxr = scripts_dir / "ctxr"
            if target_ctxr.exists():
                target_ctxr.unlink()
            os.symlink(source_ctxr, target_ctxr)
            os.chmod(target_ctxr, 0o755)
            
        if source_contextr:
            target_contextr = scripts_dir / "contextr"
            if target_contextr.exists():
                target_contextr.unlink()
            os.symlink(source_contextr, target_contextr)
            os.chmod(target_contextr, 0o755)
    
    return True

def check_path(scripts_dir):
    """Check if scripts_dir is in PATH and provide instructions if not."""
    system = platform.system()
    path_env = os.environ.get("PATH", "")
    
    if str(scripts_dir) not in path_env:
        print(f"\nNOTE: {scripts_dir} is not in your PATH.")
        
        if system == "Windows":
            print("\nTo add it to your PATH:")
            print(f"1. Press Win+X and select 'System'")
            print(f"2. Click 'Advanced system settings'")
            print(f"3. Click 'Environment Variables'")
            print(f"4. Under 'User variables', edit 'Path'")
            print(f"5. Add '{scripts_dir}'")
            print(f"6. Restart your command prompt")
        else:  # Unix-like
            shell = os.environ.get("SHELL", "").split("/")[-1]
            if shell == "bash":
                rc_file = "~/.bashrc"
            elif shell == "zsh":
                rc_file = "~/.zshrc"
            else:
                rc_file = "your shell's rc file"
                
            print(f"\nTo add it to your PATH, add this line to {rc_file}:")
            print(f"export PATH=\"$PATH:{scripts_dir}\"")
            print("\nThen restart your terminal or run:")
            print(f"source {rc_file}")

def main():
    """Main installation function."""
    print("Installing contextr...")
    
    if create_symlinks():
        scripts_dir = get_scripts_dir()
        print(f"\nSuccess! contextr commands installed to: {scripts_dir}")
        
        # Check if the scripts directory is in PATH
        check_path(scripts_dir)
        
        print("\nYou can now use the following commands from anywhere:")
        print("  ctxr init        - Initialize contextr in a project")
        print("  ctxr watch '*.py' - Add files to watch")
        print("  ctxr sync        - Sync and export to clipboard")
    else:
        print("\nInstallation failed. Please try installing with pip instead:")
        print("pip install contextr")

if __name__ == "__main__":
    main()