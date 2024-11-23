"""NADOO MeshLink Service Module."""
import asyncio
import json
import logging
import os
import platform
from pathlib import Path
from typing import Any, Dict, List, Optional

import zmq
import zmq.asyncio
from nadoo_framework import Service, ProcessManager

logger = logging.getLogger(__name__)


class MeshLinkService(Service):
    """MeshLink P2P Networking Service."""

    def __init__(self):
        """Initialize MeshLinkService."""
        super().__init__()
        self.name = "meshlink"
        self.description = "NADOO MeshLink P2P Networking Service"
        self._process_id: Optional[str] = None
        self._zmq_context: Optional[zmq.asyncio.Context] = None
        self._socket: Optional[zmq.asyncio.Socket] = None
        self._running = False

    @property
    def go_binary_path(self) -> Path:
        """Get the path to the Go binary."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        # Determine binary name based on platform
        if system == "windows":
            binary_name = f"meshlink_{system}_{machine}.exe"
        else:
            binary_name = f"meshlink_{system}_{machine}"
        
        # Get package installation directory
        package_dir = Path(__file__).parent.parent
        return package_dir / "go" / binary_name

    async def start(self) -> None:
        """Start the MeshLink service."""
        if self._running:
            return

        try:
            # Get ProcessManager
            process_manager = self.framework.get_service("process_manager")
            if not process_manager:
                raise RuntimeError("ProcessManager service not found")

            # Make binary executable on Unix systems
            if platform.system().lower() != "windows":
                self.go_binary_path.chmod(0o755)

            # Start the Go process through ProcessManager
            self._process_id = await process_manager.start_process(
                command=str(self.go_binary_path),
                name="meshlink_go",
                restart_on_failure=True,
                stdout_callback=self._handle_process_output,
                stderr_callback=self._handle_process_error
            )

            # Initialize ZMQ connection
            await self._init_zmq()
            self._running = True
            logger.info("MeshLink service started successfully")
        except Exception as e:
            logger.error(f"Failed to start MeshLink service: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        """Stop the MeshLink service."""
        if not self._running:
            return

        try:
            # Stop the Go process through ProcessManager
            if self._process_id:
                process_manager = self.framework.get_service("process_manager")
                if process_manager:
                    await process_manager.stop_process(self._process_id)
                self._process_id = None

            # Cleanup ZMQ
            if self._socket:
                self._socket.close()
            if self._zmq_context:
                self._zmq_context.term()

            self._running = False
            logger.info("MeshLink service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping MeshLink service: {e}")
            raise

    async def _init_zmq(self) -> None:
        """Initialize ZeroMQ connection."""
        self._zmq_context = zmq.asyncio.Context()
        self._socket = self._zmq_context.socket(zmq.REQ)
        self._socket.connect("tcp://localhost:5555")

    async def _handle_process_output(self, line: str) -> None:
        """Handle process stdout."""
        logger.info(f"MeshLink Go: {line}")

    async def _handle_process_error(self, line: str) -> None:
        """Handle process stderr."""
        logger.error(f"MeshLink Go Error: {line}")

    async def _send_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Send command to Go service."""
        if not self._socket:
            raise RuntimeError("ZeroMQ socket not initialized")

        message = {"command": command, **kwargs}
        await self._socket.send_json(message)
        response = await self._socket.recv_json()

        if response.get("error"):
            raise RuntimeError(response["error"])

        return response

    async def connect(self, address: str) -> Dict[str, Any]:
        """Connect to a peer."""
        return await self._send_command("connect", address=address)

    async def broadcast(self, message: str) -> Dict[str, Any]:
        """Broadcast a message to all peers."""
        return await self._send_command("broadcast", message=message)

    async def join_topic(self, topic: str) -> Dict[str, Any]:
        """Join a topic."""
        return await self._send_command("join", topic=topic)

    async def publish_to_topic(self, topic: str, message: str) -> Dict[str, Any]:
        """Publish a message to a topic."""
        return await self._send_command("publish", topic=topic, message=message)

    async def get_node_address(self) -> str:
        """Get the node's address."""
        response = await self._send_command("address")
        return response["address"]

    async def get_peers(self) -> List[str]:
        """Get list of connected peers."""
        response = await self._send_command("peers")
        return response["peers"]

    async def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        return await self._send_command("stats")
