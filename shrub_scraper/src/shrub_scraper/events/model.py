class Event:
    def __init__(self,**kwargs):
        self.source = kwargs['source'] if 'source' in kwargs else None
        self.title = kwargs['title'] if 'title' in kwargs else None
        self.date = kwargs['date'] if 'date' in kwargs else None
        self.description = kwargs['description'] if 'description' in kwargs else None
        self.url = kwargs['url'] if 'url' in kwargs else None
        self.type_ = kwargs['type_'] if 'type_' in kwargs else None