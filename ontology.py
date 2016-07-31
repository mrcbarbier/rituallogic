# -*- coding: utf-8 -*-

from classes import Atom
from utilityclasses import DatabaseHandler


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
        edges (dict of dicts):
            edges[i][j] is a list of relations between i and j.

    Relations are identified strings, and they are directed by default.
    """

    def __init__(self,typ,ruleset=None):
        self.typ=typ
        self.edges={}
        if ruleset is None:
            ruleset=DefaultOntologyRuleset()
        self.ruleset=ruleset

    def add(self,i):
        self.edges.setdefault(i,{})

    def add_edge(self,i,j,e,reciprocal=False):
        """Add edge of type e between i and j. Directed unless reciprocal==True."""
        self.edges.setdefault(i,{})[j]=[e]
        if reciprocal:
            self.add_edge(j,i,e)

    def rem_edge(self,i,j,e,reciprocal=True):
        """Removes all edges of type e between i and j, and also between
        j and i unless reciprocal==False."""
        if i in self.edges and j in self.edges[i]:
            [self.edges[i][j].remove(edge) for edge in self.edges[i][j] if edge==e]
        if reciprocal:
            self.rem_edge(j,i,e,reciprocal=False)



    def get_edges(self,uid):
        """"""
        return self.edges.setdefault(uid,{})

    def get_parents(self,uid,recursive=True):
        """Returns all object uids corresponding to parents of the given uid.
        If recursive, adds all further ancestors as well."""
        parent_types=set(self.ruleset.get_types('parent'))
        parents=set([])
        edges=self.get_edges(uid)
        for j in edges:
            if parent_types.intersection(edges[j]):
                parents.add(j)
                if recursive:
                    parents.union(self.get_parents(j))
        return parents


class Database(Ontology):
    """Ontology that stores real elements rather than UIDs
    and links toward instances of its elements."""

    def __init__(self,typ):
        self.typ=typ
        self.edges={}
        self.instances={}
        self.object={}

    def add(self,obj):
        uid=obj.uid
        self.object[uid]=obj
        self.edges.setdefault(uid,{})

    def add_instance(self,obj,location):
        self.instances.setdefault(obj.uid,set([])).add(location)
        self.add(obj)

    def __contains__(self,uid):
        return uid in self.object

    def __getitem__(self,uid):
        return self.object[uid]

class QueryHandler(object):

    def query(self,sequence,exp):
        """Returns"""
        return 1

    def get_state(self,sequence,frame):
        """Given a sequence and a frame (object, identifier or number),
        """