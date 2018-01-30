#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Statements Classes
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import yaml
from enum import Enum

class Statement(object):

    def __init__(self):

        self.operator = str()
        self.variables = dict ()
        self.params = dict ()

    def save(self, syntax):

        var_o = self.variables.get('output')
        var_i = [self.variables.get('input1'),self.variables.get('input2','')]

        stm = syntax['STATEMENT'].format(operator=self.operator,
                                         out_var=var_o,
                                         in_vars=" ".join(var_i),
                                         parameters='{parameters}')

        return stm

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

    def save(self, syntax):

        stm = syntax['MATERIALIZE'].format(variable=self.variables.get('input1'),
                                           file_name=self.variables.get('output'))

        return stm


class Select(Statement):

    def __init__(self):
        super(Select, self).__init__()
        self.operator = 'SELECT'

    def save(self, syntax):
        stm = super(Select, self).save(syntax)
        params_form = syntax['PARAMS']
        select_params = params_form['SELECT']
        sep = params_form['type_separator']

        params = []

        # Format conditions over metadata
        predicate = self.params.get('metadata', None)

        if predicate:
            f_predicate = self.save_wff(params_form, predicate)
            params.append(select_params['metadata'].format(predicate=f_predicate))

        # Format conditions over samples fields
        predicate = self.params.get('region', None)

        if predicate:
            f_predicate = self.save_wff(params_form, predicate)
            params.append(select_params['region'].format(predicate=f_predicate))

        # Format semijoin conditions
        predicate = self.params.get('semijoin', None)

        if predicate:
            f_predicate = predicate.save(params_form)
            params.append(select_params['semijoin'].format(predicate=f_predicate))

        stm = stm.format(parameters=sep.join(params))

        return stm

    @staticmethod
    def save_wff(syntax, pred):
        w_format = syntax['wff']

        if isinstance(pred, list):
            if pred[-1] == 'AND' :
                return w_format['AND'].format(p1=Select.save_wff(syntax, pred[0]), p2=Select.save_wff(syntax, pred[1]))
            elif pred[-1] == 'OR' :
                return w_format['OR'].format(p1=Select.save_wff(syntax, pred[0]), p2=Select.save_wff(syntax, pred[1]))
            elif pred[-1] == 'NOT' :
                return w_format['NOT'].format(p=Select.save_wff(syntax, pred[0]))
            elif pred[-1] == 'BLOCK' :
                return w_format['BLOCK'].format(p=Select.save_wff(syntax, pred[0]))
        else :
            return pred.save(syntax)

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


class Map(Statement):
    def __init__(self):
        super(Map, self).__init__()
        self.operator = 'MAP'

    def set_output_var(self, var):
        self.set_variable(var, 'output')

    def set_reference_var(self, var):
        self.set_variable(var, 'input1')

    def set_experiment_var(self, var):
        self.set_variable(var, 'input2')

    def set_count_attribute(self, name=''):
        self.count_attribute = name

    def set_new_regions(self, regionAttributes):
        self.set_param(regionAttributes, 'newRegions')

    def set_joinby_clause(self, joinbyClause):
        sefl.set_param(joinbyClause, 'joinby')

    def save(self, syntax):
        pass


class Predicate(object):

    def __init__(self, field1, field2, condition):

        self.p_attribute = field1
        self.p_value = field2
        self.condition = condition
        self.value_type = 'string'

    def save(self, syntax):
        p_format = syntax['predicate']

        predicate = p_format[self.condition].format(att=self.p_attribute,
                                                    val=p_format['values'][self.value_type].format(p=self.p_value))

        return predicate


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
                    self.p_value = int(self.p_value)
                    self.value_type = 'int'
                except ValueError :
                    try:
                        self.p_value= float(self.p_value)
                        self.value_type = 'float'
                    except ValueError :
                        self.value_type = 'string'
        else:
            #The type is given.
            self.value_type = type

class RegionGenerator(object):
    def __init__(self, newRegion, function, oldRegion):
        self.newRegion = newRegion
        self.function = function
        self.argument = oldRegion

    def save(self, syntax):
        pass

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

class MetadataComparison(object):

    def __init__(self, attributes):
        self.attributes = attributes

    def save(self, syntax):
        sep = syntax['param_separator']
        attr =  sep.join(self.attributes)
        return attr

class JoinbyClause(MetadataComparison):

    def __init__(self, attributes):
        super(JoinbyClause, self).__init__(attributes)

    def save(self, syntax):
        # Works differently as some attributes could be actually be attribute + modifier (FULL, EXACT)
        pass

class SemiJoinPredicate(MetadataComparison):

    def __init__(self, attributes, dataset, condition):
        super(SemiJoinPredicate, self).__init__(attributes)
        self.ds_ext = dataset
        self.condition = condition

    def save(self, syntax):
        attributes = super(SemiJoinPredicate, self).save(syntax)

        return syntax['SELECT']['semijoin_predicate'][self.condition].format(attributes=attributes,
                                                                             ds_ext=self.ds_ext)