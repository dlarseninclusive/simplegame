# File: slave_system.py
class Slave:
    def __init__(self, owner, obedience_level=100):
        self.owner = owner
        self.obedience_level = obedience_level
        self.current_task = None

    def assign_task(self, task):
        """Assign a new task to the slave."""
        self.current_task = task

    def complete_task(self):
        """Mark the current task as completed."""
        self.current_task = None
