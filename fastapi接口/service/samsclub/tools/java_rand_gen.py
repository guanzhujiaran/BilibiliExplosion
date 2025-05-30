# --- Helper functions (from previous response) ---
def to_int32(value: int) -> int:
    """Converts a Python integer to a 32-bit signed integer (simulating Java int)."""
    value &= 0xFFFFFFFF
    if value & 0x80000000:
        return value - 0x100000000
    return value


def unsigned_right_shift(value: int, bits: int) -> int:
    """Simulates Java's unsigned right shift (>>>) on a 32-bit integer."""
    return (value & 0xFFFFFFFF) >> bits


# --- XorWowRandomPython class (from previous response) ---
class XorWowRandomPython:
    def __init__(self, seed1: int, seed2: int, seed3: int = None,
                 seed4: int = None, seed5: int = None, addend_seed: int = None):
        if seed3 is None:
            s1 = to_int32(seed1)
            s2 = to_int32(seed2)
            self._x = s1
            self._y = s2
            self._z = to_int32(0)
            self._w = to_int32(0)
            self._v = to_int32(~s1)
            self._addend = to_int32(to_int32(s1 << 10) ^ unsigned_right_shift(s2, 4))
        else:
            self._x = to_int32(seed1)
            self._y = to_int32(seed2)
            self._z = to_int32(seed3)
            self._w = to_int32(seed4)
            self._v = to_int32(seed5)
            self._addend = to_int32(addend_seed)

        if (self._x == 0 and self._y == 0 and self._z == 0 and \
                self._w == 0 and self._v == 0):
            raise ValueError("Initial state must have at least one non-zero element among x, y, z, w, v.")

        for _ in range(64):
            self.nextInt()  # Warm-up

    def nextInt(self) -> int:
        t = self._x
        t = to_int32(t ^ unsigned_right_shift(t, 2))
        self._x = self._y
        self._y = self._z
        self._z = self._w
        old_v = self._v
        self._w = old_v
        term1 = to_int32(t ^ to_int32(t << 1))
        term2 = to_int32(term1 ^ old_v)
        new_v = to_int32(term2 ^ to_int32(old_v << 4))
        self._v = new_v
        self._addend = to_int32(self._addend + 362437)
        return to_int32(self._v + self._addend)

    # _e_h and nextBits are not strictly needed for the final wrapper class,
    # if we've established that f65205a.nextInt() directly calls XorWow's nextInt().
    # However, keeping them for completeness of XorWowRandomPython simulation if needed elsewhere.
    def _e_h(self, value: int, bit_count: int) -> int:
        if not (0 <= bit_count <= 32):
            raise ValueError("bit_count must be between 0 and 32.")
        if bit_count == 0:
            return 0
        shifted_value = unsigned_right_shift(value, 32 - bit_count)
        return to_int32(shifted_value)

    def nextBits(self, bit_count: int) -> int:
        return self._e_h(self.nextInt(), bit_count)

class F65205aRandomIntGenerator:
    def __init__(self):
        """
        Initializes the internal random number generator based on the logic of
        ys.e.a(10000) which creates a ys.f (XorWowRandom) instance.
        ys.e.a(10000) effectively calls new ys.f(10000, 0).
        """
        seed_value_from_java = 10000

        # Calculate parameters for XorWowRandomPython's 2-argument constructor simulation
        # param1 = 10000
        # param2 = 10000 >> 31 (Java arithmetic shift) = 0
        param1 = to_int32(seed_value_from_java)

        # Simulating Java's arithmetic right shift for param2
        if param1 >= 0:
            param2 = param1 >> 31  # Python's >> is arithmetic here
        else:
            # For negative numbers, Python's >> is also arithmetic.
            # Java's >> for negative numbers shifts in 1s from the left.
            param2 = param1 >> 31
        param2 = to_int32(param2)  # Ensure it's 0 or -1 as a 32-bit int

        # Internal XorWowRandom instance
        self._rng = XorWowRandomPython(param1, param2)

    def nextInt(self) -> int:
        """
        Generates the next random integer, simulating `this.f65205a.nextInt()` from Java.
        As analyzed, this directly calls the underlying XorWowRandom's nextInt().
        """
        return self._rng.nextInt()

if __name__ == "__main__":
    a = F65205aRandomIntGenerator()
    for i in range(902):
        print(a.nextInt())