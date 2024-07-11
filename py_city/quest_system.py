class Quest:
    def __init__(self, description, target_type, target_count):
        self.description = description
        self.target_type = target_type
        self.target_count = target_count
        self.current_count = 0

    def update(self, event_type):
        if event_type == self.target_type:
            self.current_count += 1
            return self.current_count >= self.target_count
        return False

available_quests = [
    Quest("Catch 3 criminals", "criminal_caught", 3),
    Quest("Help 5 civilians", "civilian_helped", 5),
    Quest("Patrol the city (visit 10 buildings)", "building_visited", 10)
]
