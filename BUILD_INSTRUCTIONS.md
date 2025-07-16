# EchoV2 Standalone Mac App Build Instructions

This guide will help you build EchoV2 into a standalone Mac app that includes the Python backend and requires no separate installation.

## Prerequisites

Before building, ensure you have the following installed:

### 1. Node.js and npm
```bash
# Check if installed
node --version
npm --version

# Install via Homebrew if needed
brew install node
```

### 2. Python 3.8+
```bash
# Check if installed
python3 --version

# Should show Python 3.8 or higher
```

### 3. Rust and Cargo
```bash
# Install Rust (required for Tauri)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Verify installation
rustc --version
cargo --version
```

### 4. Tauri Prerequisites (macOS)
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Accept Xcode license
sudo xcodebuild -license accept
```

## Build Process

### Option 1: Automated Build (Recommended)

Use the automated build script:

```bash
# Navigate to project directory
cd /path/to/EchoV2

# Run the automated build script
npm run build:standalone
```

### Option 2: Manual Build Steps

If you prefer to build manually or need to debug issues:

#### Step 1: Build Python Backend
```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dependencies (including PyInstaller)
pip install -r requirements.txt

# Build standalone executable
pyinstaller echov2-backend.spec

# Verify executable was created
ls -la dist/echov2-backend
```

#### Step 2: Build Frontend
```bash
# From project root
npm install
npm run build
```

#### Step 3: Build Tauri App
```bash
npm run tauri:build
```

## Output

After a successful build, you'll find the standalone app at:
```
src-tauri/target/release/bundle/macos/EchoV2.app
```

This app bundle contains:
- The React frontend (built with Vite)
- The Tauri wrapper (Rust-based desktop app framework)
- The Python backend executable (built with PyInstaller)
- All configuration files

## Usage

Simply double-click `EchoV2.app` to run the application. The backend will start automatically when the app launches and stop when the app is closed.

## Troubleshooting

### Build Issues

1. **Python Backend Build Fails**
   - Ensure all Python dependencies are installed: `pip install -r backend/requirements.txt`
   - Check Python version: `python3 --version` (must be 3.8+)
   - Try rebuilding: `cd backend && pyinstaller echov2-backend.spec`

2. **Frontend Build Fails**
   - Clear node modules: `rm -rf node_modules && npm install`
   - Check Node.js version: `node --version` (must be 16+)

3. **Tauri Build Fails**
   - Ensure Rust is installed: `rustc --version`
   - Update Rust: `rustup update`
   - Clean and rebuild: `cd src-tauri && cargo clean && cd .. && npm run tauri:build`

4. **Backend Not Starting**
   - Check that `backend/dist/echov2-backend` exists and is executable
   - Verify Tauri configuration includes the backend in `externalBin`
   - Check app logs for process startup errors

### Runtime Issues

1. **Backend Connection Errors**
   - The frontend includes retry logic, but you may need to wait 10-30 seconds for backend startup
   - Check Activity Monitor for `echov2-backend` process
   - Verify no other applications are using port 8000

2. **Plugin/Provider Issues**
   - Ensure AI provider API keys are configured in the app settings
   - Check that provider endpoints (OpenAI, Anthropic, Ollama) are accessible

## Architecture

The standalone app uses the following architecture:

```
EchoV2.app/
├── Contents/
│   ├── MacOS/
│   │   ├── EchoV2              # Tauri frontend executable
│   │   └── echov2-backend      # Python backend executable
│   ├── Resources/
│   │   ├── config/             # Configuration files
│   │   └── ...                 # Other resources
│   └── Info.plist              # macOS app metadata
```

When launched:
1. Tauri starts the main app process
2. Rust code automatically spawns the Python backend process
3. Frontend connects to backend via HTTP (localhost:8000)
4. Backend provides AI chat functionality with pluggable providers
5. When app closes, backend process is automatically terminated

This creates a true standalone application that users can run without any additional setup or dependencies.