


class Val:

    def __init__(self, val):
        self.value = val

    def __gt__(self, other):
        if type(other) == Val:
            return self.value > other.value
        return self.value > other

    def __lt__(self, other):
        if type(other) == Val:
            return self.value < other.value
        return self.value < other

    def __eq__(self, other):
        if type(other) == Val:
            return self.value == other.value
        return self.value == other

    def __or__(self, other):
        if type(other) == Val:
            return self.value or other.value
        return self.value or other

    def __and__(self, other):
        if type(other) == Val:
            return self.value and other.value
        return self.value and other

    def __add__(self, other):
        if type(other) == Val:
            return self.value + other.value
        return self.value + other

    def __sub__(self, other):
        if type(other) == Val:
            return self.value - other.value
        return self.value - other

    def __mul__(self, other):
        if type(other) == Val:
            return self.value * other.value
        return self.value * other

    def __divmod__(self, other):
        if type(other) == Val:
            return self.value // other.value, self.value % other.value
        return self.value // other, self.value % other

    def __repr__(self):
        return str(self.value)

    def eval(self):
        return self.value


class Op:
    pass


class LT(Op):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"({self.a} < {self.b})"

    def __repr__(self):
        return f"({self.a} < {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a < b


class GT(Op):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return f"({self.a} > {self.b})"

    def __repr__(self):
        return f"({self.a} > {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a > b


class AND(Op):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"({self.a} && {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a and b


class OR(Op):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"({self.a} || {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a or b


class PLUS(Op):

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"({self.a} + {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a + b


class MINUS(Op):

    def __init(self, a, b):
        self.a = a
        self.b = b

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"({self.a} - {self.b})"

    def eval(self):
        if issubclass(type(self.a), Op) or type(self.a) == Expr:
            a = self.a.eval()
        else:
            a = self.a
        if issubclass(type(self.b), Op) or type(self.b) == Expr:
            b = self.b.eval()
        else:
            b = self.b
        return a - b


class Expr:

    def __init__(self, e):
        self.e = e

    def __lt__(self, other):
        if type(other) == Expr:
            return self.eval() < other.eval()
        return self.eval() < other

    def __gt__(self, other):
        if type(other) == Expr:
            return self.eval() > other.eval()
        return self.eval() > other

    def __repr__(self):
        return repr(self.e)

    def eval(self):
        return self.e.eval()


"""
#cur_price = self.EMAT.data["close"].iloc[i]
cur_value = 5
diff = 0.08

emac = LT(8, 3)
msic = GT(3, 8)
stop_loss = GT(diff, 0.01)
signal = AND(emac, msic)

cond = OR(signal, stop_loss)
print(stop_loss)
print(stop_loss.eval())
print(signal)
print(signal.eval())
print(cond)
print(cond.eval())
"""