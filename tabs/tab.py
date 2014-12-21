class Tab:
    def __init__(self, config={}):
        """
        Do something with the provided settings here
        """
        self.title = "DEFAULT TITLE"
    
    def render_tab(self, ctx):
        raise NotImplementedError("render_tab not implemented on %s!" % self.__class__.__name__)