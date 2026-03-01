class Score:
    def __init__(self):
        self.score = 0

    def add_score(self, score):
        self.score = max(0, self.score + int(score))

    def deduct(self, deduct):
        self.score = max(0, self.score - int(deduct))

    def get_score(self):
        return self.score

    def set_score(self, score):
        self.score = max(0, int(score))

    def reset_score(self):
        self.score = 0