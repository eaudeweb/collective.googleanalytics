from plone.memoize.instance import memoize
from collective.googleanalytics.utils import json_serialize, js_literal
from string import Template
import datetime
import time
import os


class AnalyticsReportVisualization(object):
    """
    The visualization for an Analytics report. This object is generated by the
    visualization method of the AnalyticsReportRenderer object. It encapsulates
    all of the logic for turning the report results in to javascript
    configuration for Google Visualizations.
    """

    def __init__(self, report, columns, rows, options):
        self.report = report
        self.columns = columns
        self.rows = rows
        self.options = options

    @memoize
    def render(self):
        """
        Returns the markup and javascript to create the visualization.
        """

        template_file = os.path.join(
            os.path.dirname(__file__), 'visualization.tpl')
        template = Template(open(template_file).read())

        template_vars = {
            'package_name': self.report.viz_type.lower(),
            'columns': self._getColumns(),
            'data': json_serialize(self.rows),
            'chart_type': self.report.viz_type,
            'id': self.id(),
            'options': self._getOptions()
        }

        return template.substitute(template_vars)

    @memoize
    def id(self):
        """
        Creates a unique ID that we can use for the div that will hold the
        visualization.
        """

        return 'analytics-' + str(hash((self.report.id, time.time())))

    @memoize
    def _getColumns(self):
        """
        Returns javascript that adds the appropriate columns to the DataTable.
        """

        column_types = []
        if self.rows:
            for value in self.rows[0]:
                if isinstance(value, datetime.date):
                    col_type = 'date'
                elif isinstance(value, str):
                    col_type = 'string'
                else:
                    col_type = 'number'
                column_types.append(col_type)
            js = []
            for col_type, label in zip(column_types, self.columns):
                js.append('data.addColumn("%s", "%s");' % (col_type, label))
            return '\n'.join(js)
        return ''

    @memoize
    def _getOptions(self):
        """
        Returns a javascript object containing the options
        for the visualization.
        """

        options = self.options.copy()
        # Set the width of the visualization to the container width if it
        # if not already set.
        if 'width' not in self.options.keys():
            options['width'] = js_literal('container_width')
        if options:
            return json_serialize(options)
        return 'null'
