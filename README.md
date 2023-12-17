![2182c2bc-44a0-422c-a9e1-ff37c9a79908](https://github.com/NADOOITChristophBa/DyP2PNM/assets/106314951/1a4a8ad6-1a5f-4ed6-9f0e-88918d5f6a04)

# NADOO MeshLink

## Introduction
NADOO MeshLink is an innovative broker process designed for advanced connectivity in decentralized Peer-to-Peer (P2P) networks. It leverages Go, libp2p, and ZeroMQ to facilitate versatile interactions across various programming languages and platforms.

## Core Functionality
- **Primary Role**: Serves as a dynamic broker, managing P2P network connectivity and inter-process communication.
- **Process Lifecycle**: Operates continuously, adapting to network changes and application requests.

## Key Features
1. **Dynamic P2P Communication**: Manages real-time communication within diverse P2P networks.
2. **Inter-Process Communication via ZeroMQ**: Offers language-agnostic communication between applications and the MeshLink broker.
3. **Local and Remote Function Execution**: Dynamically decides and routes function calls for local or remote execution.
4. **Service Management**: Dynamically manages local services, starting or stopping them as needed.
5. **Scalable Architecture**: Designed for scalability, handling numerous concurrent function calls and network nodes.
6. **Security and Privacy**: Ensures secure communication and data handling.

## Architecture
- **Broker Design**: MeshLink's architecture as a broker includes P2P connections and application message handling.
- **Interoperability**: ZeroMQ enables MeshLink to communicate with applications in various programming languages.
- **Flowchart**:
```mermaid
flowchart TB
    %% Nodes
    UA[User Application]
    MB[MeshLink Broker]
    FLT[Function Lookup Table]

    %% Flow
    UA -->|Function Call| MB
    MB -->|Check Function| FLT

    %% Local Execution
    subgraph LocalExecution
        direction TB
        LS{Local Service Running?}
        LFE[Execute Function Locally]
        LSM[Start Local Service]
        BIU[Background Install/Update]
    end

    %% Business Network
    subgraph BusinessNetwork
        direction TB
        BEN[Execute in Business Network]
        BPN[Business P2P Network]
    end

    %% Trusted Business Network
    subgraph TrustedBusinessesNetwork
        direction TB
        TBN[Execute in Trusted Business Network]
        TBP[Trusted Business P2P Network]
    end

    %% Global P2P Network
    subgraph GlobalP2PNetwork
        direction TB
        GPN[Execute in Global P2P Network]
        GP[Global P2P Network]
    end

    %% Local Function Flow
    FLT -- Local Function --> LS
    LS -- Yes --> LFE
    LS -- No --> LSM
    LSM --> BIU
    BIU --> LFE

    %% Remote Function Flow
    FLT -- Remote Function --> DEC{Determine Execution Context}
    DEC -->|Only Local| FNE[Function Not Executable]
    DEC -->|In Business Network| BEN
    DEC -->|Trusted Businesses| TBN
    DEC -->|Anyone| GPN

    %% Return Results
    LFE -->|Return Result| MB
    BPN -->|Return Result| MB
    TBP -->|Return Result| MB
    GP -->|Return Result| MB
    MB -->|Return Result| UA


## Technology Stack
- **Programming Language**: rimarily Go, with support for various languages via ZeroMQ.
- **Network Communication**: libp2p for P2P networking and ZeroMQ for inter-process communication.

## Architecture
- **Broker Design**: Details MeshLink's architecture as a broker, including handling of P2P connections and application messages.
- **Interoperability**: Explains how ZeroMQ enables MeshLink to interact with applications written in various programming languages.

## Installation and Setup
- **Installation Guide**: Steps for installing MeshLink.
- **Configuration Instructions**: Setting up MeshLink for different P2P networks and application environments.

## Contributing
Guidelines for contributing to the NADOO MeshLink project.

## License
AGPL-3.0 License.

## Acknowledgments
Thanks to contributors and supporters.

## Future Directions

#### Mobile Platform Support
- **Integration with iOS and Android**: Creating a Go library from MeshLink for native mobile applications.
- **Using Gomobile**: Building the library with Gomobile for Java/Kotlin (Android) and Swift/Objective-C (iOS) compatibility.
- **Native App Development**: Developing applications that integrate the MeshLink library for mobile P2P communication.
- **Considerations for Mobile**: Adhering to mobile OS limitations, App Store and Google Play Store policies, and optimizing for mobile device performance.

This initiative will expand MeshLink's capabilities to mobile platforms, making it a comprehensive cross-platform solution for decentralized network management.
