# -*- coding: utf-8 -*-

from classes import *
from ontology import *
from utilityclasses import *
#from datatools import *



if __name__ =='__main__':
    from ui import *
    app = QtGui.QApplication(sys.argv)
    myapp = Editor()
    #myapp.set_data_from('example.dat')

    myapp.show()
    sys.exit(app.exec_())

    if 0:
        gviz=GraphVisualization()
        gviz.plot(myapp.parser.atom_db,hold=0)