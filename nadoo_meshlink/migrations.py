"""NADOO MeshLink Migration Module."""
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from nadoo_migration import Migration


class MeshLinkMigration(Migration):
    """Migration handler for NADOO MeshLink."""

    def __init__(self):
        """Initialize MeshLinkMigration."""
        super().__init__()
        self.name = "meshlink"
        self.description = "NADOO MeshLink P2P Networking Plugin"
        self._go_binary_path = None

    @property
    def go_binary_path(self) -> Path:
        """Get the path to the Go binary."""
        if self._go_binary_path is None:
            system = platform.system().lower()
            machine = platform.machine().lower()
            
            # Determine binary name based on platform
            if system == "windows":
                binary_name = f"meshlink_{system}_{machine}.exe"
            else:
                binary_name = f"meshlink_{system}_{machine}"
            
            # Get package installation directory
            package_dir = Path(__file__).parent
            self._go_binary_path = package_dir / "go" / binary_name
        
        return self._go_binary_path

    def _find_go(self) -> Optional[str]:
        """Find Go installation."""
        try:
            return shutil.which("go")
        except Exception:
            return None

    def _install_go(self) -> bool:
        """Install Go if not present."""
        system = platform.system().lower()
        
        try:
            if system == "darwin":
                subprocess.run(["brew", "install", "go"], check=True)
            elif system == "linux":
                if shutil.which("apt-get"):
                    subprocess.run(["sudo", "apt-get", "install", "-y", "golang"], check=True)
                elif shutil.which("yum"):
                    subprocess.run(["sudo", "yum", "install", "-y", "golang"], check=True)
                elif shutil.which("pacman"):
                    subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "go"], check=True)
            elif system == "windows":
                subprocess.run(["choco", "install", "golang", "-y"], check=True)
            return True
        except Exception:
            return False

    def _build_go_binary(self) -> bool:
        """Build the Go binary for the current platform."""
        try:
            # Get source directory
            go_src_dir = Path(__file__).parent / "go"
            
            # Set up environment variables
            env = os.environ.copy()
            env["CGO_ENABLED"] = "1"
            
            # Build the binary
            subprocess.run(
                ["go", "build", "-o", str(self.go_binary_path)],
                cwd=str(go_src_dir),
                env=env,
                check=True,
            )
            
            # Make binary executable on Unix systems
            if platform.system().lower() != "windows":
                self.go_binary_path.chmod(0o755)
            
            return True
        except Exception:
            return False

    def check(self) -> bool:
        """Check if migration is needed."""
        # Check if binary exists and is executable
        if not self.go_binary_path.exists():
            return True
        
        if platform.system().lower() != "windows":
            if not os.access(self.go_binary_path, os.X_OK):
                return True
        
        return False

    def up(self) -> bool:
        """Perform migration up."""
        try:
            # Ensure Go is installed
            if not self._find_go():
                if not self._install_go():
                    return False
            
            # Build Go binary
            if not self._build_go_binary():
                return False
            
            return True
        except Exception:
            return False

    def down(self) -> bool:
        """Perform migration down."""
        try:
            # Remove Go binary if it exists
            if self.go_binary_path.exists():
                self.go_binary_path.unlink()
            return True
        except Exception:
            return False
