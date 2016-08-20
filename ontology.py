# -*- coding: utf-8 -*-

from classes import Atom


class OntologyRuleset(object):
    """Set of inference rules about an Ontology (see below).
    Lists which types of edges in the ontology allow to infer
    certain properties on elements, for example which
    edge types imply inheritance of atoms between nodes."""


class DefaultOntologyRuleset(OntologyRuleset):
    """Default Ruleset for ontology inference."""


    def get_types(self,rule):
        """Return list of edge types compatible with a certain rule
    The unique relation type "IN" defines a parent-child relationship
    between objects, e.g. every part of an object is "IN" that object,
    which is their parent."""
        if rule == 'parent':
            return ('in',)
        if rule == 'exclude':
            return ('antonym',)
        if rule =='equal':
            return ('is',)
        if rule =='location':
            return ('at','in','on','near')


class Ontology(object):
    """Stores permanent relations between objects of the same type.

    Attributes:
        typ (class): type of objects in the ontology.
        edge (dict of dicts):
            edge[i][j] is a list of relations between i and j.

    Relations are directed by default.
    """

    #(IDEA: if I relax constraint of objects of the same type,
    #elations are 2nd-order nodes that can themselves have relations
    #e.g. rel1=(Node1 near Node2), rel2=(rel1 in Sequence1) if rel1 exists only in Sequence1

    def __init__(self,typ,**kwargs):
        self.typ=typ
        self.edge={} #dictionary
        self.node={} #dictionary
        self.nodes=[] #ordered list
        self.edges=[] #ordered list

    def pairs(self):
        pairs=[]
        for i,j,e in self.edges:
            if not (i,j) in pairs:
                pairs.append((i,j))
        return pairs

    def copy(self):
        copy=self.__class__(self.typ)
        for n in self.nodes:
            copy.add(n)
            copy.node[n]=list(self.node[n])
        for i,j,e in self.edges:
            copy.add_edge(i,j,e)
        return copy


    def add(self,i):
        if i in self.nodes:
            return
        self.edge.setdefault(i,{})
        self.node.setdefault(i,[])
        self.nodes.append(i)

    def add_node(self,i):
        self.add(i)

    def add_edge(self,i,j,e='is',reciprocal=False):
        """Add edge of type e between i and j. Directed unless reciprocal==True."""
        if not (i,j,e) in self.edges:
            self.edge.setdefault(i,{}).setdefault(j,[])
            self.edge[i][j]+=[e]
            self.edges.append((i,j,e))
        if reciprocal:
            self.add_edge(j,i,e)

    def rem_edge(self,i,j,e,reciprocal=True):
        """Removes all edges of type e between i and j, and also between
        j and i unless reciprocal==False."""
        if i in self.edge and j in self.edge[i]:
            [self.edge[i][j].remove(edge) for edge in self.edge[i][j] if edge==e]
            while (i,j,e) in self.edges:
                self.edges.remove((i,j,e))
        if reciprocal:
            self.rem_edge(j,i,e,reciprocal=False)



    def get_edges(self,uid):
        """"""
        return self.edge.setdefault(uid,{})




class Database(Ontology):
    """Ontology that stores objects in addition to UIDs
    and links toward instances of its objects."""

    def __init__(self,typ,**kwargs):
        Ontology.__init__(self,typ,**kwargs)
        self.instances={}
        self.object={}

    def add(self,obj):
        if not hasattr(obj,'uid'):
            return Ontology.add(self,obj)
        uid=obj.uid
        self.object[uid]=obj
        return Ontology.add(self,uid)

    def add_edge(self,obj1,obj2,*args,**kwargs):
        if not hasattr(obj1,'uid'):
            u1=obj1
        else:
            u1=obj1.uid
        if not hasattr(obj2,'uid'):
            u2=obj2
        else:
            u2=obj2.uid
        self.add(obj1)
        self.add(obj2)
        return Ontology.add_edge(self,u1,u2,*args,**kwargs)

    def add_instance(self,obj,location):
        self.instances.setdefault(obj.uid,set([])).add(location)
        self.add(obj)

    def __contains__(self,uid):
        if not isinstance(uid,basestring):
            uid=uid.uid
        return uid in self.object

    def __getitem__(self,uid):
        return self.object[uid]

    def get(self,uid,default=None):
        if uid in self.object:
            return self.__getitem__(uid)
        else:
            return default


class QueryHandler(object):

    def __init__(self,data,ruleset=None):
        self.data=data
        if ruleset is None:
            ruleset=DefaultOntologyRuleset()
        self.ruleset=ruleset

    def filter(self,text,field='any',rule='strict'):
        """filter"""
        edges=list(self.data.edges)

        return edges



    def get_parents(self,db,uid,recursive=True):
        """Returns all object uids corresponding to parents of the given uid.
        If recursive, adds all further ancestors as well."""
        parent_types=set(self.ruleset.get_types('parent'))
        parents=set([])
        edges=db.get_edges(uid)
        for j in edges:
            if parent_types.intersection(edges[j]):
                parents.add(j)
                if recursive:
                    parents.union(self.get_parents(j))
        return parents