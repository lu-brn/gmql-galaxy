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
    PROJECT = 'PROJECT'
    MAP = 'MAP'
    ORDER = 'ORDER'
    JOIN = 'JOIN'
    COVER = 'COVER'
    FLAT = 'FLAT'
    SUMMIT = 'SUMMIT'
    HISTOGRAM = 'HISTOGRAM'

class Wff(Enum):
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
    SQRT = 'SQRT'
    NULL = 'NULL'
    META = 'META'
    MATH = ''

class DistalConditions(Enum) :
    DL = 'DL'
    DLE = 'DLE'
    MD = 'MD'
    DGE = 'DGE'

class DistalStream(Enum):
    UPSTREAM = 'UP'
    DOWNSTREAM = 'DOWN'

class CoordParam(Enum):
    LEFT = 'LEFT'
    LEFT_DISTINCT = 'LEFT_DISTINCT'
    RIGHT = 'RIGHT'
    RIGHT_DISTINCT = 'RIGHT_DISTINCT'
    INT = 'INT'
    CAT = 'CAT'
    BOTH = 'BOTH'

