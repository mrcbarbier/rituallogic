from PyQt4 import QtGui
from PyQt4 import QtCore
import sys
from qt import Ui_MainWindow


from classes import *
from ontology import *
from utilityclasses import *
#from datatools import *




class Editor(QtGui.QMainWindow):
    SAVES=0
    block_changes=0
    _focused=None
    log_path='./logs'
    backup_path='./logs'

    def __init__(self, parent=None,**kwargs):
        self.sequences=[] #Data

        self.undo_stack=[]
        self.redo_stack=[]

        #QT
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.timeline_editor=self.TimelineEditor(self)
        self.db_editor=self.DatabaseEditor(self)
        self.ui.setupUi(self)
        self.db_editor.make_connections()
        self.timeline_editor.make_connections()
        self.make_connections()

        try:

            for l in open(Path(self.log_path)+'.last','r'):
                if not l.strip():
                    continue
                filename=l.strip()
                self.set_data_from(filename)
        except Exception as e:
            print e
            pass

    def make_connections(self):
        #Connections
        ui=self.ui
        ui.actionLoad.triggered.connect(self.load_menu)
        ui.actionSave.triggered.connect(self.save_menu)

        ui.actionSave.setShortcut("Ctrl+S")
        ui.actionLoad.setShortcut("Ctrl+L")


    def save_menu(self):
        name = QtGui.QFileDialog.getSaveFileName(self, 'Save File')
        self.save_data_to(name)

    def load_menu(self):
        name = QtGui.QFileDialog.getOpenFileName(self, 'Load File')
        try:
            self.set_data_from(name)
        except Exception as e:
            diag=QtGui.QErrorMessage()
            diag.showMessage('Could not load {}: {}'.format(name,e) )
            diag.exec_()


    class SubEditor():
        _block_changes=0
        @property
        def block_changes(self):
            return self._block_changes or self.parent.block_changes
        @block_changes.setter
        def block_changes(self,val):
            self._block_changes=val
        def make_backup(self):
            self.parent.make_backup()

    class DatabaseEditor(SubEditor):
        def __init__(self,parent):
            self.parent=parent
            self.ui=parent.ui
            self.current_ontology=None
            self.dico={}

        def set_data(self):
            self.text_db=self.parent.text_db
            self.atom_db=self.parent.atom_db
            self.node_db=self.parent.node_db

            self.set_current_ontology(0)

        def make_connections(self):
            #Connections
            ui=self.ui
            ui.onto_select.activated.connect(self.set_current_ontology)
            ui.onto_search_field.activated.connect(self.make_search)
            ui.onto_search_rule.activated.connect(self.make_search)
            ui.search_button.clicked.connect(self.make_search)

            ui.onto_table.itemChanged.connect(self.change_dataitem)

        def change_dataitem(self,view):
            if self.block_changes:
                return 0
            handled=0
            olddata=self.dico[view]
            newdata=[unicode(view.data(c,0).toString()) for c in range(view.columnCount())]
            cur=self.current_ontology
            try:
                cur.rem_edge(*olddata)
                cur.add_edge(*newdata)
                handled =1
            except Exception as e:
                print e
            if handled:
                self.make_search()
                self.make_backup()
            return handled

        def set_current_ontology(self,*args):
            ont=[self.atom_db,self.node_db][args[0]]
            self.current_ontology=ont
            self.set_display()

        def make_search(self,*args):
            ui=self.ui
            text=unicode(ui.onto_search.text())
            field=unicode(ui.onto_search_field.currentText()).lower()
            rule=unicode(ui.onto_search_rule.currentText()).lower()
            #print  text,field,rule

            if not text:
                return self.set_display()
            query=QueryHandler(self.current_ontology)
            self.set_display(query.filter(text,field=field,rule=rule) )

        def set_display(self,content=None):
            self.dico={}
            twidget=self.ui.onto_table
            twidget.clear()
            if content is None:
                ont=self.current_ontology
                content=ont.edges
            parent={}
            self.block_changes=True

            for e in content:
                if e[2]=='part':
                    pwid=self.dico.get(e[1],QtGui.QTreeWidgetItem(twidget))
                    pwid.setText(0,e[1])
                    self.dico[e[1]]=pwid
                    wid=self.dico.get(e[0],QtGui.QTreeWidgetItem(pwid))
                    wid.setText(0,e[0])
                    self.dico[e[0]]=wid

                    parent[e[0]]=wid
            for i,j,e in content:
                if i in parent:
                    widget=parent[i]
                else:
                    widget=twidget
                item=QtGui.QTreeWidgetItem(widget)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                item.setText(0,i)
                if j:
                    item.setText(1,j)
                if e:
                    item.setText(2,e)
                self.dico[item]=(i,j,e)
                self.dico[(i,j,e)]=item

            self.block_changes=False
            twidget.expandAll()


    class TimelineEditor(SubEditor):
        def __init__(self,parent):
            self.parent=parent
            self.ui=parent.ui
            self.timeline=[] #Compiled frames
            self.dico={}

        @property
        def sequences(self):
            return self.parent.sequences

        def change_focused(self):
            data=self._focused
            if not data:
                return
            data.uid=unicode(self.ui.uid_edit.text())
            data.atoms=unicode(self.ui.tags_edit.document().toPlainText()).replace(' ','').split(',')
            comments=unicode(self.ui.comment_edit.document().toPlainText()).replace(' ','').split(',')
            self.text_db.set(data.uid,'comment',comments)


        def change_dataitem(self,view):
            if self.block_changes:
                return 0
            handled=0
            data=self.dico[view]
            content=[unicode(view.data(c,0).toString()) for c in range(view.columnCount())]
            #print content
            if isinstance(data[0],Action):
                if data[1]=='member':
                    i,j=content
                    i=data[2]
                    if not j in self.node_db:
                        self.node_db.add(Node(j))
                    data[0].members[i]=self.node_db[j]
                    self.set_action(data[0])
                    handled=1
                elif data[1]=='nodestate':
                    i,j=content
                    if not i in self.node_db:
                        self.node_db.add(Node(i))
                    data[0].changes[self.node_db[i]]=j.replace(' ','').split(',')
                    handled=1
                elif data[1]=='relationship':
                    i,j=[x.replace(' ','').split(',') for x in content]
                    for n in i:
                        if not i in self.node_db:
                            self.node_db.add(Node(i))
                    i=[self.node_db[x] for x in i]
                    handled=1
                    idx=self.relationship_table.selectedIndexes()[0].row()
                    if idx<len(data.relations):
                        data[0].relations[idx]=Relation(i,j)
                    else:
                        data[0].relations.append(Relation(i,j))
            if handled:
                self.timeline=[self.seqview.frame_by_frame(seq) for seq in self.sequences]
                self.make_backup()
            return handled

        def set_focused_object(self,obj):
            #self.make_backup()
            self._focused=None
            self.ui.uid_edit.setText(obj.uid)
            self.ui.tags_edit.setPlainText(', '.join(obj.atoms))
            self.ui.comment_edit.setPlainText(', '.join(self.text_db.get(obj,'comment' )))
            self._focused=obj
            #TODO: COMMENTS

        def set_atom_completer(self,edit):
            completer = QtGui.QCompleter(self.atom_db.keys())
            edit.setCompleter(completer)

        def actionlist_menu(self,position):
            indexes = self.ui.actionlist.selectedIndexes()
            level= len(indexes) > 0
            menu = QtGui.QMenu()
            if level == 0:
                menu.addAction("New action", self.new_action)
                menu.addAction("Delete action",self.delete_action )
            else:
                menu.addAction("New action", self.new_action)

            menu.exec_(self.ui.actionlist.viewport().mapToGlobal(position))

        def timeline_menu(self, position):

            indexes = self.ui.timeline_tree.selectedIndexes()
            if len(indexes) > 0:

                level = 0
                index = indexes[0]
                while index.parent().isValid():
                    index = index.parent()
                    level += 1
            else:
                level=-1

            menu = QtGui.QMenu()
            if level == 0:
                menu.addAction("New sequence", self.new_sequence)
                menu.addAction("Delete sequence", self.delete_sequence)
                menu.addAction("New frame",self.new_frame )
            elif level == 1:
                menu.addAction("New frame",self.new_frame )
                menu.addAction("Delete frame",self.delete_frame )

            menu.exec_(self.ui.timeline_tree.viewport().mapToGlobal(position))


        @property
        def selected_text(self):
            return self.ui.text_edit.textCursor().selectedText()

        def set_frame(self,frame=None,**kwargs):
            if not self.sequences:
                return
            if frame is None or not isinstance(frame,Frame):
                sel=self.ui.timeline_tree.selectedItems()
                if not sel:
                    data=self.sequences[0]
                else:
                    sel=sel[0]
                    data=self.dico[sel]
                    self.set_focused_object(data)
            else:
                data=frame
                self.dico[frame].setSelected(1)
                sel=data
            if isinstance(data,Sequence):
                data=data.frames[0]
            text=self.text_db.get(data.uid,'text')
            if text:
                #self.ui.text_edit.setVisible(1)
                self.ui.text_edit.setText(text[0])
            else:
                #self.ui.text_edit.setVisible(0)
                self.ui.text_edit.setText('')
            self.ui.actionlist.clear()
            for action in data.actions:
                if action in self.dico:
                    old=self.dico[action]
                    del self.dico[old]
                    del old
                item=QtGui.QListWidgetItem(self.ui.actionlist)
                self.dico[item]=action
                self.dico[action]=item
                #print item, action
                item.setText(action.uid.split('|')[-1] )
            graph=None
            for gseq in self.timeline:
                for g in gseq:
                    if g.uid==data.uid:
                        graph=g
                        break
            if graph:
                #Nodestates
                self.ui.nodestate_view.clear()
                for i in graph.nodes:
                    item=QtGui.QTreeWidgetItem()
                    item.setText(0,i)
                    item.setText(1,', '.join(graph.node[i]))
                    self.ui.nodestate_view.addTopLevelItem(item)

                #Relationships
                self.ui.relationship_view.clear()
                for n1,n2 in graph.pairs():
                    item=QtGui.QTreeWidgetItem()
                    item.setText(0,', '.join([n1,n2]) )
                    item.setText(1,', '.join(graph.edge[n1][n2]))
                    self.ui.relationship_view.addTopLevelItem(item)

            if sel and data.actions:
                self.set_action()#data.actions[0])

        def set_action(self,action=None):
            if action is None or not isinstance(action,Action):
                sel=self.ui.actionlist.selectedItems()
                if not sel:
                    if self.ui.timeline_tree.selectedItems():
                        view=self.ui.timeline_tree.selectedItems()[0]
                        obj=self.dico[view]
                    else:
                        obj=self.sequences[0]
                    if hasattr(obj,'setup'):
                        data=obj.setup
                    else:
                        data=obj.actions[0]
                else:
                    sel=sel[0]
                    data=self.dico[sel]
                    self.set_focused_object(data)
            else:
                data=action
                self.ui.actionlist.setCurrentItem(self.dico[data])
            #Members
            self.ui.role_table.clear()
            for i in ACTION_KEYWORDS:

            #for i,j in data.members.iteritems():
                item=QtGui.QTreeWidgetItem()
                self.dico[item]=(data,'member',i)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                item.setText(0,i)
                if i in data.members:
                    j=data.members[i]
                    item.setText(1,j.uid)
                self.ui.role_table.addTopLevelItem(item)

            #Nodestates
            self.ui.nodestate_table.clear()
            #print data.uid,data.changes
            for i,j in data.changes.iteritems():
                item=QtGui.QTreeWidgetItem()
                self.dico[item]=(data,'nodestate',i)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                item.setText(0,i.uid)
                item.setText(1,', '.join(j))
                self.ui.nodestate_table.addTopLevelItem(item)

            #Relationships
            self.ui.relationship_table.clear()
            for i in data.relations:
                item=QtGui.QTreeWidgetItem()
                self.dico[item]=(data,'relationship',i)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                item.setText(0,', '.join(i.nodes) )
                item.setText(1,', '.join(i.atoms) )
                self.ui.relationship_table.addTopLevelItem(item)


        def add_sequence(self,seq,alone=True,position=None):
            if position is None:
                self.sequences.append(seq)
            else:
                self.sequences.insert(position,seq)
            widget=QtGui.QTreeWidgetItem(self.ui.timeline_tree)
            widget.setText(0,seq.uid)
            self.dico[widget]=seq
            self.dico[seq]=widget
            for frame in seq.frames:
                fwidget=QtGui.QTreeWidgetItem(widget)
                fwidget.setText(0,frame.uid.split('|')[-1])
                self.dico[fwidget]=frame
                self.dico[frame]=fwidget
            if alone:
                self.set_frame()
            if not position is None:
                self.renew_tree()

        def add_frame(self,frame,seq):
            widget=self.dico[seq]
            fwidget=QtGui.QTreeWidgetItem(widget)
            fwidget.setText(0,frame.uid.split('|')[-1])
            self.dico[fwidget]=frame
            self.dico[frame]=fwidget
            self.set_frame(frame)

        def new_sequence(self):
            indexes = self.ui.timeline_tree.selectedIndexes()
            view=self.ui.timeline_tree.itemFromIndex(indexes[0])
            obj=self.dico[view]
            uid='Sequence{}'.format(len(self.sequences))
            setup=Action(uid+'|setup|setup')
            setup_frame=Frame(uid+'|setup',actions=[setup])
            seq=Sequence(uid,frames=[setup_frame]  )
            self.add_sequence(seq,
                alone=True,position=self.sequences.index(obj)+1 )
            self.make_backup()

        def delete_sequence(self):
            indexes = self.ui.timeline_tree.selectedIndexes()
            view=self.ui.timeline_tree.itemFromIndex(indexes[0])
            obj=self.dico[view]
            del view
            self.sequences.remove(obj)
            del obj
            self.renew_tree()
            self.make_backup()

        def renew_tree(self):
            self.ui.timeline_tree.clear()
            seqs=tuple(self.sequences)
            self.sequences[:]=[]
            for seq in seqs:
                self.add_sequence(seq,alone=0)
            self.set_frame()

        def new_frame(self):
            indexes = self.ui.timeline_tree.selectedIndexes()
            view=self.ui.timeline_tree.itemFromIndex(indexes[0])
            obj=self.dico[view]
            if isinstance(obj,Sequence):
                fr=obj.new_frame()
                fr.new_action()
                self.add_frame(fr,obj)

            else:
                for seq in self.sequences:
                    if obj in seq.frames:
                        fr=seq.new_frame()
                        fr.new_action()
                        self.add_frame(fr,seq)
            self.make_backup()

        def delete_frame(self):
            indexes = self.ui.timeline_tree.selectedIndexes()
            view=self.ui.timeline_tree.itemFromIndex(indexes[0])
            obj=self.dico[view]
            view.parent().removeChild(view)
            del view
            for seq in self.sequences:
                seq.rem_frame(obj)
            del obj
            self.make_backup()

        def add_action(self,action,frame,seq):
            self.set_frame(frame)

        def new_action(self,view):
            obj=self.dico[view]
            for seq in self.sequences:
                for fr in seq.frames:
                    if obj in fr.actions:
                        act=fr.new_action()
                        self.add_action(act,fr,seq)
            self.make_backup()

        def delete_action(self,view):
            obj=self.dico[view]
            for seq in self.sequences:
                for fr in seq.frames:
                    if fr.rem_action(obj):
                        self.set_frame(fr)
                        self.set_action(fr.actions[0])
            self.make_backup()


        def set_timeline_widget(self,*args):
            #print args
            self.ui.timeline_stacked.setCurrentIndex(args[0])


        def make_connections(self):
            #Connections
            ui=self.ui

            ui.timeline_switch.activated.connect(self.set_timeline_widget)
            ui.uid_edit.textChanged.connect(self.change_focused)
            ui.tags_edit.textChanged.connect(self.change_focused)
            ui.comment_edit.textChanged.connect(self.change_focused)

            ui.timeline_tree.itemPressed.connect(self.set_frame)
            ui.timeline_tree.currentItemChanged.connect(self.set_frame)
            ui.timeline_tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            ui.timeline_tree.customContextMenuRequested.connect(self.timeline_menu)

            ui.actionlist.itemPressed.connect(self.set_action)
            ui.actionlist.currentItemChanged.connect(self.set_action)
            ui.actionlist.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
            ui.actionlist.customContextMenuRequested.connect(self.actionlist_menu)

            ui.role_table.itemChanged.connect(self.change_dataitem)
            ui.nodestate_table.itemChanged.connect(self.change_dataitem)
            ui.relationship_table.itemChanged.connect(self.change_dataitem)

        def set_data(self,sequences):
            self.text_db=self.parent.text_db
            self.atom_db=self.parent.atom_db
            self.node_db=self.parent.node_db


            tree=self.ui.timeline_tree
            self.sequences[:]=[]
            self.dico={}
            tree.clear()
            [self.add_sequence(s,alone=False) for s in sequences]
            #print self.sequences[0].frames[0].actions[0].changes, sequences[0].frames[0].actions[0].changes
            self.set_frame()
            if sequences:
                self.set_focused_object(sequences[0])
            self.timeline=[self.seqview.frame_by_frame(seq) for seq in self.sequences]
            tree.expandAll()


    def keyPressEvent(self, event):
        ## has ctrl-E been pressed??
        undo = (event.modifiers() == QtCore.Qt.ControlModifier and
                      event.key() == QtCore.Qt.Key_Z)
        redo = (event.modifiers() == (QtCore.Qt.ControlModifier| QtCore.Qt.ShiftModifier)
            and  event.key() == QtCore.Qt.Key_Z)

        new =(event.modifiers() == QtCore.Qt.ControlModifier and
                      event.key() == QtCore.Qt.Key_N)
        if undo:
            self.undo()
        if redo:
            self.redo()
        if new:
            self.make_new()

    def set_data_from(self,filename,log=1):
        self.iohandler=parser=IOHandler()
        self.timeline_editor.seqview=SequenceViewer()
        sequences=parser.parse(filename)

        self.text_db=parser.text_db
        self.atom_db=parser.atom_db
        self.node_db=parser.node_db

        self.timeline_editor.set_data(sequences)
        self.db_editor.set_data()
        #Logging the last file to reopen
        if log:
            f=open(Path(self.log_path)+'.last','w')
            f.write(filename)
            f.close()
            print 'Setting data from',filename
        self.undo_stack.append(filename)

    def save_data_to(self,filename,log=1):
        self.iohandler.export(filename,self.sequences)

        #Logging the last file to reopen
        if log:
            f=open(Path(self.log_path)+'.last','w')
            f.write(filename)
            f.close()

    def make_backup(self):
        #print debug_caller_name(3)
        #import time
        current=Path(self.backup_path)+'{}.bk'.format(self.SAVES) #time.asctime()
        self.block_changes=True
        #print "Making backup",current
        self.save_data_to(current,log=0)
        self.SAVES+=1
        self.undo_stack.append(current)
        if len(self.undo_stack)>20:
            self.undo_stack.pop(0)
        self.block_changes=False

    def undo(self):
        if len(self.undo_stack)<2:
            return
        last=self.undo_stack.pop(-1)
        #print 'UNDO:',last
        #self.block_changes=True
        self.set_data_from(self.undo_stack.pop(-1),log=0)
        self.redo_stack.append(last)
        #self.block_changes=False

    def redo(self):
        if len(self.redo_stack)<1:
            return
        #self.block_changes=True
        last=self.redo_stack.pop(-1)
        #print 'REDO:',last
        self.set_data_from(last,log=0)
        #self.block_changes=False



if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = Editor()
    #myapp.set_data_from('example.dat')

    myapp.show()
    sys.exit(app.exec_())

