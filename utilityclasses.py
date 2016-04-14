# -*- coding: utf-8 -*-

#========================================================================#
# UTILITY CLASSES
#========================================================================#

class DatabaseHandler(object):
    """Loads a database and allows to manipulate it."""
    database=None

    def __init__(self,filename=None):
        if filename:
            self.load_database(filename)


    def load_database(self,filename):
        """Set database from file."""
        self.database=self.open(filename)



class GraphVisualization(object):
    """Loads a data structure and represents it as a graph."""

    def plot(self,graph):
        import networkx as nx,matplotlib.pyplot as plt
        g=nx.DiGraph()
        for i in graph.edges:
            edges=graph.edges[i]
            for j in edges:
                for e in edges[j]:
                    g.add_edge(i,j,name=e)



        pos=self.pos=nx.spring_layout(g)
        nx.draw_networkx_edges(g,pos=pos,edgelist=[(i,j) for i,j,d in
            g.edges_iter(data=True) if d['name']=='IN'],edge_color='g' )
        nx.draw_networkx_edges(self,pos=pos,edgelist=[(i,j) for i,j,d in
            g.edges_iter(data=True) if d['name']!='IN'],edge_color='k' )

        nx.draw_networkx_nodes(g,pos=pos  )
        nx.draw_networkx_labels(g,pos=pos,labels={n:str(n) for n in g.nodes() }  )

        edge_labels=dict([((u,v,),d['name'])
             for u,v,d in g.edges(data=True)])
        nx.draw_networkx_edge_labels(g,pos,edge_labels=edge_labels)

        #nx.draw(g)
        plt.show()