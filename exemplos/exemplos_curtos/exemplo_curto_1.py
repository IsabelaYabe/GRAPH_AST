from abc import ABC, abstractmethod


class Foo(ABC):
    @abstractmethod
    def toast(self):
        pass

class BarFoo(Foo):
    def toast(self):
        return "Concrete implementation"

def create_instance(x):
    if x > 0:
        return BarFoo()
    else:
        raise ValueError("x must be positive")
        