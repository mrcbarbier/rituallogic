# -*- coding: utf-8 -*-
from ontology import *
from classes import *
from copy import deepcopy


def debug_caller_name(skip=2):
    """Get a name of a caller in the format module.class.method
    `skip` specifies how many levels of stack to skip while getting caller
    name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.
    An empty string is returned if skipped levels exceed stack height
    """
    import inspect
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
        return ''
    parentframe = stack[start][0]
    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
        # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        # be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>': # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)


class Path(str):
    #Strings that represent filesystem paths
    #When paths are added, gives a path
    #When a string is added, gives a string
    def __add__(self,x):
        import os
        if isinstance(x,Path):
            return Path(os.path.normpath(os.path.join(str(self),x)))
        return os.path.normpath(os.path.join(str(self),x))

    def norm(self):
        import os
        return Path(os.path.normpath(str(self)))

    def split(self):
        """"""
        import os
        lst=[]
        cur=os.path.split(self.norm())
        while cur[-1]!='':
            lst.insert(0,cur[-1])
            cur=os.path.split(cur[0])
        return lst

    def mkdir(self):
        """Make directories in path that don't exist"""
        import os
        cur=Path('./')
        for intdir in self.split():
            cur+=Path(intdir)
            if not os.path.isdir(cur):
                os.mkdir(cur)

    def curdir(self):
        import os
        return Path(os.path.split(self.norm())[0])

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
    '''Converter of Sequence into list of Databases (one per Frame) compiling
    incremental information from all Actions up to that point'''
    def __init__(self,atom_query):
        self.atom_query=atom_query

    class FrameGraph(Ontology):
        uid=None

    def frame_by_frame(self,sequence):
        """Take a sequence and returns a list of FrameGraphs (Ontologies)
        Uses QueryHandler on atom_db to perform simple inference on effect
        of changing states and relations.
        (NB: simple inference = no black magic such as restoring a previous tag
        when removing a tag that had replaced it)"""
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
                    if not node.uid in graph.node:
                        graph.add_node(node.uid)
                #STATES
                for i,lst in action.states.iteritems():
                    for j in lst:
                        if '-' == j[0]:
                            j=j[1:]
                            if j in graph.node[i.uid]:
                                graph.node[i.uid].remove(j)
                        else:
                            if '+' == j[0]:
                                j=j[1:]
                            if not j in graph.node[i.uid]:
                                graph.node[i.uid].append(j)

                            #Apply inference rules
                            for other in tuple(graph.node[i.uid]):
                                if other ==j:
                                    continue
                                if 'exclude' in self.atom_query.get_relations(j,other):
                                    graph.node[i.uid].remove(other)

                #RELATIONS
                for r in action.relations:
                    src,tgt=r.nodes
                    for atom in r.atoms:
                        if '-' == atom[0]:
                            graph.rem_edge(src,tgt,atom[1:] )
                        else:
                            if '+'==atom[0]:
                                atom=atom[1:]
                            graph.add_edge(src,tgt,atom)

                            #Apply inference rules
                            for other in tuple(graph.edge[src][tgt]):
                                if other==atom:
                                    continue
                                if 'exclude' in self.atom_query.get_relations(atom,other):
                                    graph.edge[src][tgt].remove(other)
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
                    for n in act.states:
                        tmp+='<node: {}\ntags:{}>\n\n'.format(n.uid,
                            ', '.join(act.states[n]))
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
                    #for m in act.roles:
                        #tmp+='{}:{}\n'.format(m,act.members[m])
                    if act.roles:
                        tmp+='roles: {}\n'.format(', '.join(['{}:({})'.format(i,
                            ','.join(act.roles[i] ) )
                            for i in act.roles]   ))
                    if act.states:
                        tmp+='states: {}\n'.format(', '.join(['{}:({})'.format(i,
                            ','.join(act.states[i] ) )
                            for i in act.states]   ))
                    if act.relations:
                        tmp+='relations: {}\n'.format(', '.join(['({}):({})'.format(
                            ','.join([unicode(z) for z in i.nodes]),
                            ','.join( i.atoms ) )
                            for i in act.relations]   ))
                    tmp+='>\n\n'
                    txt+=tmp

        fout=open(filename,'w')
        fout.write(txt)
        fout.close()

    def parse(self,filename,objects=None,contents=None):
        if objects is None:
            objects={}
        if contents is None:
            contents={}
        """Import data from file"""
        from ontology import Database
        fin=open(filename,'r')
        self.atom_db=Database('atom')
        self.node_db=Database('node')
        self.action_db=Database('action')
        self.sequence_db=Database('sequence')
        self.text_db=TextDatabase()

        text=''''''
        for l in fin:
            if not l.strip():
                continue
            text+=l.strip()+'$'

        current=[]
        cur_obj=[]
        main=[]

        obj_pattern='<(.*?)>'
        for obj_txt in re.findall(obj_pattern,text):
            lines=[l for l in obj_txt.split('$') if l]
            lines = [l if 'text' in l else l.replace(' ','') for l in lines]
            typ,sep,uids=lines[0].partition(':')
            uid,sep,inherit=[x.strip() for x in uids.partition('@')]
            ancestors=[a.strip() for a in inherit.split(',') if a.strip() ]

            #AUTOMATIC APPENDING OF UID
            idprefix=''
            if typ=='action':
                idprefix='{}|'.format(current[1])
                uid=idprefix+uid
                current=current[:2]+[uid]
            elif typ=='frame':
                idprefix='{}|'.format(current[0])
                uid=idprefix+uid
                current=current[:1]+[uid]
            elif typ=='sequence':
                uid=idprefix+uid
                current=[uid]


            content={}

            #INHERITANCE
            for ancestor in ancestors:
                nbpipes=len(ancestor.split('|'))
                ancid='|'.join(idprefix.split('|')[nbpipes:])+ancestor.strip()
                prevcontent=contents[ancid]
                content.update(deepcopy(prevcontent))
            if uid in contents: #If the same uid was already used previously, overwrite
                content.update(deepcopy(contents[uid]))
                #print content

            for l in lines[1:]:
                key,sep,val=l.partition(':')
                if val:
                    clean=re.split(',(?![\s\w,-_]*\))',val)
                    if ':' in val:
                        listmode=False
                        cleandict=OrderedDict()
                        for s in clean:
                            i,j = [x.replace('(','').replace(')','') for x in s.split(':')]
                            j=j.split(',')
                            if i in cleandict:
                                cleandict[i]+=j
                            else:
                                cleandict[i]=j
                        clean=cleandict
                    else:
                        listmode=True
                    if key[0]=='+':
                        key=key[1:]
                        if listmode:
                            content[key]+=clean
                        else:
                            for i in clean:
                                content[key].setdefault(i,[])
                                content[key][i]+=clean[i]

                    elif key[0]=='-':
                        key=key[1:]
                        for i in clean:
                            if listmode:
                                if i in content[key]:
                                    content[key].remove(i)
                            else:
                                content[key].setdefault(i,[])
                                for j in clean[i]:
                                    if j in content[key][i]:
                                        content[key][i].remove(j)
                                if not content[key][i]:
                                    del content[key][i]
                    else:
                        content[key]=clean
            contents[uid]={}
            contents[uid].update(content)

            #PARSING OBJECT
            if typ=='include':
                incl=Path(filename).curdir()+ uid
                main+=self.parse(incl,objects,contents)
                continue
            elif typ=='ontology':
                self.parse_ontology(uid,content)
                continue
            elif typ=='node':
                obj=self.parse_node(uid,content)
                objects[current[0]].setup.add_change(obj,content.get('tags',[]) )

            elif typ=='relation':
                obj=self.parse_relation(uid,content)
                objects[current[0]].setup.add_relation(obj)
                for a in obj.atoms:
                    self.node_db.add_edge(obj.nodes[0],obj.nodes[1],a)
            elif typ=='action':
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
                obj=self.parse_frame(uid,content)
                if len(cur_obj)==1:
                    cur_obj.append(obj)
                else:
                    cur_obj=cur_obj[:1]+[obj]
                cur_obj[0].add_frame(obj)
            elif typ=='sequence':
                obj=self.parse_sequence(uid,content)
                cur_obj=[obj]
                main.append(obj)

            objects[uid]=obj
            notes=content.pop('note',[])+content.pop('text',[])
            if notes:
                #print 'GETTING TEXT',uid,notes
                n=notes.pop(0)
                self.text_db.set(uid,'text',n.strip())
                [self.text_db.add(uid,'comment',n.strip()) for n in notes]

            if typ in ('sequence','frame','action'):
                for a in obj.atoms:
                    self.atom_db.add_instance(Atom(a),obj)

        for seq in main:
            for fr in seq.frames:
                for act in fr.actions:
                    for node in act.states:
                        for a in act.states[node]:
                            self.atom_db.add_instance(Atom(a),(act,node) )
                    for rel in act.relations:
                        for a in rel.atoms:
                            self.atom_db.add_instance(Atom(a),(act,rel.nodes ) )
        #self.objects=objects
        return main

    def parse_ontology(self,typ,content=None):
        if content is None:
            content={}
        if typ=='atom':
            ont=self.atom_db
        elif typ=='node':
            ont=self.node_db
        elif typ=='action':
            ont=self.action_db
        elif typ=='sequence':
            ont=self.sequence_db
        for s in content.get('states',[]):
            states=content['states']
            for elem in states:
                ont.add_node(elem,states[elem])
        for r in content.get('relations',[]):
            obj=r.replace('(','').replace(')','').split(',')
            for rel in content['relations'][r]:
                ont.add_edge(obj[0],obj[1],rel)

    def parse_node(self,uid,content=None):
        if content is None:
            content={}

        if not uid in self.node_db:
            #tags=content.pop('tags',())
            node= Node(uid)#,atoms=tags)
            self.node_db.add(node)
        else:
            node=self.node_db[uid]
            #node.atoms=list(set(node.atoms).union() )
        return node

    def parse_relation(self,uid,content=None):
        if content is None:
            content={}

        nodes=uid.replace('(','').replace(')','').split(',')
        for n in nodes:
            self.parse_node(n)
        return Relation(nodes,atoms=content.pop('tags',()))

    def parse_action(self,uid,content):
        tags,states,relations,roles=content.pop('tags',()),content.pop('states', ()
            ),content.pop('relations',()),content.pop('roles',{} )
        #print states
        #print relations
        roles.update(OrderedDict([( j[0],[i]) for i, j in content.iteritems()]) )
        act= Action(uid, atoms=tags,
            states=OrderedDict([(self.parse_node(i),states[i]) for i in states]),
            relations=[self.parse_relation(r,{'tags':relations[r]}) for r in relations],
            roles=OrderedDict([(self.parse_node(i),roles[i]) for i in roles]) )
        return act

    def parse_frame(self,uid,content):
        tags=content.pop('tags',())
        return Frame(uid,atoms=tags)

    def parse_sequence(self,uid,content):
        tags=content.pop('tags',())
        setup=Action(uid+'|setup|setup')
        setup_frame=Frame(uid+'|setup',actions=[setup])
        return Sequence(uid,atoms=tags,frames=[setup_frame])

