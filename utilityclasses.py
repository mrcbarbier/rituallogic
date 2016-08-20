# -*- coding: utf-8 -*-
from ontology import *
from classes import *

#========================================================================#
# UTILITY CLASSES
#========================================================================#

class TextDatabase(object):
    typs=['text','comment']

    def __init__(self):
        self.db={}

    def add_id(self,uid):
        self.db.setdefault(uid,{})

    def get(self,uid,typ='text'):
        self.add_id(uid)
        return self.db[uid].get(typ,[])

    def set(self,uid,typ='text',val=''):
        self.add_id(uid)
        if isinstance(val,basestring):
            val=[val]
        self.db[uid][typ]=val

    def add(self,uid,typ='text',val=''):
        self.add_id(uid)
        self.db[uid].setdefault(typ,[])
        if isinstance(val,basestring):
            val=[val]
        self.db[uid][typ]+=val

    def __contains__(self,uid):
        return uid in self.db


class SequenceViewer(object):
    class FrameGraph(Ontology):
        uid=None

    def frame_by_frame(self,sequence):
        """Take a sequence and returns a list of FrameGraphs"""
        graphs=[]
        for frame in sequence.frames:
            if graphs:
                graph=graphs[-1].copy()
            else:
                graph=self.FrameGraph('node')
            graph.uid=frame.uid
            graphs.append(graph)
            for action in frame.actions:
                for node in action.nodes:
                    #print node.atoms
                    if not node.uid in graph.node:
                        graph.add_node(node.uid)
                for i,lst in action.changes.iteritems():
                    #if i.uid in graph.node and 'tags' in graph.node[i.uid]:
                        #print 'before',graph.node[i.uid]
                    for j in lst:
                        if '-' == j[0]:
                            j=j[1:]
                            if j in graph.node[i.uid]:
                                graph.node[i.uid].remove(j)
                        else:
                            if not j in graph.node[i.uid]:
                                graph.node[i.uid].append(j)
                    #if i.uid in graph.node and 'tags' in graph.node[i.uid]:
                        #print 'after',graph.node[i.uid]
                for r in action.relations:
                    for atom in r.atoms:
                        if '-' == atom[0]:
                            graph.rem_edge(r.nodes[0],r.nodes[1],atom[1:] )
                        else:
                            graph.add_edge(r.nodes[0],r.nodes[1],atom)
        #return
        return graphs

class IOHandler(object):

    def export(self,filename,sequences):
        """Export data to file"""
        txt=''''''
        for seq in sequences:
            tmp='''<sequence: {}\n'''.format(seq.uid)
            if seq.uid in self.text_db:
                tmp+='text: {}\n'.format(', '.join(self.text_db.get(seq.uid,'text') ))
            if seq.atoms:
                tmp+='tags: {}\n'.format(', '.join(seq.atoms) )
            tmp+='>\n\n'

            txt+=tmp
            for fr in seq.frames:
                if fr.uid.split('|')[-1]=='setup':
                    act=fr.actions[0]
                    tmp=''
                    for n in act.changes:
                        tmp+='<node: {}\ntags:{}>\n\n'.format(n.uid,
                            ', '.join(act.changes[n]))
                    for i in act.relations:
                        tmp+='<relation:({})\ntags:{}>\n\n'.format(
                            ','.join(i.nodes),
                            ','.join(i.atoms ) )
                    txt+=tmp
                    continue
                tmp='''<frame: {}\n'''.format(fr.uid.split('|')[-1] )
                if fr.uid in self.text_db:
                    tmp+='text: {}\n'.format(', '.join(self.text_db.get(fr.uid,'text')))
                if fr.atoms:
                    tmp+='tags: {}\n'.format(', '.join(fr.atoms) )
                tmp+='>\n\n'
                txt+=tmp
                for act in fr.actions:
                    tmp='''<action: {}\n'''.format(act.uid.split('|')[-1])
                    if act.uid in self.text_db:
                        tmp+='text: {}\n'.format(', '.join(self.text_db.get(act.uid,'text')))
                    if act.atoms:
                        tmp+='tags: {}\n'.format(', '.join(act.atoms) )
                    for m in act.members:
                        tmp+='{}:{}\n'.format(m,act.members[m])
                    if act.changes:
                        tmp+='nodes: {}\n'.format(', '.join(['{}:{}'.format(i,
                            ','.join(act.changes[i] ) )
                            for i in act.changes]   ))
                    if act.relations:
                        tmp+='relations: {}\n'.format(', '.join(['({}):({})'.format(
                            ','.join(i.nodes),
                            ','.join(i.atoms ) )
                            for i in act.relations]   ))
                    tmp+='>\n\n'
                    txt+=tmp

        fout=open(filename,'w')
        fout.write(txt)
        fout.close()

    def parse(self,filename):
        """Import data from file"""
        from ontology import Database
        fin=open(filename,'r')
        self.atom_db=Database('atom')
        self.node_db=Database('node')
        self.text_db=TextDatabase()

        text=''''''
        for l in fin:
            if not l.strip():
                continue
            text+=l.strip()+'$'

        objects={}
        #structure=nx.DiGraph()
        current=[]
        cur_obj=[]
        main=[]

        obj_pattern='<(.*?)>'
        for obj_txt in re.findall(obj_pattern,text):
            lines=[l for l in obj_txt.split('$') if l]
            lines = [l if 'text' in l else l.replace(' ','') for l in lines]
            typ,sep,uid=lines[0].partition(':')
            content={}
            for l in lines[1:]:
                spl=l.partition(':')
                if spl[2]:
                    clean=re.split(',(?![\s\w]*\))',spl[2])
                    if ':' in spl[2]:
                        #print cline
                        clean=OrderedDict([(s.split(':')[0].replace('(','').replace(')',''),
                            s.split(':')[1].replace('(','').replace(')','').split(','))
                             for s in clean ])
                    content[spl[0]]=clean
            if typ=='node':
                obj=self.parse_node(uid,content)
                objects[current[0]].setup.add_change(obj,content.get('tags',[]) )

            elif typ=='relation':
                obj=self.parse_relation(uid,content)
                objects[current[0]].setup.add_relation(obj)
                for a in obj.atoms:
                    self.node_db.add_edge(obj.nodes[0],obj.nodes[1],a)
            elif typ=='action':
                uid='{}|{}'.format(current[1],uid)
                #structure.add_edge(current[1],uid)
                current=current[:2]+[uid]
                obj=self.parse_action(uid,content)
                if len(cur_obj)==2:
                    cur_obj.append(obj)
                else:
                    cur_obj=cur_obj[:2]+[obj]
                cur_obj[1].add_action(obj)

                #Put all nodes that are never referenced before into setup action
                for n in obj.nodes:
                    objects[current[0]].setup.add_change(n,[])
                for r in obj.relations:
                    for nt in r.nodes:
                        n=self.node_db.get(nt,Node(nt))
                        objects[current[0]].setup.add_change(n,[])

            elif typ=='frame':
                uid='{}|{}'.format(current[0],uid)
                #structure.add_edge(current[0],uid)
                current=current[:1]+[uid]
                obj=self.parse_frame(uid,content)
                if len(cur_obj)==1:
                    cur_obj.append(obj)
                else:
                    cur_obj=cur_obj[:1]+[obj]
                cur_obj[0].add_frame(obj)
            elif typ=='sequence':
                #structure.add_node(uid)
                current=[uid]
                obj=self.parse_sequence(uid,content)
                cur_obj=[obj]
                main.append(obj)

            objects[uid]=obj
            notes=content.pop('note',[])+content.pop('text',[])
            if notes:
                n=notes.pop(0)
                self.text_db.set(uid,'text',n.strip())
                [self.text_db.add(uid,'comment',n.strip()) for n in notes]

            if typ in ('sequence','frame','action'):
                for a in obj.atoms:
                    self.atom_db.add_instance(Atom(a),obj)

        for seq in main:
            for fr in seq.frames:
                for act in fr.actions:
                    for node in act.changes:
                        for a in act.changes[node]:
                            self.atom_db.add_instance(Atom(a),(act,node) )
                    for rel in act.relations:
                        for a in rel.atoms:
                            self.atom_db.add_instance(Atom(a),(act,rel.nodes ) )

        return main

    def parse_node(self,uid,content={}):
        if not uid in self.node_db:
            #tags=content.pop('tags',())
            node= Node(uid)#,atoms=tags)
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
        tags,changes,relations=content.pop('tags',()),content.pop('nodes', ()
            ),content.pop('relations',())
        #print changes
        #print relations
        act= Action(uid, atoms=tags,
            changes=OrderedDict([(self.parse_node(i),changes[i]) for i in changes]),
            relations=[self.parse_relation(r,{'tags':relations[r]}) for r in relations],
            members={i:self.parse_node(j[0]) for i,j in content.iteritems()})
        return act

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
