# -*- coding: utf-8 -*-


class OntologyRuleset(object):
    """Set of inference rules about an Ontology (see below).
    Lists which types of edges in the ontology allow to infer
    certain properties on elements, for example which
    edge types imply inheritance of atoms between nodes."""


    rule_types={}

    def __init__(self):
        self.rules=[rule for typ in self.rule_types for rule in self.rule_types[typ] ]


class DefaultOntologyRuleset(OntologyRuleset):
    """Default Ruleset for ontology inference."""


    rule_types={
    'existential':[  #RULES ABOUT HOW AN ELEMENT MAY BE DEFINED FROM ANOTHER
        'is',  # An element is an instance of another (if mutual, equivalence class)
        'inherit',  # An element inherits all links from another
        ],
    'combination':[  #RULES ABOUT HOW ELEMENT MAY COMBINE
        'replace', #When an element is meant to override another
        'block', #When an element is meant to prevent another from being
        ]
    }


    def get_types(self,rule):
        """Return list of edge types compatible with a certain rule"""
    #e.g. the unique relation type "IN" defines a parent-child relationship
    #between objects, e.g. every part of an object is "IN" that object,
    #which is their parent."""
        #if rule == 'parent':
            #return ('in',)
        types=()
        if not rule in self.rules:
            return types
        if rule =='is':
            types= ('equal','translation','variant')
        elif rule =='inherit':
            types= ('is',)
        elif rule == 'replace':
            types= ('antonym',)
        elif rule =='location':
            types= ('at','in','on','near','direction')
        return (rule,)+tuple(r for t in types  for r in self.get_types(t))


    def inner_relation(self,attr=[]):
        '''Relations between members of the same category (i.e. elements
        inheriting from the same element) given that category has attributes attr'''

        relations=[]
        if 'exclusive' in attr:
            relations.append('exclude')
        return relations




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
        self.edge={} #dictionary of dictionaries
        self.node={} #dictionary of node attributes
        self.nodes=[] #list
        self.edges=[] #list
        self.skeleton={} #dictionary of sets (existence of edges, undirected and unlabelled)

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


    def add(self,i,attr=None):
        '''Add node with uid i and possibly attributes.'''
        if i in self.nodes:
            return
        self.edge.setdefault(i,{})
        self.node.setdefault(i,[])
        if not attr is None:
            if isinstance(attr,basestring):
                self.node[i].append(attr)
            else:
                self.node[i]+=list(attr)
        self.nodes.append(i)

    def add_node(self,i,*args,**kwargs):
        '''Alias of add.'''
        return self.add(i,*args,**kwargs)

    def add_edge(self,i,j,e='is',reciprocal=False):
        """Add edge of type e between i and j. Directed unless reciprocal==True."""
        if not (i,j,e) in self.edges:
            self.edge.setdefault(i,{}).setdefault(j,[])
            self.edge[i][j]+=[e]
            self.edges.append((i,j,e))
            self.skeleton.setdefault(i,set([])).add(j)
            self.skeleton.setdefault(j,set([])).add(i)
        if reciprocal:
            self.add_edge(j,i,e)


    def rem_edge(self,i,j,e,reciprocal=True):
        """Removes all edges of type e between i and j, and also between
        j and i unless reciprocal==False."""
        if i in self.edge and j in self.edge[i]:
            [self.edge[i][j].remove(edge) for edge in self.edge[i][j] if edge==e]
            while (i,j,e) in self.edges:
                self.edges.remove((i,j,e))
            if not self.edge[i][j] and not self.edge.get(j,{}).get(i,None):
                if j in self.skeleton[i]:
                    self.skeleton[i].remove(j)
                if i in self.skeleton[j]:
                    self.skeleton[j].remove(i)
        if reciprocal:
            self.rem_edge(j,i,e,reciprocal=False)


    def get_edges(self,uid1,uid2=None):
        """Get all edges for one element or between two elements"""
        if uid2 is None:
            return self.edge.setdefault(uid1,{})
        else:
            return self.get_edges(uid1).get(uid2,[])

    def nei(self,uid,relation=None):
        '''Find all neighbors of uid (that have a given relation, if specified).'''
        for i in self.edge.get(uid,{}):
            for etype in self.edge[uid][i]:
                if relation is None or relation==etype:
                    yield i

    def paths(self,src,tgt,directed=0,relations=None,maxlen=None):
        '''Find all paths between src and tgt, possibly specifying:
            directed paths only
            set of acceptable relations
            maximum length of path
        NB: Simple depth-first algorithm'''

        if directed:
            graph=self.edge
        else:
            graph=self.skeleton
        if not src in graph or not tgt in graph:
            return []
        #paths=self._all_simple_paths_graph(self.skeleton,uid1,uid2)


        if maxlen is None:
            maxlen = len(self.nodes)-1
        paths=[]
        visited=[src] #current path
        neis=[ list(graph[src]) ] #neighbors that remain to visit at current step and previous
        while neis:
            pocket=neis[-1]
            if (not pocket) or len(visited)>=maxlen:
                neis.pop()
                visited.pop()
            else:
                nxt=pocket.pop()
                if not relations is None:
                    #Skip if bad relation types
                    rels=self.get_edges(visited[-1],nxt)
                    if not directed:
                        rels+=self.get_edges(nxt,visited[-1])
                    if not set(relations).intersection(rels):
                        continue
                if nxt==tgt:
                    #Stop at this depth
                    paths.append(visited+[tgt] )
                elif not nxt in visited:
                    #Go deeper
                    visited.append(nxt)
                    neis.append(list(graph[nxt]))
        return paths

class Database(Ontology):
    """Ontology that stores objects in addition to UIDs
    and links toward instances of its objects."""

    def __init__(self,typ,**kwargs):
        Ontology.__init__(self,typ,**kwargs)
        self.instances={}
        self.object={}

    def add(self,obj,*args,**kwargs):
        if not hasattr(obj,'uid'):
            return Ontology.add(self,obj,*args,**kwargs)
        uid=obj.uid
        self.object[uid]=obj
        return Ontology.add(self,uid,*args,**kwargs)

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
    """Allows intelligent querying of a database using a ruleset for inference.

    Attributes:
        database (Ontology):
        rule (OntologyRuleset): Set of logical, spatial, etc. rules that allow
            inference on the database.
        relation_db (Ontology): Optional, distinct database for relations between
            (atoms representing) relation types.

        ."""


    def __init__(self,database,rule=None,relation_db=None):
        self.database=database
        if rule is None:
            rule=DefaultOntologyRuleset()
        self.rule=rule
        if relation_db is None:
            #Relations between relations are assumed to be stored in the same db
            self.relation_db=self.database
        else:
            #Relatiosn between relations are stored externally
            self.relation_db=relation_db

    def filter(self,text,field='any',rule='strict'):
        """filter"""
        edges=list(self.database.edges)

        return edges

    def get_neighbors(self,uid,relation=None,strict=True,is_relation=False):
        '''Find neighbors to element with given uid, filtered by relation type
            (if provided) either strictly or allowing for equivalences.
            If element is itself a relation type, search relation_db instead.'''
        if not is_relation:
            dbs=self.database
        else:
            dbs=self.relation_db
        if strict:
            '''Find only neighbors with specified relation'''
            return dbs.get_nei(uid,relation)
        else:
            '''Find neighbors with equivalent relation'''
            #If relation is a primary relation type of the ontology ruleset (e.g. exclude)
            types=self.rule.get_types(relation,is_relation=True)
            if not types:
                types=self.get_equivalents(relation)
            neis=[]
            for t in types:
                neis+=self.get_neighbors(uid,t,strict=True,is_relation=is_relation)
            return neis

    def get_relations(self,uid1,uid2,strict=False,is_relation=False):
        '''Find all relations between uid1 and uid2, including indirect ones
        unless strict=True'''
        if not is_relation:
            dbs=self.database
        else:
            dbs=self.relation_db

        #Find all paths between the two nodes
        rule=self.rule
        inherit=set(rule.get_types('inherit'))
        paths=dbs.paths(uid1,uid2)
        relations=list(dbs.get_edges(uid1,uid2))
        for path in paths:
            cur=list(path)
            if len(cur)==2:
                continue
            #Via inheritance, reduce the path from both ends
            while len(cur)>=2 and inherit.intersection(dbs.get_edges(cur[0],cur[1]) ) :
                    cur=cur[1:]
            while len(cur)>=2 and inherit.intersection(dbs.get_edges(cur[-1],cur[-2]) ) :
                cur=cur[:-1]
            newrel=[]
            if len(cur)==2:
                #Relation between parent categories
                newrel=list(dbs.get_edges(uid1,uid2))
            elif len(cur)==1:
                #Relation between two tokens of the same category
                newrel=rule.inner_relation(dbs.node[cur[0]])
            relations+= newrel
            print 'QueryHandler.get_relations: reduced path between',uid1,uid2,cur, newrel
        return relations

    def get_equivalents(self, uid,is_relation=False):
        '''Find all atoms that are equivalent to a given atom.'''
        equi=[uid]+self.get_neighbors(uid,'is',strict=False, is_relation=is_relation)
        return equi


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