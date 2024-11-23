# NADOO-MeshLink

A powerful P2P networking plugin for NADOO Framework applications, built with libp2p and ZeroMQ.

## Features

- **P2P Communication**: Direct peer-to-peer communication using libp2p
- **Topic-based Pub/Sub**: Advanced publish/subscribe messaging system
- **Network Management**: Comprehensive peer and network statistics
- **Framework Integration**: Seamless integration with NADOO Framework
- **Cross-Language**: Go backend with Python interface
- **Async Support**: Full async/await support in Python

## Installation

```bash
poetry add git+https://github.com/NADOOITChristophBa/NADOO-MeshLink.git
```

## Quick Installation

One-command installation (macOS):
```bash
curl -sSL https://raw.githubusercontent.com/NADOOITChristophBa/NADOO-MeshLink/main/setup.sh | bash
```

This will automatically:
1. Install required dependencies (Go, Poetry, ZeroMQ)
2. Build the Go binary
3. Install the Python package
4. Set up the development environment

For manual installation or other operating systems, see [Manual Installation](#manual-installation).

## Quick Start

```python
from nadoo_framework import App

async def main():
    # Create NADOO app
    app = App("your-app-name")
    
    # Get MeshLink service
    meshlink = app.get_service("meshlink")
    
    # Start the app
    await app.start()
    
    # Connect to a peer
    await meshlink.connect_to_peer(peer_addr)
    
    # Send a broadcast message
    await meshlink.broadcast_message("Hello P2P World!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Advanced Features

### Topic-based Messaging

```python
# Join a topic
await meshlink.join_topic("my-topic")

# Publish to topic
await meshlink.publish_to_topic("my-topic", "Hello Topic!")
```

### Network Management

```python
# Get network statistics
stats = await meshlink.get_network_stats()
print(f"Connected Peers: {stats['connected_peers']}")

# Get detailed peer information
peers = await meshlink.get_peers()
for peer in peers:
    print(f"Peer ID: {peer['id']}")
    print(f"Latency: {peer['latency']}")
```

### Peer Management

```python
# Connect to peer
await meshlink.connect_to_peer(peer_addr)

# Disconnect from peer
await meshlink.disconnect_peer(peer_id)
```

## Architecture

NADOO-MeshLink uses a hybrid architecture:

1. **Go Backend**: 
   - libp2p for P2P networking
   - Efficient peer discovery and routing
   - Built-in security features

2. **Python Frontend**:
   - Async service implementation
   - NADOO Framework integration
   - Simple, intuitive API

3. **ZeroMQ Bridge**:
   - Fast inter-process communication
   - Language-agnostic messaging
   - Reliable message delivery

## Examples

Check out the `examples` directory for:

- Basic peer-to-peer communication
- Topic-based messaging system
- Network monitoring and statistics
- Complete chat application example

## Development

Requirements:
- Python 3.8+
- Go 1.16+
- Poetry for dependency management

Setup development environment:

```bash
# Clone repository
git clone https://github.com/NADOOITChristophBa/NADOO-MeshLink.git
cd NADOO-MeshLink

# Install dependencies
poetry install

# Run tests
poetry run pytest
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Security

NADOO-MeshLink inherits security features from libp2p:

- TLS-based security
- Peer authentication
- Message encryption
- DoS protection

## Troubleshooting

Common issues and solutions:

1. **Connection Issues**:
   - Ensure peer addresses are correct
   - Check firewall settings
   - Verify network connectivity

2. **Performance Issues**:
   - Monitor network statistics
   - Reduce message frequency if needed
   - Check system resources

## Roadmap

Future improvements:

1. Enhanced peer discovery
2. Advanced security features
3. More message patterns
4. Performance optimizations
5. Additional protocol support

## Contact

- GitHub: [@NADOOITChristophBa](https://github.com/NADOOITChristophBa)
- Project Link: [https://github.com/NADOOITChristophBa/NADOO-MeshLink](https://github.com/NADOOITChristophBa/NADOO-MeshLink)
