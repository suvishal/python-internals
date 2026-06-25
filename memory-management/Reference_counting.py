"""
reference_counting.py

Run this top to bottom and read the printed numbers as you go.
Before each print, try to predict the count yourself — that's the
exercise. The comments explain *why* each number is what it is,
not just what it is.

Remember: sys.getrefcount(x) always reports ONE HIGHER than the
"real" count, because passing x into getrefcount() as an argument
creates a temporary reference for the duration of that call.
"""

import sys

# --- Part 1: basic aliasing ---------------------------------------------

a = [1, 2, 3]
print("1. Initial ref count of a:", sys.getrefcount(a))
# Expect 2: one from 'a' itself, one temporary from getrefcount()'s own
# argument-passing.

b = a  # b is NOT a copy — it's another name for the same list object
print("2. After 'b = a':", sys.getrefcount(a))
# Expect 3: 'a', 'b', + the temporary getrefcount() reference.

c = a
print("3. After 'c = a':", sys.getrefcount(a))
# Expect 4: 'a', 'b', 'c', + temporary.

del b
print("4. After 'del b':", sys.getrefcount(a))
# Expect 3 again — deleting a NAME removes one reference, the object
# itself is untouched (and still alive, because 'a' and 'c' remain).


# --- Part 2: references through function calls --------------------------

def func(x):
    # Inside this function, the count includes:
    # 'a', 'c', the parameter 'x' (a new reference to the same object),
    # + getrefcount()'s own temporary reference.
    print("5. Inside function:", sys.getrefcount(x))


func(a)
print("6. Outside function (after func returns):", sys.getrefcount(a))
# Expect this to drop back down — once func() returns, its local frame
# (including the parameter 'x') is destroyed, removing that reference.
# This is the heap-vs-stack idea from notes.md in action: the function's
# stack frame disappears immediately, the heap object survives because
# 'a' and 'c' still point to it.

del c
print("7. After 'del c', only 'a' remains:", sys.getrefcount(a))
# Expect 2: 'a' + temporary. Back to where we started in step 1.

del a
# The list's ref count just hit 0. CPython deallocates it RIGHT NOW —
# not at some later GC pass. There is nothing left to print; the name
# 'a' no longer exists.
print("8. 'a' deleted — object is freed immediately (no cycle, no GC needed)")


# --- Part 3: try it yourself ---------------------------------------------
# Uncomment and predict the output BEFORE running:
#
# x = {}
# print(sys.getrefcount(x))      # baseline
# y = x
# z = x
# print(sys.getrefcount(x))      # how much did it change, and why?
# del y
# print(sys.getrefcount(x))      # predict this one before running it
