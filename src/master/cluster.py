from master.node import Node

class Cluster:
    def __init__(self, slave_list):
        self.nodes = []
        for slave in slave_list:
            node = Node(slave['IP'], slave['status'])
            self.nodes.append(node)
                            