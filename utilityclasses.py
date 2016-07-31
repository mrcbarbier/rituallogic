# -*- coding: utf-8 -*-
from ontology import *
from classes import *
import networkx as nx

#========================================================================#
# UTILITY CLASSES
#========================================================================#



class SequenceViewer(object):
    class FrameGraph(nx.DiGraph):
        uid=None

    def frame_by_frame(self,sequence):
        """Take a sequence and returns a list of FrameGraphs"""
        graphs=[]
        for frame in sequence.frames:
            if graphs:
                graph=graphs[-1].copy()
            else:
                graph=self.FrameGraph()
            graph.uid=frame.uid
            graphs.append(graph)
            for action in frame.actions:
                for node in action.nodes:
                    #print node.atoms
                    if not node.uid in graph.node:
                        graph.add_node(node.uid)
                for i,j in action.changes.iteritems():
                    graph.node[i.uid].setdefault('tags',[])
                    graph.node[i.uid]['tags']+=j
                for r in action.relations:
                    graph.add_edge(r.nodes[0],r.nodes[1],tags=list(r.atoms))
        #return
        return graphs

class DatabaseHandler(object):
    """Loads a database and allows to manipulate it."""
    database=None

    def __init__(self,filename=None):
        if filename:
            self.load_database(filename)


    def load_database(self,filename):
        """Set database from file."""
        self.database=self.open(filename)

class TextParser(object):

    def export(self,filename,sequence):
        """Export data to file"""
        return

    def parse(self,filename):
        """Import data from file"""
        from ontology import Database
        fin=open(filename,'r')
        self.atom_db=Database('atom')
        self.node_db=Database('node')
        self.notes={}

        text=''''''
        for l in fin:
            if not l.strip():
                continue
            text+=l.strip()+'$'

        objects={}
        structure=nx.DiGraph()
        current=[]

        obj_pattern='<(.*?)>'
        for obj_txt in re.findall(obj_pattern,text):
            lines=[l.replace(' ','') for l in obj_txt.split('$') if l]
            typ,sep,uid=lines[0].partition(':')
            content={}
            for l in lines[1:]:
                spl=l.partition(':')
                if spl[2]:
                    clean=re.split(',(?![\s\w]*\))',spl[2])
                    if ':' in spl[2]:
                        #print cline
                        clean={s.split(':')[0]:s.split(':')[1].split(',') for s in clean }
                    content[spl[0]]=clean
            if typ=='node':
                obj=self.parse_node(uid,content)
                objects[current[0]].setup.add_change(obj,[])
            elif typ=='relation':
                obj=self.parse_relation(uid,content)
                objects[current[0]].setup.add_relation(obj)
            elif typ=='action':
                uid='{}|{}'.format(current[1],uid)
                structure.add_edge(current[1],uid)
                current=current[:2]+[uid]
                obj=self.parse_action(uid,content)
                for n in obj.nodes:
                    objects[current[0]].setup.add_change(n,[])
                for r in obj.relations:
                    objects[current[0]].setup.add_relation(r)

            elif typ=='frame':
                uid='{}|{}'.format(current[0],uid)
                structure.add_edge(current[0],uid)
                current=current[:1]+[uid]
                obj=self.parse_frame(uid,content)
            elif typ=='sequence':
                structure.add_node(uid)
                current=[uid]
                obj=self.parse_sequence(uid,content)

            objects[uid]=obj
            notes=content.pop('note',None)
            if notes:
                self.notes[uid]=notes

            for a in obj.atoms:
                self.atom_db.add_instance(Atom(a),obj)
        main=[]
        for seq in structure.nodes():
            if structure.predecessors(seq):
                continue
            main.append(objects[seq])
            for frame in structure.successors(seq):
                objects[seq].add_frame(objects[frame])
                for action in structure.successors(frame):
                    objects[frame].add_action(objects[action])
            #print 'Setup',objects[seq].setup.relations,objects[seq].setup.changes
        #print self.atom_db.instances
        return main

    def parse_node(self,uid,content={}):
        if not uid in self.node_db:
            tags=content.pop('tags',())
            node= Node(uid,atoms=tags)
            self.node_db.add(node)
        else:
            node=self.node_db[uid]
            #node.atoms=list(set(node.atoms).union() )
        return node

    def parse_relation(self,uid,content={}):
        nodes=uid.replace('(','').replace(')','').split(',')
        for n in nodes:
            self.parse_node(n)
        return Relation(nodes,atoms=content.pop('tags',()))

    def parse_action(self,uid,content):
        tags,changes,relations=content.pop('tags',()),content.pop('state', () ),content.pop('relations',())
        #print relations
        return Action(uid, atoms=tags,
            changes={self.parse_node(i):changes[i] for i in changes},
            relations=[self.parse_relation(r,{'tags':relations[r]}) for r in relations],
            members={i:self.parse_node(j[0]) for i,j in content.iteritems()})

    def parse_frame(self,uid,content):
        tags=content.pop('tags',())
        return Frame(uid,atoms=tags)

    def parse_sequence(self,uid,content):
        tags=content.pop('tags',())
        setup=Action(uid+'|setup|setup')
        setup_frame=Frame(uid+'|setup',actions=[setup])
        return Sequence(uid,atoms=tags,frames=[setup_frame])


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
