"""Example client for NADOO-MeshLink service."""
import asyncio
import json
import logging
from typing import Dict, Any, Optional

import zmq.asyncio

logger = logging.getLogger(__name__)


class NADOOMeshLinkClient:
    """Client for interacting with NADOO-MeshLink service."""

    def __init__(self, zmq_port: str = "5555"):
        """Initialize the client.

        Args:
            zmq_port: ZMQ port for communication with MeshLink service
        """
        self._context: Optional[zmq.asyncio.Context] = None
        self._socket: Optional[zmq.asyncio.Socket] = None
        self._zmq_port = zmq_port
        self._connected = False

    async def connect(self) -> None:
        """Connect to MeshLink service."""
        if self._connected:
            return

        self._context = zmq.asyncio.Context()
        self._socket = self._context.socket(zmq.REQ)
        self._socket.connect(f"tcp://localhost:{self._zmq_port}")
        self._connected = True
        logger.info("Connected to MeshLink service")

    async def close(self) -> None:
        """Close connection to MeshLink service."""
        if not self._connected:
            return

        if self._socket:
            self._socket.close()
        if self._context:
            self._context.term()
        self._connected = False
        logger.info("Disconnected from MeshLink service")

    async def _send_command(self, command: str, **kwargs) -> Dict[str, Any]:
        """Send command to MeshLink service.

        Args:
            command: Command name
            **kwargs: Additional command arguments

        Returns:
            Dict[str, Any]: Service response

        Raises:
            RuntimeError: If not connected or command fails
        """
        if not self._connected or not self._socket:
            raise RuntimeError("Not connected to MeshLink service")

        message = {"command": command, **kwargs}
        await self._socket.send_json(message)
        response = await self._socket.recv_json()

        if response.get("error"):
            raise RuntimeError(response["error"])

        return response

    async def connect_to_peer(self, address: str) -> Dict[str, Any]:
        """Connect to a peer.

        Args:
            address: Peer address to connect to

        Returns:
            Dict[str, Any]: Connection response
        """
        return await self._send_command("connect", address=address)

    async def broadcast_message(self, message: str) -> Dict[str, Any]:
        """Broadcast a message to all peers.

        Args:
            message: Message to broadcast

        Returns:
            Dict[str, Any]: Broadcast response
        """
        return await self._send_command("broadcast", message=message)

    async def get_node_address(self) -> str:
        """Get this node's address.

        Returns:
            str: Node address
        """
        response = await self._send_command("address")
        return response["address"]

    async def get_peers(self) -> Dict[str, Any]:
        """Get list of connected peers.

        Returns:
            Dict[str, Any]: Peer information
        """
        return await self._send_command("peers")


async def main():
    """Example usage of NADOOMeshLinkClient."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Create and connect client
    client = NADOOMeshLinkClient()
    await client.connect()

    try:
        # Get our node address
        node_addr = await client.get_node_address()
        print(f"Our node address: {node_addr}")

        # Example: Connect to a peer
        peer_addr = input("Enter peer address to connect (or press enter to skip): ")
        if peer_addr:
            result = await client.connect_to_peer(peer_addr)
            print(f"Connection result: {result}")

        # Example: Send messages
        while True:
            message = input("Enter message to broadcast (or Ctrl+C to exit): ")
            result = await client.broadcast_message(message)
            print(f"Broadcast result: {result}")

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
