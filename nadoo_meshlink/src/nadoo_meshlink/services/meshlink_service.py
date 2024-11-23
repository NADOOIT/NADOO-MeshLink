"""
MeshLink Service: A P2P networking service using libp2p.

Features:
- Direct peer connections
- Message broadcasting
- Topic-based publish/subscribe
- Network statistics and peer management
"""

import os
import subprocess
import atexit
import signal
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import zmq
from nadoo_framework.core.service import Service, ServiceState

class MeshLinkService(Service):
    """A service that manages the P2P networking capabilities using libp2p."""
    
    def __init__(self):
        super().__init__(
            name="meshlink",
            description="P2P networking service using libp2p",
            version="0.1.0"
        )
        self._context: Optional[zmq.Context] = None
        self._socket: Optional[zmq.Socket] = None
        self._go_process: Optional[subprocess.Popen] = None
        self._zmq_port = "5555"
        self._node_address: Optional[str] = None
        self._active_topics: List[str] = []

    def _ensure_go_binary(self) -> str:
        """Ensure the Go binary is available and return its path."""
        package_dir = Path(__file__).parent.parent
        go_binary = package_dir / "go" / "meshlink"
        
        if not go_binary.exists():
            # Compile Go binary if it doesn't exist
            go_src = package_dir / "go" / "main.go"
            self.logger.info(f"Compiling Go binary from {go_src}")
            subprocess.run(["go", "build", "-o", str(go_binary), str(go_src)], check=True)
        
        return str(go_binary)

    async def start(self) -> None:
        """Start the MeshLink service."""
        try:
            # Start Go binary
            go_binary = self._ensure_go_binary()
            self._go_process = subprocess.Popen([go_binary])
            
            # Initialize ZMQ
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.connect(f"tcp://localhost:{self._zmq_port}")
            
            # Wait for Go service to start
            time.sleep(1)
            
            # Get node address
            self._node_address = await self.get_node_address()
            
            # Register cleanup
            atexit.register(self._cleanup)
            
            self.state = ServiceState.RUNNING
            self.logger.info(f"MeshLink service started. Node address: {self._node_address}")
            
        except Exception as e:
            self.state = ServiceState.ERROR
            self.logger.error(f"Failed to start MeshLink service: {e}")
            raise

    async def stop(self) -> None:
        """Stop the MeshLink service."""
        self._cleanup()
        self.state = ServiceState.STOPPED
        self.logger.info("MeshLink service stopped")

    def _cleanup(self):
        """Cleanup function to be called on exit."""
        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
        if self._go_process:
            self._go_process.terminate()
            self._go_process.wait()

    async def _send_message(self, msg_type: str, payload: Any) -> Optional[Dict]:
        """Send a message to the Go service and wait for response."""
        if not self._socket:
            raise RuntimeError("MeshLink service not initialized")
        
        message = {
            "type": msg_type,
            "payload": payload
        }
        
        try:
            self._socket.send_json(message)
            return self._socket.recv_json()
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return None

    async def connect_to_peer(self, peer_addr: str) -> bool:
        """Connect to a specific peer using their multiaddress."""
        response = await self._send_message("connect", peer_addr)
        return response is not None and response.get("success", False)

    async def broadcast_message(self, message: str) -> bool:
        """Broadcast a message to all connected peers."""
        response = await self._send_message("broadcast", message)
        return response is not None and response.get("success", False)

    async def get_node_address(self) -> Optional[str]:
        """Get this node's multiaddress."""
        response = await self._send_message("get_address", None)
        return response.get("address") if response else None

    async def join_topic(self, topic: str) -> bool:
        """Join a topic for pub/sub messaging."""
        response = await self._send_message("join_topic", topic)
        if response and response.get("success", False):
            self._active_topics.append(topic)
            return True
        return False

    async def publish_to_topic(self, topic: str, message: str) -> bool:
        """Publish a message to a specific topic."""
        if topic not in self._active_topics:
            if not await self.join_topic(topic):
                return False
        
        payload = {
            "topic": topic,
            "data": message
        }
        response = await self._send_message("publish_to_topic", payload)
        return response is not None and response.get("success", False)

    async def get_peers(self) -> List[Dict[str, Any]]:
        """Get information about connected peers."""
        response = await self._send_message("get_peers", None)
        return response.get("data", []) if response else []

    async def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics."""
        response = await self._send_message("get_network_stats", None)
        return response.get("data", {}) if response else {}

    async def disconnect_peer(self, peer_id: str) -> bool:
        """Disconnect from a specific peer."""
        response = await self._send_message("disconnect_peer", peer_id)
        return response is not None and response.get("success", False)

    @property
    def node_address(self) -> Optional[str]:
        """Get the current node's address."""
        return self._node_address

    @property
    def active_topics(self) -> List[str]:
        """Get the list of active topics."""
        return self._active_topics.copy()
