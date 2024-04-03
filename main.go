package main

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"github.com/libp2p/go-libp2p"
	"github.com/libp2p/go-libp2p-core/network"
	"github.com/libp2p/go-libp2p-core/peer"
	"github.com/multiformats/go-multiaddr"
)

const textProtocolID = "/nadoomeshlink/text/1.0.0"

func handleStream(stream network.Stream) {
    // Create a buffer stream for non blocking read and write.
    rw := bufio.NewReadWriter(bufio.NewReader(stream), bufio.NewWriter(stream))

    go readData(rw)
    go writeData(rw)

    // 'stream' will stay open until you close it (or the other side closes it).
}

func readData(rw *bufio.ReadWriter) {
    for {
        str, _ := rw.ReadString('\n')
        if str == "" {
            return
        }
        if str != "\n" {
            fmt.Printf("\x1b[32m%s\x1b[0m> ", str)
        }
    }
}

func writeData(rw *bufio.ReadWriter) {
    stdReader := bufio.NewReader(os.Stdin)

    for {
        fmt.Print("> ")
        sendData, _ := stdReader.ReadString('\n')
        rw.WriteString(fmt.Sprintf("%s\n", sendData))
        rw.Flush()
    }
}

func main() {
    // Create a new libp2p Host that listens on a random TCP port
    node, err := libp2p.New(libp2p.ListenAddrStrings("/ip4/0.0.0.0/tcp/0"))
    if err != nil {
        panic(err)
    }

    // Set a stream handler on the host
    node.SetStreamHandler(textProtocolID, handleStream)

    // Output the host's address
    fmt.Println("Your Multiaddress Is:", node.Addrs()[0].String()+"/p2p/"+node.ID().Pretty())

    // If a peer address is provided as the second argument, connect to it
    if len(os.Args) > 1 {
        peerAddr, _ := multiaddr.NewMultiaddr(os.Args[1])
        peerInfo, _ := peer.AddrInfoFromP2pAddr(peerAddr)

        if err := node.Connect(context.Background(), *peerInfo); err != nil {
            fmt.Println("Connection failed:", err)
        }

        // Open a stream to the destination peer
        stream, err := node.NewStream(context.Background(), peerInfo.ID, textProtocolID)
        if err != nil {
            panic(err)
        }

        rw := bufio.NewReadWriter(bufio.NewReader(stream), bufio.NewWriter(stream))

        go writeData(rw)
        go readData(rw)
    }

    // Wait for a SIGINT or SIGTERM signal
    ch := make(chan os.Signal, 1)
    signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
    <-ch
    fmt.Println("Shutting down...")
}
