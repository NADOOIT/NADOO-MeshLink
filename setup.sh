#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Starting NADOO-MeshLink setup...${NC}"

# Detect OS
detect_os() {
    case "$OSTYPE" in
        darwin*)  OS="macos" ;;
        linux*)   OS="linux" ;;
        msys*)    OS="windows" ;;
        cygwin*)  OS="windows" ;;
        *)        OS="unknown" ;;
    esac
    echo -e "${BLUE}Detected OS: ${OS}${NC}"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Go based on platform
install_go() {
    if ! command_exists go; then
        echo -e "${BLUE}Installing Go...${NC}"
        case $OS in
            "macos")
                brew install go
                ;;
            "linux")
                # Download latest Go for Linux
                GO_VERSION=$(curl -s https://golang.org/dl/ | grep -oP 'go([0-9\.]+)\.linux-amd64\.tar\.gz' | head -n 1)
                wget https://golang.org/dl/$GO_VERSION
                sudo tar -C /usr/local -xzf $GO_VERSION
                echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
                source ~/.bashrc
                rm $GO_VERSION
                ;;
            "windows")
                echo -e "${YELLOW}Please install Go from https://golang.org/dl/${NC}"
                echo -e "${YELLOW}After installation, run this script again.${NC}"
                exit 1
                ;;
            *)
                echo -e "${RED}Unsupported OS for automatic Go installation${NC}"
                exit 1
                ;;
        esac
    fi
    echo -e "${GREEN}Go is installed!${NC}"
}

# Install Poetry based on platform
install_poetry() {
    if ! command_exists poetry; then
        echo -e "${BLUE}Installing Poetry...${NC}"
        case $OS in
            "windows")
                (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
                ;;
            *)
                curl -sSL https://install.python-poetry.org | python3 -
                ;;
        esac
    fi
    echo -e "${GREEN}Poetry is installed!${NC}"
}

# Install package managers
install_package_manager() {
    case $OS in
        "macos")
            if ! command_exists brew; then
                echo -e "${BLUE}Installing Homebrew...${NC}"
                /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            fi
            ;;
        "linux")
            if command_exists apt-get; then
                sudo apt-get update
            elif command_exists yum; then
                sudo yum update
            elif command_exists pacman; then
                sudo pacman -Syu
            fi
            ;;
        "windows")
            if ! command_exists choco; then
                echo -e "${YELLOW}Please install Chocolatey from https://chocolatey.org/install${NC}"
                echo -e "${YELLOW}After installation, run this script again.${NC}"
                exit 1
            fi
            ;;
    esac
}

# Check Python version
check_python() {
    local python_cmd
    case $OS in
        "windows")
            python_cmd="python"
            ;;
        *)
            python_cmd="python3"
            ;;
    esac

    if ! command_exists $python_cmd; then
        echo -e "${RED}Python 3 is required but not installed.${NC}"
        case $OS in
            "macos")
                brew install python
                ;;
            "linux")
                if command_exists apt-get; then
                    sudo apt-get install -y python3 python3-pip
                elif command_exists yum; then
                    sudo yum install -y python3 python3-pip
                elif command_exists pacman; then
                    sudo pacman -S python python-pip
                fi
                ;;
            "windows")
                choco install python
                ;;
        esac
    fi
    
    version=$($python_cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$version < 3.8" | bc -l) )); then
        echo -e "${RED}Python 3.8 or higher is required. Current version: $version${NC}"
        exit 1
    fi
    echo -e "${GREEN}Python $version is installed!${NC}"
}

# Install ZeroMQ dependencies
install_zmq_deps() {
    echo -e "${BLUE}Installing ZeroMQ dependencies...${NC}"
    case $OS in
        "macos")
            brew install zeromq
            ;;
        "linux")
            if command_exists apt-get; then
                sudo apt-get install -y libzmq3-dev
            elif command_exists yum; then
                sudo yum install -y zeromq-devel
            elif command_exists pacman; then
                sudo pacman -S zeromq
            fi
            ;;
        "windows")
            choco install zeromq
            ;;
    esac
    echo -e "${GREEN}ZeroMQ dependencies installed!${NC}"
}

# Build Go binary
build_go_binary() {
    echo -e "${BLUE}Building Go binary...${NC}"
    cd go
    go mod tidy
    
    # Build for current platform
    case $OS in
        "windows")
            go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink.exe
            ;;
        *)
            go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink
            ;;
    esac
    
    # Cross-compile for other platforms
    echo -e "${BLUE}Cross-compiling for other platforms...${NC}"
    
    # Linux
    GOOS=linux GOARCH=amd64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_linux_amd64
    GOOS=linux GOARCH=arm64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_linux_arm64
    
    # macOS
    GOOS=darwin GOARCH=amd64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_darwin_amd64
    GOOS=darwin GOARCH=arm64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_darwin_arm64
    
    # Windows
    GOOS=windows GOARCH=amd64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_windows_amd64.exe
    
    # Android (requires Android NDK)
    if command_exists $ANDROID_NDK_ROOT; then
        echo -e "${BLUE}Building for Android...${NC}"
        GOOS=android GOARCH=arm64 go build -o ../nadoo_meshlink/src/nadoo_meshlink/go/meshlink_android_arm64
    else
        echo -e "${YELLOW}Android NDK not found, skipping Android build${NC}"
    fi
    
    cd ..
    echo -e "${GREEN}Go binaries built successfully!${NC}"
}

# Install Python package
install_package() {
    echo -e "${BLUE}Installing NADOO-MeshLink package...${NC}"
    poetry install
    echo -e "${GREEN}Package installed successfully!${NC}"
}

# Setup mobile development environment
setup_mobile() {
    echo -e "${BLUE}Setting up mobile development environment...${NC}"
    
    # Install gomobile
    go install golang.org/x/mobile/cmd/gomobile@latest
    go install golang.org/x/mobile/cmd/gobind@latest
    
    # Initialize gomobile
    gomobile init
    
    # Build mobile libraries
    cd go
    echo -e "${BLUE}Building mobile libraries...${NC}"
    
    # iOS
    if [[ $OS == "macos" ]]; then
        echo -e "${BLUE}Building for iOS...${NC}"
        gomobile bind -target=ios -o ../mobile/ios/NADOOMeshLink.framework
    else
        echo -e "${YELLOW}iOS build requires macOS${NC}"
    fi
    
    # Android
    echo -e "${BLUE}Building for Android...${NC}"
    gomobile bind -target=android -o ../mobile/android/nadoomeshlink.aar
    
    cd ..
    echo -e "${GREEN}Mobile libraries built successfully!${NC}"
}

# Verify installation
verify_installation() {
    echo -e "${BLUE}Verifying installation...${NC}"
    
    # Check Go
    if ! go version > /dev/null 2>&1; then
        echo -e "${RED}Go installation verification failed${NC}"
        exit 1
    fi
    
    # Check Poetry
    if ! poetry --version > /dev/null 2>&1; then
        echo -e "${RED}Poetry installation verification failed${NC}"
        exit 1
    fi
    
    # Check Python package
    if ! poetry run python -c "import nadoo_meshlink" > /dev/null 2>&1; then
        echo -e "${RED}NADOO-MeshLink package installation verification failed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Installation verified successfully!${NC}"
}

# Main installation process
main() {
    detect_os
    echo -e "${BLUE}Checking system requirements...${NC}"
    
    # Install basic requirements
    install_package_manager
    install_go
    install_poetry
    check_python
    install_zmq_deps
    
    # Create mobile directories
    mkdir -p mobile/ios mobile/android
    
    # Build and install
    build_go_binary
    setup_mobile
    install_package
    verify_installation
    
    echo -e "${GREEN}NADOO-MeshLink installation completed!${NC}"
    echo -e "${BLUE}You can now use NADOO-MeshLink in your projects.${NC}"
    echo -e "${BLUE}Check the examples directory for usage examples.${NC}"
    
    case $OS in
        "windows")
            echo -e "${YELLOW}Note: On Windows, you may need to add Go and Poetry to your PATH manually.${NC}"
            ;;
        "linux")
            echo -e "${YELLOW}Note: You may need to restart your terminal for PATH changes to take effect.${NC}"
            ;;
    esac
}

# Run main installation
main
