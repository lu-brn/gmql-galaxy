#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Enum Classes
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

from enum import Enum


class Operator(Enum):
    MATERIALIZE = 'MATERIALIZE'
    SELECT = 'SELECT'
    MAP = 'MAP'

class wff(Enum):
    AND = 'AND'
    OR = 'OR'
    NOT = 'NOT'
    BLOCK = 'BLOCK'

class RegFunction(Enum):
    COUNT = 'COUNT'
    COUNTSAMP = 'COUNTSAMP'
    BAG = 'BAG'
    BAGD = 'BAGD'
    SUM = 'SUM'
    AVG = 'AVG'
    MIN = 'MIN'
    MAX = 'MAX'
    MEDIAN = 'MEDIAN'
    STD = 'STD'
