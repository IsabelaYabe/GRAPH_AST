# exemplo.py
PI = 3.14

class Foo:
    """FOO class example"""
    _k = 0
    def __init__(self, x: int):
        self.x = x
    @staticmethod
    def util(z):
        return z*2
    @classmethod
    def make(cls, v):
        return cls(v)
    @property
    def valor(self):
        return self.x

def _aux(y): return y + 1
