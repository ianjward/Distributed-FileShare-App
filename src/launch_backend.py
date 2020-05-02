from twisted.internet import reactor
import src.network_node_types.broadcast_node as broadcast
import src


if __name__ == '__main__':
    broadcast.search_for(["ians_share"])
    reactor.run()

