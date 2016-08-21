# -*- coding: utf-8 -*-

class GraphVisualization(object):
    """Loads a data structure and represents it as a graph."""

    def plot(self,graph,hold=0):
        import networkx as nx,matplotlib.pyplot as plt
        if not isinstance(graph, nx.DiGraph):
            g=nx.DiGraph()
            for i in graph.edge:
                edges=graph.edge[i]
                for j in edges:
                    for e in edges[j]:
                        g.add_edge(i,j,name=e)
        else:
            g=graph
        #print g.edges()

        plt.figure()
        pos=self.pos=nx.spring_layout(g)
        nx.draw_networkx_edges(g,pos=pos,edgelist=[(i,j) for i,j,d in
            g.edges_iter(data=True) if d.get('name',None)=='IN'],edge_color='g' )
        nx.draw_networkx_edges(g,pos=pos,edgelist=[(i,j) for i,j,d in
            g.edges_iter(data=True) if d.get('name',None)!='IN'],edge_color='k' )

        nx.draw_networkx_nodes(g,pos=pos  )
        nx.draw_networkx_labels(g,pos=pos,labels={n:str(n)+str(g.node[n].get(
            'tags','') ) for n in g.nodes() }  )

        edge_labels=dict([((u,v,),d.get('name',d.get('tags','')) )
             for u,v,d in g.edges(data=True)])
        nx.draw_networkx_edge_labels(g,pos,edge_labels=edge_labels)

        #nx.draw(g)
        if not hold:
            plt.show()
