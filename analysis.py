# -*- coding: utf-8 -*-

from ontology import *

"""Analysis of ritual sequences"""


class Grammar(OntologyRuleset):
    """Ruleset for an ontology of grammatical objects."""
    rule_types={
    'syntax':[
        'adjoin',
        'qualify',
        'bind',
        'depend',
        ],
    'morphology':[
        'affix',
        ]
    }


class Lexicon(OntologyRuleset):
    """Ruleset for an ontology of lexical objects"""
    pass


class Inference(object):
    """Rules for inferring grammatical and lexical relations from raw material."""
    pass