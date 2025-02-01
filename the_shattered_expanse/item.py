class Item:
    def __init__(self, name, item_type, stats=None):
        self.name = name
        self.type = item_type
        self.stats = stats or {}

    def get_stat(self, stat_name, default=0):
        return self.stats.get(stat_name, default)
