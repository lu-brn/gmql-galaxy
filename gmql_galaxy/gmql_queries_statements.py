#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Statements Classes
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import yaml

class Statement(object):

    def __init__(self, syntax):

        self.syntax = yaml.load(syntax)

        self.operator = str()
        self.variables = dict ()
        self.params = dict ()

    def save(self, output):
        pass

    def write_query(self):
        pass

    def set_variable(self, var, var_name):
        self.variables.update(var_name=var)

    def set_param(self, param, param_type):
        self.params.update(param_type=param)

class Materialize(Statement):

    def __init__(self, syntax):
        super(Materialize, self).__init__(syntax=syntax)

class Select(Statement):

    def __init__(self, syntax):
        super(Select, self).__init__(syntax=syntax)
        self.operator = 'SELECT'

    def set_output_ds(self, var):
        self.set_variable(var, 'output')

    def set_input_ds(self, var):
        self.set_variable(var, 'input')

    def set_metadata_predicates(self, logicalPredicate):
        self.set_param(logicalPredicate, 'metadata')

    def set_region_predicates(self, logicalPredicate):
        self.set_param(logicalPredicate, 'region')

    def set_semijoin_predicates(self, sjClauses):
        self.set_param(sjClauses, 'semijoin')


class WellFormedFormula(object) :

    def __init__(self,p):
        self.wff = p

    def save(self, output):
        pass

    def write_query(self, syntax):
        pass

    def negate(self):
        self.wff = (self.wff, 'NOT')
        return self

    def _and(self, p):
        self.wff = (self.wff, p.wff, 'AND')
        return self

    def _or(self, p):
        self.wff = (self.wff, p.wff, 'OR')
        return self


class Predicate(object):

    def __init__(self, field1, field2):

        self.field1 = field1
        self.field2 = field2
        self.condition = None

    def save(self, output):
        pass

    def write_query(self, syntax):
        pass


    def eq(self):
        self.condition = '=='
        return self

    def lt(self):
        self.condition = '<'
        return self

    def gt(self):
        self.condition = '>'
        return self

    def let(self):
        self.condition = '<='
        return self

    def get(self):
        self.condition = '>='
        return self


class MetaPredicate(Predicate):

    def __init__(self, attribute, value):
        super(MetaPredicate, self).__init__(attribute, value)

class RegionPredicate(Predicate):

    def __init__(self, attribute, value):
        super(RegionPredicate, self).__init__(attribute, value)

class SemiJoinPredicate(Predicate):

    def __init__(self, attributes, dataset):
        super(SemiJoinPredicate, self).__init__(attributes, dataset)

    def is_in(self):
        self.condition = 'IN'
        return self

    def is_not_int(self):
        self.condition = 'NOT IN'
        return self