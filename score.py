class Score:
    def __init__(self):
        self.score = 0

    def add_score(self, score):
        self.score += score

    def deduct(self, deduct):
        self.score -= deduct

    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = score

    def reset_score(self):
        self.score = 0