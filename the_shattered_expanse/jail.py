class Jail:
    def __init__(self):
        self.inmates = []  # List of dicts: {"character": <ref>, "time_remaining": <float>}
    
    def imprison(self, character, jail_time):
        """Send a character to jail."""
        character.in_jail = True
        self.inmates.append({"character": character, "time_remaining": jail_time})
    
    def update(self, dt):
        """Reduce jail time for inmates and release if done."""
        for inmate in self.inmates[:]:
            inmate["time_remaining"] -= dt
            if inmate["time_remaining"] <= 0:
                inmate["character"].in_jail = False
                self.inmates.remove(inmate)
