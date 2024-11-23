"""Advanced example of NADOO-MeshLink capabilities."""
import asyncio
import logging
from typing import Dict, List, Optional

from nadoo_framework import App
from nadoo_meshlink import MeshLinkService

logger = logging.getLogger(__name__)


class AdvancedMeshLinkApp(App):
    """Example app demonstrating advanced MeshLink features."""

    def __init__(self):
        """Initialize the app."""
        super().__init__("advanced-meshlink-example")
        self._meshlink: Optional[MeshLinkService] = None
        self._active_topics: List[str] = []

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

        # Get our node info
        node_addr = await self._meshlink.get_node_address()
        logger.info(f"Our node address: {node_addr}")

        while True:
            try:
                # Show menu
                print("\nNADOO-MeshLink Advanced Example")
                print("1. Connect to peer")
                print("2. Join topic")
                print("3. Publish to topic")
                print("4. Broadcast message")
                print("5. Get network stats")
                print("6. List peers")
                print("7. Exit")

                choice = input("\nEnter choice (1-7): ")

                if choice == "1":
                    await self._connect_to_peer()
                elif choice == "2":
                    await self._join_topic()
                elif choice == "3":
                    await self._publish_to_topic()
                elif choice == "4":
                    await self._broadcast_message()
                elif choice == "5":
                    await self._show_network_stats()
                elif choice == "6":
                    await self._list_peers()
                elif choice == "7":
                    logger.info("Exiting...")
                    break
                else:
                    print("Invalid choice!")

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error: {e}")

            await asyncio.sleep(0.1)

    async def _connect_to_peer(self) -> None:
        """Connect to a peer."""
        peer_addr = input("Enter peer address: ")
        result = await self._meshlink.connect_to_peer(peer_addr)
        logger.info(f"Connection result: {result}")

    async def _join_topic(self) -> None:
        """Join a topic."""
        topic = input("Enter topic name: ")
        result = await self._meshlink.join_topic(topic)
        if result:
            self._active_topics.append(topic)
            logger.info(f"Joined topic: {topic}")

    async def _publish_to_topic(self) -> None:
        """Publish message to a topic."""
        if not self._active_topics:
            logger.warning("No active topics! Join a topic first.")
            return

        print("\nActive topics:")
        for i, topic in enumerate(self._active_topics, 1):
            print(f"{i}. {topic}")

        try:
            choice = int(input("\nSelect topic number: ")) - 1
            topic = self._active_topics[choice]
            message = input("Enter message: ")
            result = await self._meshlink.publish_to_topic(topic, message)
            logger.info(f"Publish result: {result}")
        except (ValueError, IndexError):
            logger.error("Invalid topic selection!")

    async def _broadcast_message(self) -> None:
        """Broadcast a message to all peers."""
        message = input("Enter message to broadcast: ")
        result = await self._meshlink.broadcast_message(message)
        logger.info(f"Broadcast result: {result}")

    async def _show_network_stats(self) -> None:
        """Show network statistics."""
        stats = await self._meshlink.get_network_stats()
        print("\nNetwork Statistics:")
        print(f"Connected Peers: {stats.get('connected_peers', 0)}")
        print(f"Bandwidth Usage: {stats.get('bandwidth_usage', 'N/A')}")
        print(f"Active Topics: {len(self._active_topics)}")

    async def _list_peers(self) -> None:
        """List connected peers."""
        peers = await self._meshlink.get_peers()
        if not peers:
            print("No connected peers")
            return

        print("\nConnected Peers:")
        for peer in peers:
            print(f"ID: {peer.get('id')}")
            print(f"Address: {peer.get('address')}")
            print(f"Latency: {peer.get('latency', 'N/A')}")
            print("-" * 40)


async def main():
    """Run the advanced example app."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create and run app
    app = AdvancedMeshLinkApp()
    try:
        await app.start()
        await app.run()
    except Exception as e:
        logger.error(f"Error running app: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    asyncio.run(main())
