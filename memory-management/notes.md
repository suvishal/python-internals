Python abstracts memory management from the programmer, but understanding what happens under the hood is extremely useful for writing efficient and scalable applications.

Python primarily uses:

Object Model
Reference Counting
Garbage Collection
Memory Allocation Strategies

Understanding these concepts helps in:

Debugging memory leaks
Writing performant backend services
Understanding mutability and object sharing
Optimizing long-running applications


# 1. Object Model

Everything in Python is an object.

Examples:

x = 10
name = "Suvishal"
numbers = [1, 2, 3]

All of the above are objects stored in memory.

Every object in Python contains:

*Object Type*

Determines what operations are allowed.

Example:

    type(10)
    #int

*Object Value*

x = 10

The value is 10.

*Reference Count*

Keeps track of how many references point to an object.

*Object Identity*

id(x)

Returns the memory address (implementation-dependent).

Visual Representation
--------------------



      x
      |
      v
      +----------------+
      | Object: 10      |
      | Type: int       |
      | Ref Count: 1    |
      +----------------+

# 2. Reference Counting


Python uses reference counting as its primary memory management mechanism.

Every object keeps track of:

How many references point to me?

When the reference count reaches:

0

The object becomes eligible for deallocation.

Example
--
    a = [1, 2, 3]
    
    b = a

Visual:
    
    a ----\
           > [1,2,3]
    b ----/

Reference Count:

2

Delete one reference:

del a

Reference Count:

1

Delete second reference:

del b

Reference Count:

0

Object can now be freed.

# 3. Garbage Collection

Reference counting cannot handle:

Circular References

Example:

    a = {}
    b = {}
    
    a["b"] = b
    b["a"] = a

Visual:

    a <----> b

Even after:

    del a
    del b

Objects still reference each other.

Reference counts never become zero.

This is why Python uses:

Cyclic Garbage Collector

Implemented using the:

gc

module.

# 4. Circular References

Example:

class Node:
    pass

a = Node()
b = Node()

a.next = b
b.next = a

Visual:

    a -----> b
    ^         |
    |         |
    +---------+

Deleting:

del a
del b

does not immediately free memory.

The garbage collector eventually detects and removes these unreachable cycles.

# 5. Memory Allocation

Python uses:

Private Heap

All Python objects are stored inside:

Python Private Heap

Memory management is handled by:

PyMalloc

Optimized allocator for small objects.

Benefits:

Faster allocation
Reduced fragmentation
Better cache locality
Small Object Allocation

Objects like:

1
[]
{}
()

are allocated using object pools and arenas.

This reduces calls to the operating system allocator.

# 6. Stack vs Heap
Stack

Stores:

Function calls
Local references
Execution frames

Example:

    def add():
        x = 10

The reference:
    
    x

lives in the stack frame.

Heap

Stores:

Actual objects.

Example:

    x = [1,2,3]

Visual:

Stack:
x

Heap:
[1,2,3]

The variable:

x

stores a reference.

The list object itself lives on the heap.
