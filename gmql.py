# Custom datatypes for the use of the GMQL framework within Galaxy
# ----------------------------------------------------------------------------
# Luana Brancato, luana.brancato@mail.polimi.it
# ----------------------------------------------------------------------------

from galaxy.datatypes import metadata
from galaxy.datatypes.metadata import MetadataElement
from galaxy.datatypes.tabular import Tabular
from galaxy.datatypes.sniff import get_headers

import logging

class Gdm ( Tabular ):
    """Tab delimited data in Gdm format"""

    file_ext = "gdm"
    column_names = ['chr','left','right','strand','name','score']


    MetadataElement( name='columns', default='6', desc='Number of Columns', readonly=True, visible=False )
    MetadataElement( name='column_types', default=['str','int','int','str','str','float'],
                     param=metadata.ColumnTypesParameter, desc="Column types", readonly=True, visible=False)


    def display_peek(self, dataset):
        """Returns formatted html of peek"""

        return self.make_html_table(dataset, column_names=self.column_names)

    def sniff(self, filename):
        """
        Determines whether a file is in gdm format

        GDM files have at least 6 required fields.
        (Actually in the format definition only the first 5 are mandatory, but the ones returned by the system have
        always 6).

        Required fields must be tab separated.

        Columns 0, 3, 4 must be strings.
        Columns 1, 2, 5 numbers.

        Column 5 (Score) can be not provided.


        """


        headers = get_headers(filename, '\t', count=10)


        try:
            for hdr in headers:
                if hdr and hdr[0] and not hdr[0].startswith('#'):
                    if len(hdr) != 6:
                        return False
                    try:
                        int(hdr[1])
                        int(hdr[2])
                    except:
                        return False
                    if hdr[5] != '.':
                        try:
                            float(hdr[5])
                        except:
                            return False
                    return True
        except:
            return False
