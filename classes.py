# -*- coding: utf-8 -*-

from parameters import *
from collections import OrderedDict
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
        uid=unicode(uid)
        if uid[0]=='-':
            uid=uid[1:]
        self.uid=uid

    def __repr__(self):
        return self.uid

    def __eq__(self,atom):
        if isinstance(atom,basestring):
            return self.uid==atom
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

    Any entity of the ritual that exists beyond a single time step and may
    undergo transformations or be put in relation with others over time,
    e.g. humans, materia, places, and relevant groupings or parts thereof."""

    def __init__(self,uid):
        self.uid=uid

class Relation(Atom):
    """Relation between nodes.
    Attributes:
        nodes (tuple): Identifiers of the nodes involved in the relation (ordered)
        atoms (list): Mutable collection of atoms characterizing the node.

    Relations are defined uniquely by the nodes they involve and by their atoms."""

    def __init__(self,nodes=[],atoms=[]):
        self.nodes=tuple(nodes)
        self.atoms=list(atoms)

    def __repr__(self):
        return str(self.nodes)

class AtomContainer(Atom):
    """Internal use only.
    Abstract superclass for objects characterized by a collection of atoms.

    Attributes:
        uid (string): Identifier.
        atoms (list): Mutable collection of atoms characterizing the object.
    """

    def __init__(self,uid,atoms=[]):
        self.uid=uid
        self.atoms=list(atoms)
    def add_atom(self,atom):
        self.atoms.append(atom)

    def rem_atom(self,atom):
        self.atoms.remove(atom)


class Action(AtomContainer):
    """Ritual action.

    Attributes:
        uid (string): Identifier.
        atoms (list): Mutable collection of atoms characterizing the action,
            e.g. adverb, semantic/symbolic content, annotations.
        roles (dict): Roles occupied by different nodes in the action.
            {Node: Keyword}
        states (dict): Assign new atoms to member nodes.
            {Node: list(Atom or AtomChange)}
        relations (list): Change relations between nodes

    Single change of the state and relationships of nodes.
    Can involve any number of nodes in different roles taken from the
    ACTION_KEYWORDS set.

    Action Templates are available elsewhere. For instance, the template
        light(Priest,Fire)
    takes these nodes as roles and also assigns the atom "lit" to Fire.
    """


    @property
    def children(self):
        return self.nodes

    @property
    def nodes(self):
        return set(self.roles.keys()).union( set(self.states.keys()) )

    def add_relation(self,relation):
        """Add relation"""
        self.relations.append(relation)

    def add_change(self,node,change):
        """Add either change or list of changes on node"""
        self.states.setdefault(node,[])
        try:
            self.states[node]+=change
        except:
            self.states.append(change)

    def __init__(self,uid,atoms=[],roles={},states={},relations=()):
        self.uid=uid
        self.atoms=list(atoms)
        self.roles=OrderedDict(roles)
        self.states=OrderedDict(states)
        self.relations=list(relations)


        #if not set(ACTION_KEYWORDS)>= set(roles.values()):
            ##Some of the roles have a role that is not listed in Parameters.
            #raise Exception('Action Keywords {} not permitted.'.format(
                    #sorted(set(roles)- set(ACTION_KEYWORDS)) )
                #)


class Frame(AtomContainer):
    """Collection of simultaneous actions, one time step in the ritual.

    Attributes:
        uid (string): Identifier.
        atoms (list): Mutable collection of atoms characterizing the frame.
        actions (list): Mutable collection of actions in the frame.

    (NB: 'Frame' as in single movie frame.)"""


    @property
    def children(self):
        return self.actions

    def __init__(self,uid,atoms=[],actions=[]):
        self.uid=uid
        self.atoms=list(atoms)
        self.actions=list(actions)

    @property
    def nodes(self):
        nodes=[]
        for a in self.actions:
            nodes+= a.roles.keys()
        return set(nodes)

    def add_action(self,action):
        """Adds an action to the frame"""
        self.actions.append(action)


    def new_action(self):
        act= Action('{}|action{}'.format(self.uid,len(self.actions) ) )
        self.add_action(act)
        return act

    def rem_action(self,action):
        if action in self.actions:
            self.actions.remove(action)
            return 1
        return 0

class Sequence(AtomContainer):

    """Sequence of frames.

    Attributes:
        uid (string): Identifier.
        atoms (list): Mutable collection of atoms characterizing the sequence.
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
            return self.frames[0].actions[0]
        return None

    def __init__(self,uid,atoms=[],frames=[],setup=None):
        self.uid=uid
        self.atoms=list(atoms)
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

    def new_frame(self):
        fr= Frame('{}|frame{}'.format(self.uid,len(self.frames) ) )
        self.add_frame(fr)
        return fr

    def rem_frame(self,frame):
        if frame in self.frames:
            self.frames.remove(frame)
            for node in frame.nodes:
                try:
                    self.nodes[node].remove(frame)
                except:
                    pass
            return 1
        return 0