# GMQL editor: composition of the specific statements on the base of the syntax
# defined in gmql_syntax config file..
# --------------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# --------------------------------------------------------------------------------
import os
import yaml
import logging


class Compositor(object) :

    def __init__(self):

        y_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gmql_syntax.yaml')

        with open(y_path, 'r') as yfile:
            self.syntax = yaml.load(yfile)

        return

    def read_query(self, file):
        """Read the query in the gmql_query format and transform it in an actual textual query"""

        #logging.basicConfig(filename='/home/luana/log.txt',level=logging.DEBUG, filemode='w')

        with open(file, 'r') as f_in :
            s = map(lambda x: x.rstrip('\n').split('\t'), f_in)
            sts = map(lambda  x: self.compose_statement(x),s)
            query = '\n'.join(sts)

        return query

    def compose_statement(self, st_parts):
        """gmql_queries has the following structure:
        OUT_VARIABLE    OPERATION   PARAMETERS  IN_VARIABLE1    [IN_VARIABLE2]"""

        o_var = st_parts[0]
        op = st_parts[1]
        par = st_parts[2]
        i_vars = list ()

        for i in range(3,len(st_parts)) :
            i_vars.append(st_parts[i])
            logging.debug(st_parts[i])

        i_vars = ' '.join(i_vars)

        st = self.write_statement(o_var, op, par, i_vars)

        return st


    def write_statement(self, o_variable, operation, parameters, i_variables):

        st = self.syntax['STATEMENT']

        st = st.format(o_variable=o_variable,
                 operation=operation,
                 parameters=parameters,
                 i_variables=i_variables)

        return st

