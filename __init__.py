# -*- coding: utf-8 -*-

from classes import *
from ontology import *
from utilityclasses import *
#from datatools import *



if __name__ =='__main__':
    parser=IOHandler()
    sequences=parser.parse('example.dat')
    gviz=GraphVisualization()
    seqview=SequenceViewer()
    for seq in sequences:
        graphs=seqview.frame_by_frame(seq)
        for g in graphs:
            gviz.plot(g,hold=1)
        plt.show()

if 0:


    y=Node("yaj",atoms=('human') )
    f=Node("fire",atoms=('unlit') )

    a=Action('y_light_f',atoms=('slowly'),members={'AGENT':y,'OBJECT':f},
         changes={f:AtomChange('-unlit +lit')} )

    fr1=Frame('initial')
    fr2=Frame('sutra1',actions=[a])

    s=Sequence('DPM',frames=[fr1,fr2])


    atom_ont=Ontology('atom')
    atom_ont.add_edge('slowly','speed','IN')
    atom_ont.add_edge('quickly','speed','IN')
    atom_ont.add_edge('speed','manner','IN')

    q=QueryHandler()
    gviz=GraphVisualization()


    print s.frames[0].nodes

    gviz.plot(atom_ont,hold=0)