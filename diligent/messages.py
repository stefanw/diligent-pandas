def message(mes, **kwargs):
    return DiligentMessage(mes, **kwargs)


class DiligentMessage(object):
    def __init__(self, message, rows=None):
        self.message = message
        self.rows = rows

    def __str__(self):
        return self.message


class MessageRenderer(object):
    def __init__(self, message):
        self.message = message


class HTMLMessageRenderer(MessageRenderer):
    def render(self, df, column=None):
        if isinstance(self.message, DiligentMessage):
            return self.to_html(df, column=column)
        return str(self.message)

    def to_html(self, df, column=None):
        if self.message.rows is not None:
            return '<h4>{}</h4>{}'.format(
                self.message, df.ix[self.message.rows].to_html()
            )
        return self.message
