try:
    str = unicode
except NameError:
    pass

from collections import OrderedDict
from multiprocessing import Pool
import itertools
import inspect
import uuid

import pandas as pd

from .utils import escape_js
from .messages import HTMLMessageRenderer


def diligent(df, **kwargs):
    """diligent - Proofing a dataframe

    Args:
        df (pandas.DataFrame or pandas.Series): Description
        **kwargs (TYPE): Description

    Returns:
        TYPE: Description
    """

    if isinstance(df, pd.Series):
        df = df.to_frame()
    columns = df.columns
    checks = registry.get_checks(
        include=kwargs.pop('include', None),
        exclude=kwargs.pop('exclude', None),
    )
    return DiligentReport(
        df,
        checks,
        columns,
        **kwargs
    )


def run_report(args):
    df, check, col, check_no = args
    if check.dataframe:
        return (col, check_no), list(check(df))
    return (col, check_no), list(check(df[col]))


class DiligentReport(object):
    NUMBER_OF_ITEMS = 5

    def __init__(self, df, checks, columns, verbose=False, interactive=True,
                 parallel=True):
        self.df = df
        self.checks = checks
        self.check_order = OrderedDict((c, i) for i, c in enumerate(checks))
        self.columns = list(columns)
        self.reports = OrderedDict(
            itertools.chain(
                 (((None, check), check(df)) for check in checks
                        if check.dataframe),
                 (((col, check), check(df[col])) for col in columns
                            for check in checks if not check.dataframe),
            )
        )
        self.verbose = verbose
        self.interactive = interactive
        self.parallel = parallel

    def get_reports(self):
        if self.parallel:
            return self.get_reports_parallel()
        return self.get_reports_serial()

    def get_reports_serial(self):
        for column, check in self.reports.keys():
            report_list = self.get_report((column, check))
            yield (column, self.check_order[check]), report_list

    def get_reports_parallel(self):
        for result in self.get_finished_reports():
            yield result
        pool = Pool()
        tasks = list(self.get_unfinished_reports_args())
        for key, report in pool.imap_unordered(run_report, tasks):
            # Store result
            self.reports[(key[0], self.checks[key[1]])] = report
            yield key, report

    def get_unfinished_reports_args(self):
        for col, check in self.reports.keys():
            if inspect.isgenerator(self.reports[(col, check)]):
                yield self.df, check, col, self.check_order[check]

    def get_finished_reports(self):
        for key in self.reports:
            if not inspect.isgenerator(self.reports[key]):
                yield (key[0], self.check_order[key[1]]), self.reports[key]

    def get_report(self, key):
        if inspect.isgenerator(self.reports[key]):
            # Store generator result
            self.reports[key] = list(self.reports[key])
        return self.reports[key]

    def get_report_columns(self):
        return ['Check', 'Dataframe'] + self.columns

    def get_internal_columns(self):
        return [None] + self.columns

    def html_generator(self):
        reports = OrderedDict(self.get_reports())
        yield '<table><thead><tr>'
        for col in self.get_report_columns():
            yield '<th>'
            yield col
            yield '</th>'
        yield '</tr></thead><tbody>'
        for check_no, check in enumerate(self.checks):
            yield '<tr><th>%s</th>' % str(check)
            for column in self.get_internal_columns():
                yield '<td>'
                report = reports.get((column, check_no))
                if report is not None:
                    for m in self.render_messages(report,
                                                  column=column):
                        yield m
                yield '</td>'
            yield '</tr>'
        yield '</tbody></table>'

    def render_messages(self, messages, column=None):
        messages = [self.render_message(m, column=column) for m in messages]
        if messages is not None:
            if len(messages) > 1:
                yield '<ul><li>'
                if self.verbose:
                    yield '</li><li>'.join(messages)
                else:
                    yield '</li><li>'.join(messages[:self.NUMBER_OF_ITEMS])
                yield '</li></ul>'
                if not self.verbose and len(messages) > self.NUMBER_OF_ITEMS:
                    yield '<p>And {} more, set to verbose to see</p>'.format(
                            len(messages) - self.NUMBER_OF_ITEMS)

            elif messages:
                yield messages[0]

    def render_message(self, message, column=None):
        return HTMLMessageRenderer(message).render(self.df, column=column)

    def empty_table_generator(self, uid):
        yield '<table><thead><tr>'
        for col in self.get_report_columns():
            yield '<th>'
            yield col
            yield '</th>'
        yield '</tr></thead><tbody>'
        for check_no, check in enumerate(self.checks):
            yield '<tr><th>%s</th>' % str(check)
            for column_index, column in enumerate(self.get_internal_columns()):
                if ((column is None and check.dataframe) or
                        (column is not None and not check.dataframe)):
                    yield '<td id="diligent-%s-%s-%s">&hellip;</td>' % (uid,
                                                            check_no,
                                                            column_index)
                else:
                    yield '<td style="background: #ddd"></td>'
            yield '</tr>'
        yield '</tbody></table>'

    def to_html(self):
        if not self.interactive:
            return ''.join(self.html_generator())
        return self.interactive_html()

    _repr_html_ = to_html

    def interactive_html(self):
        from IPython.display import display, HTML
        uid = str(uuid.uuid4())

        display(HTML(''.join(self.empty_table_generator(uid))))
        internal_columns = self.get_internal_columns()

        for key, report in self.get_reports():
            js = '''
                (function(){
                    var node = document.getElementById('diligent-%(uid)s-%(check_no)s-%(column_no)s');
                    var data = '%(data)s';
                    node.innerHTML = data;
                    if (!data) {
                        node.style.backgroundColor = '#eee';
                    }
                }());
            ''' % {
                'uid': uid,
                'check_no': key[1],
                'column_no': internal_columns.index(key[0]),  # FIXME
                'data': escape_js(''.join(self.render_messages(report)))
            }
            display({'application/javascript': js}, raw=True)
        return ''


class DiligentCheck(object):
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.dataframe = kwargs.pop('dataframe', False)
        self.tags = kwargs.pop('tags', [])
        if not isinstance(self.tags, (list, tuple)):
            self.tags = [self.tags]

    def __str__(self):
        if 'name' in self.kwargs:
            return self.kwargs['name']
        return self.func.__name__

    def __repr__(self):
        return str(self)

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class DiligentRegistry(object):
    def __init__(self):
        self.checks = OrderedDict()

    def add_check(self, func, args, kwargs):
        self.checks[func] = DiligentCheck(func, *args, **kwargs)

    def __iter__(self):
        for key in self.checks:
            yield self.checks[key]

    def get_checks(self, include=None, exclude=None):
        if include is None:
            include = []
        if exclude is None:
            exclude = []
        if isinstance(include, str):
            include = [i.strip() for i in include.split(',')]
        if isinstance(exclude, str):
            exclude = [e.strip() for e in exclude.split(',')]
        if not isinstance(include, (list, tuple)):
            include = [include]
        if not isinstance(exclude, (list, tuple)):
            exclude = [exclude]
        return [c for c in self.__iter__() if (
            self.filter_check(c, include, exclude)
        )]

    def filter_check(self, check, include, exclude):
        tags = set(check.tags)
        return ((not include or set(include) & tags)
                and (not exclude or not set(exclude) & tags))

    def register(self, *args, **kwargs):
        def _register(func):
            self.add_check(func, args, kwargs)
            return func

        if len(args) == 1 and callable(args[0]) and not kwargs:
            return _register(args[0])
        else:
            return _register

registry = DiligentRegistry()
