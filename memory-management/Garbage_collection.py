"""
garbage_collection.py

Demonstrates the one failure mode reference counting can't handle on
its own: a reference cycle. Run this top to bottom.
"""

import gc


class Node:
    def __init__(self, name):
        self.name = name
        self.next = None

    def __repr__(self):
        return f"Node({self.name})"


# --- Part 1: build a cycle ------------------------------------------------

a = Node("a")
b = Node("b")
a.next = b
b.next = a  # a -> b -> a : a cycle. Neither's ref count can reach 0
            # through deletion of 'a' and 'b' alone, because each Node
            # still holds a reference to the other.

print("1. Tracked objects before deletion:", len(gc.get_objects()))

del a
del b
# At this point the NAMES a and b are gone, but the two Node objects
# still reference each other. Plain reference counting would leak
# this forever — there is no path to ref count 0 without help.

collected = gc.collect()
print("2. Objects collected by gc.collect():", collected)
print("3. Tracked objects after collection:", len(gc.get_objects()))
# The cyclic collector found the unreachable cycle (nothing outside
# the cycle points to it anymore) and freed both Nodes.


# --- Part 2: see the leak happen when GC is off --------------------------

gc.disable()

before = len(gc.get_objects())

# Create a batch of cyclic garbage while the collector is off
for _ in range(1000):
    x = Node("x")
    y = Node("y")
    x.next = y
    y.next = x
    # x and y go out of scope at the end of this loop iteration, but
    # since GC is disabled, nothing reclaims the cycles they formed.

after_leak = len(gc.get_objects())
print(f"4. Tracked objects with GC disabled: {before} -> {after_leak}")
print("   (grew because 1000 cycles were created and never collected)")

gc.enable()
collected = gc.collect()
after_collect = len(gc.get_objects())
print(f"5. After re-enabling and running gc.collect(): collected {collected}")
print(f"   Tracked objects now: {after_collect}")
# This is the cleanest demonstration that reference counting alone
# (which was running the whole time, even with GC "disabled") never
# would have freed these on its own — they needed the cyclic collector.


# --- Part 3: peek at what the collector is actually tracking --------------

print("\n6. First 5 tracked object types:")
for obj in gc.get_objects()[:5]:
    print("   ", type(obj))

print("\n7. Collection thresholds (gen0, gen1, gen2):", gc.get_threshold())
print("   Current counts (gen0, gen1, gen2):", gc.get_count())
# Thresholds control how many allocations trigger an automatic collection
# pass per generation. Generation 0 is checked most often (cheap, young
# objects); generation 2 least often (expensive, long-lived objects).


# --- Part 4: try it yourself ----------------------------------------------
# 1. Add a __del__ method to Node that prints "Node deleted: <name>".
#    Re-run the cycle example. Notice __del__ still fires correctly on
#    cyclic objects in modern Python (3.4+) — this used to NOT be
#    guaranteed in older versions, which is why __del__ + cycles has
#    a bad historical reputation.
#
# 2. Replace b.next = a with a weakref.ref(a) (import weakref first).
#    Re-run gc.collect() — notice you no longer need it. Why? Because
#    a weakref doesn't count toward the reference count at all, so the
#    cycle never forms in the first place.
