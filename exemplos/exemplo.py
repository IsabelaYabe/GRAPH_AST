from __future__ import annotations
from abc import ABC, abstractmethod
import re
from typing import Optional, Iterable

# ===== Infra do Chain =====
class Handler(ABC):
    def __init__(self) -> None:
        self._next: Optional[Handler] = None

    def set_next(self, nxt: "Handler") -> "Handler":
        self._next = nxt
        return nxt  # facilita encadear: a.set_next(b).set_next(c)

    def handle(self, ctx: dict) -> dict:
        self._check(ctx)
        if self._next:
            return self._next.handle(ctx)
        return ctx  # passou por toda a cadeia

    @abstractmethod
    def _check(self, ctx: dict) -> None:
        ...

# ===== Regras de senha (Handlers) =====
class MinLength(Handler):
    def __init__(self, n: int) -> None:
        super().__init__()
        self.n = n

    def _check(self, ctx: dict) -> None:
        pwd = ctx["password"]
        if len(pwd) < self.n:
            raise ValueError(f"Senha muito curta (mínimo {self.n}).")

class CharsetPolicy(Handler):
    def __init__(self, min_lower=1, min_upper=1, min_digit=1, min_special=1) -> None:
        super().__init__()
        self.min_lower = min_lower
        self.min_upper = min_upper
        self.min_digit = min_digit
        self.min_special = min_special
        self.rx_lower = re.compile(r"[a-z]")
        self.rx_upper = re.compile(r"[A-Z]")
        self.rx_digit = re.compile(r"\d")
        self.rx_special = re.compile(r"[^A-Za-z0-9]")

    def _count(self, rx, s: str) -> int:
        return len(rx.findall(s))

    def _check(self, ctx: dict) -> None:
        pwd = ctx["password"]
        if self._count(self.rx_lower, pwd) < self.min_lower:
            raise ValueError("Falta letra minúscula.")
        if self._count(self.rx_upper, pwd) < self.min_upper:
            raise ValueError("Falta letra maiúscula.")
        if self._count(self.rx_digit, pwd) < self.min_digit:
            raise ValueError("Falta dígito.")
        if self._count(self.rx_special, pwd) < self.min_special:
            raise ValueError("Falta caractere especial.")

class MaxRun(Handler):
    """Bloqueia sequências repetidas longas (ex.: 'aaaa' com max_run=3)"""
    def __init__(self, max_run: int = 3) -> None:
        super().__init__()
        self.max_run = max_run

    def _check(self, ctx: dict) -> None:
        pwd = ctx["password"]
        run = 1
        for i in range(1, len(pwd)):
            run = run + 1 if pwd[i] == pwd[i-1] else 1
            if run > self.max_run:
                raise ValueError(f"Muitas repetições do mesmo caractere (>{self.max_run}).")

class NotInCommonList(Handler):
    """Evita senhas muito comuns (lista offline de exemplo)."""
    def __init__(self, commons: Iterable[str]) -> None:
        super().__init__()
        self.commons = set(x.strip().lower() for x in commons)

    def _check(self, ctx: dict) -> None:
        if ctx["password"].lower() in self.commons:
            raise ValueError("Senha muito comum.")

class NotInHistory(Handler):
    """Evita reuso recente (comparação simples). Em produção, compare hashes (ex.: Argon2/Bcrypt)."""
    def __init__(self, last_passwords: Iterable[str]) -> None:
        super().__init__()
        self.last = set(last_passwords)

    def _check(self, ctx: dict) -> None:
        if ctx["password"] in self.last:
            raise ValueError("Senha já usada recentemente.")

# ===== Exemplo de uso =====
def build_password_chain() -> Handler:
    commons = ["123456", "password", "qwerty", "111111", "abc123", "senha123"]
    history = ["Abc!2345xyz", "Rio#2024$FGV"]  # exemplo; guarde hashes na vida real
    head = MinLength(12)
    head.set_next(CharsetPolicy(min_lower=1, min_upper=1, min_digit=1, min_special=1))\
        .set_next(MaxRun(3))\
        .set_next(NotInCommonList(commons))\
        .set_next(NotInHistory(history))
    return head

if __name__ == "__main__":
    chain = build_password_chain()

    testes = [
        "Curta1!",                # curto
        "somenteletrasAAAA!",     # falta dígito
        "AAAAaaaa!!!!1111",       # run muito longo (AAAA)
        "Password123!",           # comum (password)
        "Abc!2345xyz",            # no histórico
        "Botafogo#2025Ok",        # válida
    ]

    for pwd in testes:
        ctx = {"password": pwd, "username": "isabela"}
        try:
            chain.handle(ctx)
            print(f"OK  -> {pwd!r}")
        except ValueError as e:
            print(f"FAIL-> {pwd!r}: {e}")
