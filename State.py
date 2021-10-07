

class State:

    def __init__(self):
        self.type = None

    def __repr__(self):
        return self.type

    def process_candle(self, candle):
        return


class LookingToBuy(State):

    def __init__(self):
        self.type = "Looking to buy"
    def process_candle(self, candle):
        if candle == 1:
            return Holding()
        return self

class Holding(State):

    def __init__(self):
        self.type = "Holding"

    def process_candle(self, candle):
        if candle == 2:
            return Waiting(3)
        return self

class Waiting(State):

    def __init__(self, waiting):
        self.waiting = waiting
        self.type = self.print_type()

    def __repr__(self):
        return f"Waiting ({self.waiting})"

    def process_candle(self, candle):
        if not self.waiting:
            return LookingToBuy()
        self.waiting -= 1
        return self

    def print_type(self):
        return f"Waiting ({self.waiting})"


class StateMachine:

    def __init__(self):
        self.state = Waiting(3)


    def receive_candle(self, candle):
        self.state = self.state.process_candle(candle)
        print(candle, self.state)


candles = [3,2,3,1,1,1,15,3,5,2,5,6,1,2]
ma = StateMachine()
for c in candles:
    ma.receive_candle(c)