package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/libp2p/go-libp2p-core/protocol"
	pubsub "github.com/libp2p/go-libp2p-pubsub"
	"github.com/multiformats/go-multiaddr"
	zmq "github.com/pebbe/zmq4"
)

const (
	textProtocolID = "/nadoomeshlink/text/1.0.0"
	zmqPort       = "5555"
)

type Message struct {
	Type    string      `json:"type"`
	Payload interface{} `json:"payload"`
}

type Response struct {
	Success bool        `json:"success"`
	Error   string     `json:"error,omitempty"`
	Address string     `json:"address,omitempty"`
	Data    interface{} `json:"data,omitempty"`
}

type PeerInfo struct {
	ID        string   `json:"id"`
	Addresses []string `json:"addresses"`
	Protocols []string `json:"protocols"`
	Latency   string   `json:"latency"`
}

type NetworkStats struct {
	ConnectedPeers int      `json:"connected_peers"`
	Bandwidth      int64    `json:"bandwidth"`
	PeerList       []string `json:"peer_list"`
}

type MeshNode struct {
	host    libp2p.Host
	pubsub  *pubsub.PubSub
	topics  map[string]*pubsub.Topic
	subs    map[string]*pubsub.Subscription
	mutex   sync.RWMutex
	socket  *zmq.Socket
}

func newMeshNode(socket *zmq.Socket) (*MeshNode, error) {
	// Create libp2p node
	host, err := libp2p.New(
		libp2p.ListenAddrStrings("/ip4/0.0.0.0/tcp/0"),
		libp2p.EnableAutoRelay(),
		libp2p.EnableNATService(),
	)
	if err != nil {
		return nil, err
	}

	// Create pubsub
	ps, err := pubsub.NewGossipSub(context.Background(), host)
	if err != nil {
		host.Close()
		return nil, err
	}

	return &MeshNode{
		host:    host,
		pubsub:  ps,
		topics:  make(map[string]*pubsub.Topic),
		subs:    make(map[string]*pubsub.Subscription),
		socket:  socket,
	}, nil
}

func (n *MeshNode) handleZMQMessages() {
	for {
		msg, err := n.socket.RecvBytes(0)
		if err != nil {
			fmt.Printf("Error receiving ZMQ message: %v\n", err)
			continue
		}

		var message Message
		if err := json.Unmarshal(msg, &message); err != nil {
			sendResponse(n.socket, Response{Success: false, Error: "Invalid message format"})
			continue
		}

		switch message.Type {
		case "connect":
			if addr, ok := message.Payload.(string); ok {
				err := n.connectToPeer(addr)
				if err != nil {
					sendResponse(n.socket, Response{Success: false, Error: err.Error()})
				} else {
					sendResponse(n.socket, Response{Success: true})
				}
			} else {
				sendResponse(n.socket, Response{Success: false, Error: "Invalid peer address"})
			}

		case "broadcast":
			if data, ok := message.Payload.(string); ok {
				n.broadcastMessage(data)
				sendResponse(n.socket, Response{Success: true})
			} else {
				sendResponse(n.socket, Response{Success: false, Error: "Invalid message format"})
			}

		case "get_address":
			addr := n.host.Addrs()[0].String() + "/p2p/" + n.host.ID().Pretty()
			sendResponse(n.socket, Response{Success: true, Address: addr})

		case "join_topic":
			if topic, ok := message.Payload.(string); ok {
				err := n.joinTopic(topic)
				if err != nil {
					sendResponse(n.socket, Response{Success: false, Error: err.Error()})
				} else {
					sendResponse(n.socket, Response{Success: true})
				}
			} else {
				sendResponse(n.socket, Response{Success: false, Error: "Invalid topic name"})
			}

		case "publish_to_topic":
			if payload, ok := message.Payload.(map[string]interface{}); ok {
				topic := payload["topic"].(string)
				data := payload["data"].(string)
				err := n.publishToTopic(topic, data)
				if err != nil {
					sendResponse(n.socket, Response{Success: false, Error: err.Error()})
				} else {
					sendResponse(n.socket, Response{Success: true})
				}
			} else {
				sendResponse(n.socket, Response{Success: false, Error: "Invalid topic message format"})
			}

		case "get_peers":
			peers := n.getPeerList()
			sendResponse(n.socket, Response{Success: true, Data: peers})

		case "get_network_stats":
			stats := n.getNetworkStats()
			sendResponse(n.socket, Response{Success: true, Data: stats})

		case "disconnect_peer":
			if peerID, ok := message.Payload.(string); ok {
				err := n.disconnectPeer(peerID)
				if err != nil {
					sendResponse(n.socket, Response{Success: false, Error: err.Error()})
				} else {
					sendResponse(n.socket, Response{Success: true})
				}
			} else {
				sendResponse(n.socket, Response{Success: false, Error: "Invalid peer ID"})
			}

		default:
			sendResponse(n.socket, Response{Success: false, Error: "Unknown message type"})
		}
	}
}

func (n *MeshNode) joinTopic(topic string) error {
	n.mutex.Lock()
	defer n.mutex.Unlock()

	if _, exists := n.topics[topic]; exists {
		return nil
	}

	t, err := n.pubsub.Join(topic)
	if err != nil {
		return fmt.Errorf("failed to join topic: %v", err)
	}

	sub, err := t.Subscribe()
	if err != nil {
		return fmt.Errorf("failed to subscribe to topic: %v", err)
	}

	n.topics[topic] = t
	n.subs[topic] = sub

	// Start listening for messages
	go n.handleTopicMessages(topic, sub)

	return nil
}

func (n *MeshNode) handleTopicMessages(topic string, sub *pubsub.Subscription) {
	for {
		msg, err := sub.Next(context.Background())
		if err != nil {
			fmt.Printf("Error receiving message from topic %s: %v\n", topic, err)
			continue
		}

		// Skip messages from ourselves
		if msg.ReceivedFrom == n.host.ID() {
			continue
		}

		fmt.Printf("Received message on topic %s from %s: %s\n", topic, msg.ReceivedFrom, string(msg.Data))
	}
}

func (n *MeshNode) publishToTopic(topic string, data string) error {
	n.mutex.RLock()
	t, exists := n.topics[topic]
	n.mutex.RUnlock()

	if !exists {
		return fmt.Errorf("not subscribed to topic: %s", topic)
	}

	return t.Publish(context.Background(), []byte(data))
}

func (n *MeshNode) getPeerList() []PeerInfo {
	var peerList []PeerInfo
	for _, p := range n.host.Network().Peers() {
		info := PeerInfo{
			ID:        p.Pretty(),
			Addresses: make([]string, 0),
			Protocols: make([]string, 0),
		}

		// Get peer addresses
		if addrs := n.host.Network().Peerstore().Addrs(p); len(addrs) > 0 {
			for _, addr := range addrs {
				info.Addresses = append(info.Addresses, addr.String())
			}
		}

		// Get supported protocols
		if protos, err := n.host.Peerstore().GetProtocols(p); err == nil {
			info.Protocols = make([]string, len(protos))
			copy(info.Protocols, protos)
		}

		// Get latency
		if lat := n.host.Network().Latency(p); lat > 0 {
			info.Latency = lat.String()
		}

		peerList = append(peerList, info)
	}
	return peerList
}

func (n *MeshNode) getNetworkStats() NetworkStats {
	peers := n.host.Network().Peers()
	stats := NetworkStats{
		ConnectedPeers: len(peers),
		PeerList:       make([]string, len(peers)),
	}

	for i, p := range peers {
		stats.PeerList[i] = p.Pretty()
	}

	return stats
}

func (n *MeshNode) disconnectPeer(peerID string) error {
	pid, err := peer.Decode(peerID)
	if err != nil {
		return fmt.Errorf("invalid peer ID: %v", err)
	}

	return n.host.Network().ClosePeer(pid)
}

func (n *MeshNode) connectToPeer(peerAddr string) error {
	maddr, err := multiaddr.NewMultiaddr(peerAddr)
	if err != nil {
		return fmt.Errorf("invalid peer address: %v", err)
	}

	peerInfo, err := peer.AddrInfoFromP2pAddr(maddr)
	if err != nil {
		return fmt.Errorf("invalid peer info: %v", err)
	}

	if err := n.host.Connect(context.Background(), *peerInfo); err != nil {
		return fmt.Errorf("connection failed: %v", err)
	}

	return nil
}

func (n *MeshNode) broadcastMessage(message string) {
	for _, peer := range n.host.Network().Peers() {
		stream, err := n.host.NewStream(context.Background(), peer, protocol.ID(textProtocolID))
		if err != nil {
			continue
		}
		rw := bufio.NewReadWriter(bufio.NewReader(stream), bufio.NewWriter(stream))
		rw.WriteString(message + "\n")
		rw.Flush()
	}
}

func sendResponse(socket *zmq.Socket, response Response) {
	responseBytes, err := json.Marshal(response)
	if err != nil {
		fmt.Printf("Error marshaling response: %v\n", err)
		return
	}
	
	if err := socket.SendBytes(responseBytes, 0); err != nil {
		fmt.Printf("Error sending response: %v\n", err)
	}
}

func main() {
	// Create ZMQ context and socket
	socket, err := zmq.NewSocket(zmq.REP)
	if err != nil {
		panic(err)
	}
	defer socket.Close()

	if err := socket.Bind("tcp://*:" + zmqPort); err != nil {
		panic(err)
	}

	// Create mesh node
	node, err := newMeshNode(socket)
	if err != nil {
		panic(err)
	}

	// Set stream handler
	node.host.SetStreamHandler(protocol.ID(textProtocolID), func(stream network.Stream) {
		rw := bufio.NewReadWriter(bufio.NewReader(stream), bufio.NewWriter(stream))
		go func() {
			for {
				str, err := rw.ReadString('\n')
				if err != nil {
					return
				}
				if str != "\n" {
					fmt.Printf("Received: %s", str)
				}
			}
		}()
	})

	// Output node address for debugging
	fmt.Println("Node address:", node.host.Addrs()[0].String()+"/p2p/"+node.host.ID().Pretty())

	// Start ZMQ message handler
	go node.handleZMQMessages()

	// Wait for interrupt signal
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	<-ch
	fmt.Println("Shutting down...")
}
