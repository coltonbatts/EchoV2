#!/usr/bin/env python3
"""
Build script for creating a standalone EchoV2 Mac app.
This script automates the complete build process:
1. Builds the Python backend with PyInstaller
2. Builds the frontend with Vite
3. Builds the complete Tauri app with embedded backend
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, description=""):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Working directory: {cwd or os.getcwd()}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout:
            print("✅ Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print("stdout:")
            print(e.stdout)
        if e.stderr:
            print("stderr:")
            print(e.stderr)
        return False

def main():
    # Get project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    backend_dir = project_root / "backend"
    
    print("🚀 Starting EchoV2 Standalone Build Process")
    print(f"Project root: {project_root}")
    
    # Step 1: Build Python backend with PyInstaller
    if not run_command(
        ["source", "venv/bin/activate", "&&", "pyinstaller", "echov2-backend.spec"],
        cwd=backend_dir,
        description="Building Python backend executable with PyInstaller"
    ):
        # Try alternative approach for shell command
        if not run_command(
            ["/bin/bash", "-c", "source venv/bin/activate && pyinstaller echov2-backend.spec"],
            cwd=backend_dir,
            description="Building Python backend executable (alternative method)"
        ):
            print("❌ Failed to build Python backend")
            return False
    
    # Verify backend executable was created
    backend_executable = backend_dir / "dist" / "echov2-backend"
    if not backend_executable.exists():
        print(f"❌ Backend executable not found at {backend_executable}")
        return False
    
    print(f"✅ Backend executable created: {backend_executable}")
    
    # Step 2: Install frontend dependencies and build
    if not run_command(
        ["npm", "install"],
        cwd=project_root,
        description="Installing frontend dependencies"
    ):
        print("❌ Failed to install frontend dependencies")
        return False
    
    if not run_command(
        ["npm", "run", "build"],
        cwd=project_root,
        description="Building frontend with Vite"
    ):
        print("❌ Failed to build frontend")
        return False
    
    # Step 3: Build Tauri app (this will include the backend executable)
    if not run_command(
        ["npm", "run", "tauri:build"],
        cwd=project_root,
        description="Building complete Tauri app with embedded backend"
    ):
        print("❌ Failed to build Tauri app")
        return False
    
    # Step 4: Verify the final app bundle
    app_bundle = project_root / "src-tauri" / "target" / "release" / "bundle" / "macos" / "EchoV2.app"
    if app_bundle.exists():
        print(f"\n🎉 SUCCESS! Standalone app created at:")
        print(f"   {app_bundle}")
        
        # Check if backend is included
        backend_in_bundle = app_bundle / "Contents" / "MacOS" / "echov2-backend"
        if backend_in_bundle.exists():
            print("✅ Backend executable is included in the app bundle")
        else:
            print("⚠️  Backend executable not found in app bundle")
        
        print(f"\n📋 App bundle contents:")
        if (app_bundle / "Contents").exists():
            for item in (app_bundle / "Contents").iterdir():
                print(f"   - {item.name}")
        
        print(f"\n🏁 Build complete! You can now run the app by double-clicking:")
        print(f"   {app_bundle}")
        
        return True
    else:
        print("❌ App bundle not found after build")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)