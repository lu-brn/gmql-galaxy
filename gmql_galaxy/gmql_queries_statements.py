#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Statements Classes
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import yaml

class Statement(object):

    def __init__(self):

        self.operator = str()
        self.variables = dict ()
        self.params = dict ()

    def save(self, output):
        pass

    def write_query(self, syntax):
        self.syntax = yaml.load(syntax)

    def set_variable(self, var, var_name):
        self.variables[var_name] = var

    def set_param(self, param, param_type):
        self.params[param_type] = param

class Materialize(Statement):

    def __init__(self, filename, input_ds):
        super(Materialize, self).__init__()
        self.operator = 'MATERIALIZE'
        self.set_variable(filename, 'output')
        self.set_variable(input_ds, 'input1')


class Select(Statement):

    def __init__(self):
        super(Select, self).__init__()
        self.operator = 'SELECT'

    def set_output_var(self, var):
        self.set_variable(var, 'output')

    def set_input_ds(self, var):
        self.set_variable(var, 'input1')

    def set_metadata_predicates(self, logicalPredicate):
        self.set_param(logicalPredicate, 'metadata')

    def set_region_predicates(self, logicalPredicate):
        self.set_param(logicalPredicate, 'region')

    def set_semijoin_predicates(self, sjClauses):
        self.set_param(sjClauses, 'semijoin')


class WellFormedFormula(object) :

    def __init__(self, predicate):
        self.wff = predicate

    def save(self, output):
        pass

    def write_query(self, syntax):
        pass

    def negate(self):
        self.wff = (self.wff, 'NOT')
        return self

    def and_(self, predicate):
        self.wff = (self.wff, predicate.wff, 'AND')
        return self

    def or_(self, predicate):
        self.wff = (self.wff, predicate.wff, 'OR')
        return self


class Predicate(object):

    def __init__(self, field1, field2, condition):

        self.p_attribute = field1
        self.p_value = field2
        self.condition = condition

    def save(self, output):
        pass

    def write_query(self, syntax):
        pass


class MetaPredicate(Predicate):

    def __init__(self, attribute, value, condition):
        super(MetaPredicate, self).__init__(attribute, value, condition)

class RegionPredicate(Predicate):

    def __init__(self, attribute, value, condition):
        super(RegionPredicate, self).__init__(attribute, value, condition)

    def set_value_type(self, type=None):
        """Possible values type are: coordinate, float, string, meta_attribute"""

        if type is None :
            if self.p_attribute in ['chr', 'left', 'right', 'strand'] :
                #The region attribute given is a region coordinate attribute
                self.value_type = 'coordinate'
            else :
                try:
                    self.p_value = float(self.p_value)
                    self.value_type = 'float'
                except ValueError :
                    self.value_type = 'string'
        else:
            #The type is given.
            self.value_type = type

class MetadataComparison(object):

    def __init__(self, attributes):
        self.attributes = list ()

    def set_attributes(self, attributes):
        self.attributes = list()
        self.attributes.append(attributes)

class SemiJoinPredicate(MetadataComparison):

    def __init__(self, attributes, dataset, condition):
        super(MetadataComparison, self).__init__()
        self.set_attributes(attributes)
        self.ds_ext = dataset
        self.condition = condition