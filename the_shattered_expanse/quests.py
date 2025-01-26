# quests.py

class Quest:
    def __init__(self, quest_id, description, faction, target_item, target_count):
        self.quest_id = quest_id
        self.description = description
        self.faction = faction
        self.target_item = target_item
        self.target_count = target_count
        self.complete = False

class QuestSystem:
    """
    Handles adding, tracking, and completing quests.
    """
    def __init__(self):
        self.quests = {}

    def add_quest(self, quest_id, description, faction, target_item, target_count):
        quest = Quest(quest_id, description, faction, target_item, target_count)
        self.quests[quest_id] = quest

    def update_quests(self, player):
        """
        In a real game, you'd check multiple conditions or quest steps.
        Here we just see if the quest item count is met.
        """
        for qid, quest in self.quests.items():
            if not quest.complete:
                current_amount = player.inventory.get(quest.target_item, 0)
                if current_amount >= quest.target_count:
                    quest.complete = True
                    # As a reward, raise faction rep or give an item
                    player.change_faction_rep(quest.faction, 10)
                    print(f"Quest '{quest.description}' complete! +10 rep with {quest.faction}")

    def check_item_collection(self, player, item_type):
        """
        Called whenever the player picks up an item.
        We can see if it helps complete a quest.
        """
        self.update_quests(player)
