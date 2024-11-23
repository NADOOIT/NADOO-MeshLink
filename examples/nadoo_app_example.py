"""Example NADOO Framework application using MeshLink service."""
import asyncio
import logging
from typing import Optional

from nadoo_framework import App
from nadoo_meshlink import MeshLinkService

logger = logging.getLogger(__name__)


class MeshLinkApp(App):
    """Example app using MeshLink service."""

    def __init__(self):
        """Initialize the app."""
        super().__init__("meshlink-example")
        self._meshlink: Optional[MeshLinkService] = None

    async def setup(self) -> None:
        """Set up the app."""
        # Get MeshLink service
        self._meshlink = self.get_service("meshlink")
        if not self._meshlink:
            raise RuntimeError("MeshLink service not found")

    async def run(self) -> None:
        """Run the app."""
        if not self._meshlink:
            raise RuntimeError("App not properly set up")

        # Get our node address
        node_addr = await self._meshlink.get_node_address()
        logger.info(f"Our node address: {node_addr}")

        # Example: Connect to a peer
        peer_addr = input("Enter peer address to connect (or press enter to skip): ")
        if peer_addr:
            result = await self._meshlink.connect_to_peer(peer_addr)
            logger.info(f"Connection result: {result}")

        # Example: Send messages
        try:
            while True:
                message = input("Enter message to broadcast (or Ctrl+C to exit): ")
                result = await self._meshlink.broadcast_message(message)
                logger.info(f"Broadcast result: {result}")
                await asyncio.sleep(0.1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")


async def main():
    """Run the example app."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and run app
    app = MeshLinkApp()
    try:
        await app.start()
        await app.run()
    except Exception as e:
        logger.error(f"Error running app: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
