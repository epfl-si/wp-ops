import re
from flask import Response


class Metrics:
    """Over-engineered Prometheus metrics container / pretty-printer.

    @see https://github.com/prometheus/docs/blob/master/content/docs/instrumenting/exposition_formats.md
    """
    def __init__(self):
        self.metrics = []
        self.labels = {}

    def add_labels(self, labels):
        """Add `labels` implicitly to all subsequent calls to @link all."""
        self.labels = {**self.labels, **labels}

    def __repr__(self):
        return ''.join(self.metrics)

    def add(self, name, type, value, help=None, labels=None):
        metric_lines = ["# TYPE %s %s" % (name, type)]
        if help:
            metric_lines.insert(0, "# HELP %s %s" % (name, help))

        if labels:
            all_labels = {**self.labels, **labels}
        else:
            all_labels = self.labels
        if all_labels:
            qualified_name = '%s{%s}' % (
                name,
                ','.join('%s="%s"' % (k, self._quote_label_value(v))
                         for (k, v) in all_labels.items()))
        else:
            qualified_name = name
        metric_lines.append("%s %s" % (qualified_name, value))

        self.metrics.append(''.join('%s\n' % l for l in metric_lines))

    def _quote_label_value(self, v):
        return re.sub(r'([\"])', r'\\\1', v)

    def as_flask_response(self):
        return Response(self.__repr__(), mimetype='text/plain; version=0.0.4')
