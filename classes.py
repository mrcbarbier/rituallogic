# -*- coding: utf-8 -*-

from parameters import *

import re

#========================================================================#
# BASIC CLASSES FOR RITUAL DESCRIPTION
#========================================================================#


class Atom(object):
    """Atomic property.

    Attributes:
        uid (string): Identifier.
    """

    def __init__(self,uid):
        self.uid=str(uid)

    def __repr__(self):
        return self.uid

    def __eq__(self,atom):
        return self.uid==atom.uid

    def match(self,exp):
        """See if this atom matches a regular expression."""
        m=re.search(exp,self.uid)
        if m.group(0):
            return True
        return False

class AtomChange(object):
    """Regular expression for change in atomic property.

    Attributes:
        exp (string): Expression, e.g. "+standing", "-raw +cooked"
    """

    def __init__(self,exp):
        self.exp=exp
        parsed=exp.split(' ')
        self.add=[w.replace('+','').strip() for w in parsed if '+' in w]
        self.rem=[w.replace('-','').strip() for w in parsed if '-' in w]

    def __repr__(self):
        return self.exp

class Node(Atom):
    """Ritual component.

    Attributes:
        uid (string): Identifier.
        atoms (set): Mutable collection of atoms characterizing the node.

    Any entity of the ritual that exists beyond a single time step and may
    undergo transformations or be put in relation with others over time,
    e.g. humans, materia, places, and relevant groupings or parts thereof."""

    def __init__(self,uid,atoms=[]):
        self.uid=uid
        self.atoms=set(atoms)

    def add_atom(self,atom):
        self.atoms.add(atom)

    def rem_atom(self,atom):
        self.atoms.remove(atom)

    def apply_change(self,change):
        for atom in change.add:
            self.add_atom(atom)
        for atom in change.rem:
            self.rem_atom(atom)

class Relation(Atom):
    """Relation between nodes.
    Attributes:
        nodes (tuple): Identifiers of the nodes involved in the relation (ordered)
        atoms (set): Mutable collection of atoms characterizing the node.

    Relations are defined uniquely by the nodes they involve and by their atoms."""

    def __init__(self,nodes=[],atoms=[]):
        self.nodes=tuple(nodes)
        self.atoms=set(atoms)

    def __repr__(self):
        return str(self.nodes)

class Action(Node):
    """Ritual action.

    Attributes:
        uid (string): Identifier.
        atoms (set): Mutable collection of atoms characterizing the action,
            e.g. adverb, semantic/symbolic content, annotations.
        members (dict): Roles occupied by different nodes in the action.
            {Keyword: Node}
        changes (dict): Assign new atoms to member nodes.
            {Node: set(Atom or AtomChange)}
        relations (set): Change relations between nodes

    Single change of the state and relationships of nodes.
    Can involve any number of nodes in different roles taken from the
    ACTION_KEYWORDS set.

    Action Templates are available elsewhere. For instance, the template
        light(Priest,Fire)
    takes these nodes as members and also assigns the atom "lit" to Fire.
    """


    @property
    def children(self):
        return self.nodes

    @property
    def nodes(self):
        return set(self.members.values()).union( set(self.changes.keys()) )

    def add_relation(self,relation):
        """Add relation"""
        self.relations.add(relation)

    def add_change(self,node,change):
        """Add either change or list of changes on node"""
        self.changes.setdefault(node,[])
        try:
            self.changes[node]+=change
        except:
            self.changes.append(change)

    def __init__(self,uid,atoms=[],members={},changes={},relations=()):
        self.uid=uid
        self.atoms=set(atoms)
        self.members=dict(members)
        self.changes=dict(changes)
        self.relations=set(relations)


        if not set(ACTION_KEYWORDS)>= set(members):
            #Some of the members have a role that is not listed in Parameters.
            raise Exception('Action Keywords {} not permitted.'.format(
                    sorted(set(members)- set(ACTION_KEYWORDS)) )
                )


class Frame(Node):
    """Collection of simultaneous actions, one time step in the ritual.

    Attributes:
        uid (string): Identifier.
        atoms (set): Mutable collection of atoms characterizing the frame.
        actions (set): Mutable collection of actions in the frame.

    (NB: 'Frame' as in single movie frame_."""


    @property
    def children(self):
        return self.actions

    def __init__(self,uid,atoms=[],actions=[]):
        self.uid=uid
        self.atoms=set(atoms)
        self.actions=set(actions)

    @property
    def nodes(self):
        nodes=[]
        for a in self.actions:
            nodes+= a.members.values()
        return set(nodes)

    def add_action(self,action):
        """Adds an action to the frame"""
        self.actions.add(action)

class Sequence(Node):

    """Sequence of frames.

    Attributes:
        uid (string): Identifier.
        atoms (set): Mutable collection of atoms characterizing the sequence.
        frames (list): Temporal succession of frames.
        nodes (dict): Automatically generated list of nodes
        setup (Action): First action of the first frame.
    """


    @property
    def children(self):
        return self.frames

    @property
    def setup(self):
        """First action of the first frame, setting up the initial state"""
        if self.frames:
            return list(self.frames[0].actions)[0]
        return None

    def __init__(self,uid,atoms=[],frames=[],setup=None):
        self.uid=uid
        self.atoms=set(atoms)
        self.frames=list(frames)
        self.nodes={}
        self.set_frames(list(frames))

    def add_frame(self,frame, position=None):
        """Inserts a frame at given position, and records its nodes."""
        if frame in self.frames:
            return
        for node in frame.nodes:
            self.nodes.setdefault(node,[]).append(frame)
        if position ==None:
            self.frames.append(frame)
        else:
            self.frames.insert(position,frame)

    def set_frames(self,frames):
        """Replace current frames by given list."""
        self.clear_frames()
        for f in frames:
            self.add_frame(f)

    def clear_frames(self):
        """Empty all containers except atoms."""
        self.nodes.clear()
        self.frames[:]=[]

    def append(self,seq,uid=None):
        """Returns joint Sequence, with union on atoms."""
        if uid is None:
            uid='{}+{}'.format(self.uid,seq.uid)
        atoms=self.atoms.union(seq.atoms)
        frames=self.frames+seq.frames
        return Sequence(uid,atoms,frames)
