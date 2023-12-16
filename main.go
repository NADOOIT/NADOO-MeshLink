package main

import (
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"net"

	"github.com/libp2p/go-libp2p"
	peerstore "github.com/libp2p/go-libp2p/core/peer"
	"github.com/libp2p/go-libp2p/p2p/protocol/ping"
	multiaddr "github.com/multiformats/go-multiaddr"
)

func getLocalIP() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	for _, address := range addrs {
		// Check the address type and if it is not a loopback, then display it
		if ipnet, ok := address.(*net.IPNet); ok && !ipnet.IP.IsLoopback() {
			if ipnet.IP.To4() != nil {
				return ipnet.IP.String()
			}
		}
	}

	return ""
}

func main() {
	localIP := getLocalIP()
	if localIP == "" {
		fmt.Println("Could not find a non-loopback IP address on your machine.")
		os.Exit(1)
	}
	fmt.Printf("Your local IP address: %s\n", localIP)
    // start a libp2p node that listens on a random local TCP port,
    // but without running the built-in ping protocol
    node, err := libp2p.New(
        libp2p.ListenAddrStrings("/ip4/" + localIP + "/tcp/0"),
        libp2p.Ping(false),
    )

    if err != nil {
        panic(err)
    }

    // configure our own ping protocol
    pingService := &ping.PingService{Host: node}
    node.SetStreamHandler(ping.ID, pingService.PingHandler)

    // print the node's PeerInfo in multiaddr format
    peerInfo := peerstore.AddrInfo{
        ID:    node.ID(),
        Addrs: node.Addrs(),
    }
    addrs, err := peerstore.AddrInfoToP2pAddrs(&peerInfo)
    if err != nil {
        panic(err)
    }
    fmt.Println("libp2p node address:", addrs[0])

    // if a remote peer has been passed on the command line, connect to it
    // and send it 5 ping messages, otherwise wait for a signal to stop
    if len(os.Args) > 1 {
        addr, err := multiaddr.NewMultiaddr(os.Args[1])
        if err != nil {
            panic(err)
        }
        peer, err := peerstore.AddrInfoFromP2pAddr(addr)
        if err != nil {
            panic(err)
        }
        if err := node.Connect(context.Background(), *peer); err != nil {
            panic(err)
        }
        fmt.Println("sending 5 ping messages to", addr)
        ch := pingService.Ping(context.Background(), peer.ID)
        for i := 0; i < 5; i++ {
            res := <-ch
            fmt.Println("pinged", addr, "in", res.RTT)
        }
    } else {
        // wait for a SIGINT or SIGTERM signal
        ch := make(chan os.Signal, 1)
        signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
        <-ch
        fmt.Println("Received signal, shutting down...")
    }

    // shut the node down
    if err := node.Close(); err != nil {
        panic(err)
    }
}