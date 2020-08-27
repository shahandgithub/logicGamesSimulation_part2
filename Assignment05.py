from abc import ABC, abstractmethod


class Input:
    def __init__(self, owner):
        if not isinstance(owner, LogicGate):
            raise Exception("Owner should be a type of LogicGate")
        self._owner = owner

    def __str__(self):
        try:
            return str(self.value)
        except AttributeError:
            # It's possible to not have a value at the beginning
            return "(no value)"

    @property
    def owner(self):
        return self._owner

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # Normalize the value to bool
        self._value = bool(value)
        # Now that the input value has changed, tell to owner logic gate to re-evaluate
        self._owner.evaluate()


class Output:
    def __init__(self):
        self._connections = []

    def __str__(self):
        try:
            return str(self.value)
        except AttributeError:
            # It's possible not to have a value at the beginning
            return "(no value)"

    def connect(self, input):
        if not isinstance(input, Input):
            raise Exception("Output must be connected to an input")

        if input not in self._connections:
            self._connections.append(input)
        try:
            # Set the input's value to this output's value upon connection
            input.value = self._value
        except AttributeError:
            # If self.value is not there, skip it
            pass

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        # Normalize the value to bool
        self._value = bool(value)
        # After the output value changes, remember to send it to all the connected inputs
        for connection in self._connections:
            connection.value = self.value

    @property
    def connections(self):
        return self._connections


class CostMixin:
    COST_MULTIPLIER = 10

    def __init__(self, number_of_components):
        self._number_of_components = number_of_components
        self._cost = self.COST_MULTIPLIER * (self._number_of_components ** 2)

    @property
    def number_of_components(self):
        return self._number_of_components

    @property
    def cost(self):
        return self._cost


class NodeMixin:

    def __init__(self):
        self._next = None

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, next):
        if not isinstance(next, NodeMixin):
            raise Exception("Next should be a type of NodeMixin")
        self.next = next


class LogicGate(NodeMixin, ABC):
    def __init__(self, name, circuit=None):
        self._name = name
        self._next = None
        if circuit:
            if not isinstance(circuit, Circuit):
                raise Exception("circuit should be a type of Circuit")
            circuit.add(self)

    @property
    def name(self):
        return self._name

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, gate):
        self._next = gate


class UnaryGate(LogicGate, CostMixin):
    def __init__(self, name, circuit=None):
        CostMixin.__init__(CostMixin, 2)
        LogicGate.__init__(LogicGate, name)
        self._input = Input(self)
        self._output = Output()
        if circuit:
            if not isinstance(circuit, Circuit):
                raise Exception("circuit should be a type of Circuit")
            circuit.add(self)

    def __str__(self):
        return f"Gate {self.name}: input={self.input}, output={self.output}"

    @property
    def input(self):
        return self._input

    @property
    def output(self):
        return self._output


class BinaryGate(LogicGate, CostMixin):
    def __init__(self, name, circuit=None):
        LogicGate.__init__(LogicGate, name)
        CostMixin.__init__(CostMixin, 3)
        self._input0 = Input(self)
        self._input1 = Input(self)
        self._output = Output()
        if circuit:
            if not isinstance(circuit, Circuit):
                raise Exception("circuit should be a type of Circuit")
            circuit.add(self)

    def __str__(self):
        return f"Gate {self.name}: input0={self.input0}, input1={self.input1}, output={self.output}"

    @property
    def input0(self):
        return self._input0

    @property
    def input1(self):
        return self._input1

    @property
    def output(self):
        return self._output


class NotGate(UnaryGate):
    def evaluate(self):
        self.output.value = not self.input.value


class AndGate(BinaryGate):
    def evaluate(self):
        try:
            # This may throw an exception, if one of the input is not yet set, which is possible
            # in the normal course of evaluation, because setting the first input will kick
            # off the evaluation.  So just don't set the output.
            self.output.value = self.input0.value and self.input1.value
        except AttributeError:
            pass


class OrGate(BinaryGate):
    def evaluate(self):
        try:
            self.output.value = self.input0.value or self.input1.value
        except AttributeError:
            pass


class XorGate(BinaryGate):
    def evaluate(self):
        try:
            # Assume the value is bool, != is same as xor
            self.output.value = (self.input0.value != self.input1.value)
        except AttributeError:
            pass


class Circuit:

    def __init__(self):
        self.head = None
        self._cost = None

    @property
    def cost(self):
        return self._cost

    def add(self, gate):
        New_Node = gate
        if self.head is None:
            self.head = New_Node
            self._cost = gate.cost
            return

        last_entry = self.head
        while last_entry.next:
            last_entry = last_entry.next
        last_entry.next = New_Node
        self._cost = self._cost + gate.cost


def full_adder(a, b, ci):
    circuit = Circuit()
    xor_gate1 = XorGate("xor1", circuit)
    xor_gate2 = XorGate("xor2", circuit)
    xor_gate1.input1.value = a
    xor_gate1.input0.value = b
    xor_gate1.output.connect(xor_gate2.input0)
    xor_gate2.input1.value = ci
    and_gate1 = AndGate("and1", circuit)
    and_gate2 = AndGate("and2", circuit)
    and_gate1.input0.value = ci
    xor_gate1.output.connect(and_gate1.input1)
    and_gate2.input0.value = a
    and_gate2.input1.value = b
    or_gate = OrGate("or", circuit)
    and_gate1.output.connect(or_gate.input0)
    and_gate2.output.connect(or_gate.input1)
    t = (xor_gate2.output, or_gate.output.value, circuit.cost)
    return t


def test():
    tests = [test_not, test_and, test_or, test_xor, test_not_not, test_and_not, test_circuit, test_full_adder]
    for t in tests:
        print("Running " + t.__name__ + " " + "-" * 20)
        t()


def test_not():
    not_gate = NotGate("not")
    not_gate.input.value = True
    print(not_gate)
    not_gate.input.value = False
    print(not_gate)


def test_and():
    and_gate = AndGate("and")
    print("AND gate initial state:", and_gate)
    and_gate.input0.value = True
    print("AND gate with 1 input set", and_gate)
    and_gate.input1.value = False
    print("AND gate with 2 inputs set:", and_gate)
    and_gate.input1.value = True
    print("AND gate with 2 inputs set:", and_gate)


def test_or():
    or_gate = OrGate("or")
    or_gate.input0.value = False
    or_gate.input1.value = False
    print(or_gate)
    or_gate.input1.value = True
    print(or_gate)


def test_xor():
    # Testing xor
    xor_gate = XorGate("xor")
    xor_gate.input0.value = False
    xor_gate.input1.value = False
    print(xor_gate)
    xor_gate.input1.value = True
    print(xor_gate)


def test_not_not():
    not_gate1 = NotGate("not1")
    not_gate2 = NotGate("not2")
    not_gate1.output.connect(not_gate2.input)
    print(not_gate1)
    print(not_gate2)
    print("Setting not-gate input to False...")
    not_gate1.input.value = False
    print(not_gate1)
    print(not_gate2)


def test_and_not():
    and_gate = AndGate("and")
    not_gate = NotGate("not")
    and_gate.output.connect(not_gate.input)
    and_gate.input0.value = True
    and_gate.input1.value = False
    print(and_gate)
    print(not_gate)
    and_gate.input1.value = True
    print(and_gate)
    print(not_gate)


def test_circuit():
    circuit = Circuit()
    not_gate1 = NotGate("not1", circuit)
    not_gate2 = NotGate("not2", circuit)
    not_gate1.output.connect(not_gate2.input)
    print("Cost of NOT-NOT circuit is " + str(circuit.cost))


def test_full_adder():
    t = full_adder(True, True, False)
    for element in t:
        print(element)


if __name__ == '__main__':
    test()
