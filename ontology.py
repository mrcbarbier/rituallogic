# -*- coding: utf-8 -*-

from classes import Atom
from utilityclasses import DatabaseHandler


class Ontology(object):
    """Stores permanent relations between objects of the same type.

    Attributes:
        typ (class): type of objects in the ontology.
        edges (dict of dicts):
            edges[i][j] is a list of relations between i and j.

    Relations are identified strings, and they are directed by default.
    The unique relation type "IN" defines a parent-child relationship
    between objects, e.g. every part of an object is "IN" that object,
    which is their parent.
    """

    def __init__(self,typ):
        self.typ=typ
        self.edges={}

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
        """Returns all object uids in an "IN" relationship with the initial uid.
        If recursive, adds all further ancestors as well."""
        parents=set([])
        edges=self.get_edges(uid)
        for j in edges:
            if "IN" in edges[j]:
                parents.add(j)
                if recursive:
                    parents.union(self.get_parents(j))
        return parents


class QueryHandler(object):

    def query(self,sequence,exp):
        """Returns"""
        return 1

    def get_state(self,sequence,frame):
        """Given a sequence and a frame (object, identifier or number),
        """