# -*- coding: utf-8 -*-

from classes import *
from ontology import *
from utilityclasses import *

y=Node("yaj",atoms=('human') )
f=Node("fire",atoms=('unlit') )

a=Action('y_light_f',atoms=('slowly'),members={'AGENT':y,'OBJECT':f},
     changes={f:AtomChange('-unlit +lit')} )

f=Frame('sutra1',actions=[a])

s=Sequence('DPM',frames=[f])


atom_ont=Ontology('atom')
atom_ont.add_edge('slowly','speed','IN')
atom_ont.add_edge('quickly','speed','IN')
atom_ont.add_edge('speed','manner','IN')

q=QueryHandler()
gviz=GraphVisualization()


print s.frames[0].nodes

gviz.plot(atom_ont)