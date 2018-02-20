#!/usr/bin/env python
# --------------------------------------------------------------------------------
# GMQL Queries Statements Classes
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------

import yaml
from gmql_queries_constants import * 

class Statement(object):

    def __init__(self):

        self.operator = Operator
        self.variables = dict ()
        self.params = dict ()

    def save(self, syntax):

        var_o = self.variables.get('output')
        var_i = [self.variables.get('input1'),self.variables.get('input2','')]

        stm = syntax['STATEMENT'].format(operator=self.operator.value,
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
        self.operator = Operator.MATERIALIZE
        self.set_variable(filename, 'output')
        self.set_variable(input_ds, 'input1')

    def save(self, syntax):

        stm = syntax['MATERIALIZE'].format(variable=self.variables.get('input1'),
                                           file_name=self.variables.get('output'))

        return stm


class Select(Statement):

    def __init__(self):
        super(Select, self).__init__()
        self.operator = Operator.SELECT

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
            f_predicate = predicate.save(select_params['semijoin_predicates'], sep)
            params.append(select_params['semijoin'].format(predicate=f_predicate))

        stm = stm.format(parameters=sep.join(params))

        return stm

    @staticmethod
    def save_wff(syntax, pred):
        w_format = syntax['wff']

        if isinstance(pred, list):
            if pred[-1] is Wff.AND or Wff.OR:
                return w_format[pred[-1]].format(p1=Select.save_wff(syntax, pred[0]), p2=Select.save_wff(syntax, pred[1]))
            if pred[-1] is Wff.NOT or Wff.BLOCK:
                return w_format[pred[-1]].format(p=Select.save_wff(syntax, pred[0]))
        else :
            if isinstance(pred, Predicate):
                return pred.save(syntax)
            else:
                return pred

    def set_output_var(self, var):
        self.set_variable(var, 'output')

    def set_input_var(self, var):
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
        self.operator = Operator.MAP
        self.count_attribute = ''

    def set_output_var(self, var):
        self.set_variable(var, 'output')

    def set_reference_var(self, var):
        self.set_variable(var, 'input1')

    def set_experiment_var(self, var):
        self.set_variable(var, 'input2')

    def set_count_attribute(self, name):
        self.count_attribute = name

    def set_new_regions(self, regionAttributes):
        self.set_param(regionAttributes, 'newRegions')

    def set_joinby_clause(self, joinbyClause):
        self.set_param(joinbyClause, 'joinby')

    def save(self, syntax):
        stm = super(Map, self).save(syntax)

        params_form = syntax['PARAMS']
        map_format = params_form['MAP']
        type_sep = params_form['type_separator']
        param_sep = params_form['param_separator']

        parameters = []

        # Format new region attributes definitions

        param_regs = self.params.get('newRegions', None)

        if param_regs :
            newRegions = map(lambda x: x.save(params_form),param_regs)
            parameters.append(map_format['regions'].format(newRegions=param_sep.join(newRegions)))


        # Format user chosen name for the count attribute, if present
        if self.count_attribute :
            parameters.append(map_format['count'].format(count_name=self.count_attribute))

        # Format joinby clause
        jbc = self.params.get('joinby', None)

        if jbc:
            parameters.append(map_format['joinby'].format(joinbyClause=jbc.save(params_form,param_sep)))


        stm = stm.format(parameters=type_sep.join(parameters))

        return stm


class Order(Statement):

    def __init__(self):
        super(Order, self).__init__()
        self.operator = Operator.ORDER

    def set_output_var(self, var):
        self.set_variable(var, 'output')

    def set_input_var(self, var):
        self.set_variable(var, 'input1')

    def set_ordering_attributes(self, ordAtt, type):
        # Type can be 'metadata' or 'region'
        self.set_param(ordAtt,type+'OrderingAttributes')

    def set_top_options(self, topts):
        self.set_param(topts, 'top')

    def save(self, syntax):
        stm = super(Order,self).save(syntax)

        params_form = syntax['PARAMS']
        order_form = params_form['ORDER']
        type_sep = params_form['type_separator']
        sep = params_form['param_separator']

        params = []

        # Format metadata attribute lists
        meta_att = self.params.get('metadataOrderingAttributes', None)
        if meta_att:
            params.append(order_form['metadata']['orderingAttributes']
                          .format(att_list=meta_att.save(order_form['att_list'],sep)))

        # Top options
        tops = self.params.get('top', None)
        if tops:
            m_tops = filter(lambda x: x[0] == 'metadata', tops)
            m_tops = map(lambda x: order_form[x[0]]['top'][x[1]].format(k=x[2]), m_tops)
            params.append(type_sep.join(m_tops))

          # Format region attribute lists
        region_att = self.params.get('regionOrderingAttributes', None)
        if region_att:
            params.append(order_form['region']['orderingAttributes']
                          .format(att_list=region_att.save(order_form['att_list'],sep)))


        # Top options
        if tops:
            r_tops = filter(lambda x: x[0] == 'region', tops)
            r_tops = map(lambda x: order_form[x[0]]['top'][x[1]].format(k=x[2]), r_tops)
            params.append(type_sep.join(r_tops))

        stm = stm.format(parameters=type_sep.join(params))

        return stm



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
    def __init__(self, newRegion, function, argRegion):
        self.newRegion = newRegion
        self.function = function
        self.argument = argRegion

    def save(self, syntax):

        f = syntax['function'].format(function=self.function.value,
                                      arg=self.argument)

        return syntax['new_region'].format(r=self.newRegion,
                                           function=f)


class AttributesList(object):

    def __init__(self, attributes):
        self.attributes = attributes

    def save(self, syntax, sep):
        attr =  sep.join(self.attributes)
        return attr

class OrderingAttributes(AttributesList):

    def __init__(self):
        attributes = list()
        super(OrderingAttributes, self).__init__(attributes)

    def add_attribute(self, att, desc):
        self.attributes.append((att,desc))

    def save(self, syntax, sep):
        self.attributes = map(lambda x: syntax[x[1]].format(att=x[0]), self.attributes)
        return super(OrderingAttributes, self).save(syntax, sep)


class JoinbyClause(AttributesList):

    def __init__(self, attributes):
        super(JoinbyClause, self).__init__(attributes)

    def save(self, syntax, sep):
        attributes = map(lambda x: syntax['metajoin_condition'][x[1]].format(att_name=x[0]), self.attributes)
        return sep.join(attributes)


class SemiJoinPredicate(AttributesList):

    def __init__(self, attributes, dataset, condition):
        super(SemiJoinPredicate, self).__init__(attributes)
        self.ds_ext = dataset
        self.condition = condition

    def save(self, syntax, sep):
        attributes = super(SemiJoinPredicate, self).save(syntax, sep)
        return syntax[self.condition].format(attributes=attributes, ds_ext=self.ds_ext)