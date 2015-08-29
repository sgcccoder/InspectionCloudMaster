from master.node import Node

class Cluster:
    def __init__(self):
        self.nodes = []
        
    def getStatus(self):
        self.nodes = []
        f = open('D:\\cluster_status.txt')
        for line in f.readlines():
            str_list = line.split(' ')
            node = Node(str_list[0], str_list[1], str_list[2])
            self.nodes.append(node)
        return self.nodes
                            