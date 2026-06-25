01 — Memory Management in Python
----

Why this matters

Python hides memory management from you. That's great for productivity and terrible for debugging — when a backend service slowly eats RAM over three days in production, "Python handles it automatically" stops being comforting. This folder covers the two mechanisms that actually run under the hood:


Reference counting — Python's primary, always-on mechanism.
Cyclic garbage collection — a backup mechanism for the one case reference counting can't solve.


If you can explain why Python needs both (not just that it has both), you're already ahead of most people who can write Python but have never had to debug a memory leak in it.


1. Every object carries a reference count

When you write:

pythonx = 10

Python doesn't create a box called x containing 10. It creates an integer object 10 somewhere in memory, and x is a name that points to it. That object internally tracks one number: how many things currently point to it.

pythona = [1, 2, 3]   # the list object's ref count → 1
b = a           # same list, another name pointing to it → ref count 2
c = a           # → ref count 3

a, b, and c are not three lists. They are three names pointing at one list. This is the single most important mental model in this whole topic — Python variables are labels, not containers.

pythondel b   # ref count → 2
del c   # ref count → 1
del a   # ref count → 0 → object is freed immediately

The moment the count hits zero, CPython deallocates the object immediately — not on some future GC pass. This is why Python feels memory-efficient for ordinary code: cleanup is deterministic and instant, not "eventually, when the collector gets around to it" like in Java.


Check reference_counting.py for a script that prints these counts live, and notice the count is always 1 higher than you'd expect — that's explained below.



The gotcha: getrefcount() lies a little

pythonimport sys
a = [1, 2, 3]
print(sys.getrefcount(a))   # prints 2, not 1

Why 2, not 1? Because passing a into getrefcount() as an argument creates a temporary second reference for the duration of the call. This trips people up constantly — getrefcount() always overcounts by at least one. Don't trust the absolute number; trust the change in the number across operations.

Where this bites you in real code


Holding a reference to a large object in a list, cache, or closure longer than you think keeps it alive — getrefcount() going up unexpectedly is often how you discover an unintended reference.
A function parameter is a reference, not a copy. Passing a 2GB DataFrame into a function doesn't copy 2GB — but it does bump the ref count, so the original stays alive as long as the function frame does.



2. The case reference counting can't solve: cycles

Reference counting has exactly one blind spot: two objects that reference each other.

pythona = {}
b = {}
a["b"] = b
b["a"] = a

Now a's ref count is 2 (one from the name a, one from b["a"]), and b's ref count is 2 likewise. Run del a; del b — the names are gone, but the objects still hold references to each other. Ref count never drops to zero. Reference counting alone would leak this forever.

texta ──► b
▲     │
└─────┘

This is exactly why CPython ships a second, separate mechanism on top of reference counting.

How the cyclic collector actually works (briefly)

It doesn't scan everything — that would be too slow. Instead, Python tracks container objects (lists, dicts, objects with __dict__, etc. — things that can plausibly form cycles) in a separate list. Periodically, it walks that list, mentally "subtracts" all references that come from inside the tracked set, and whatever's left with a ref count of zero is a cycle with no external owner — safe to delete.

You can watch this happen:

pythonimport gc
gc.disable()      # turn off the automatic collector
# ... create cycles, watch memory grow ...
gc.collect()      # run it manually, see them get cleaned up


Check garbage_collection.py for exactly this experiment, with object counts before and after.



Why this matters more than it sounds


__del__ and cycles don't mix well historically. If a cyclic object defines __del__, older Python versions (pre-3.4) couldn't safely break the cycle, because they didn't know what order to call __del__ in. Python 3.4+ fixed this (PEP 442), but it's a classic interview/code-review red flag if you see __del__ on something that might form cycles.
weakref exists specifically to avoid creating cycles in the first place — e.g., a parent-child relationship where the child holds a "soft" reference back to the parent that doesn't count toward ref counting. Worth knowing the module exists even if you don't memorize the API.
Cyclic collection runs on its own schedule, triggered by allocation thresholds (gc.get_threshold()), not the instant a cycle forms. Between cycle creation and collection, that memory sits there. In a tight allocation loop, this is a real, measurable latency/memory spike — not theoretical.



3. Where the objects actually live: heap vs. stack

pythondef add():
    x = [1, 2, 3]


x (the name/reference) lives on the call stack, inside add()'s frame. When add() returns, the frame is popped, and that reference is gone instantly.
[1, 2, 3] (the object) lives on the heap, managed by Python's private memory pool — not the stack.


So when add() returns, the list's ref count drops by one (the stack reference disappeared). If nothing else points to it, that's when it actually gets freed — not because "the function ended," but because its ref count hit zero as a side effect of the function ending.

This distinction matters because it tells you exactly where leaks live: leaks are never a stack problem (stack frames always clean up correctly), they're always "something on the heap has a reference I forgot about."


4. Allocation strategy: why small objects are basically free

CPython doesn't ask the OS for memory every time you write x = 1. That would be brutally slow at the rate Python programs allocate. Instead:


All Python objects live in a private heap, managed entirely by the interpreter, never touched directly by the OS allocator for every little allocation.
pymalloc is a specialized allocator that pre-reserves chunks ("arenas") from the OS and slices them up for small objects (≤512 bytes — most ints, short strings, small tuples). This means most everyday allocations never hit a syscall at all.
Small integers (-5 to 256) and short strings are cached and reused by CPython — x = 5 and y = 5 often point to the literal same object, not a coincidence, an optimization (you can check with id(x) == id(y)).


This is why Python's GC reputation as "slow" is overstated for normal workloads: the expensive part isn't allocation, it's the cyclic collector's periodic full scans — which is exactly why long-running services with lots of object churn (e.g., per-request object creation in a web server) are the ones that actually need to think about this.


5. Tying it together: a debugging mental model

When someone hands you a Python service with a memory leak, the diagnostic order is:


Is something just holding a reference longer than intended? (Most common — a global cache, a list that only grows, a closure capturing more than it needs.) → Fixed by reference counting working correctly once you remove the stray reference.
Are there reference cycles with __del__ or weakref complications? → Needs gc.collect(), gc.get_objects(), or tools like objgraph to actually see the cycle.
Is it not a "leak" at all, just heap fragmentation from pymalloc — memory the OS sees as "still allocated to Python" even though Python itself isn't using it? → Usually only fixable by restructuring allocation patterns or accepting it (this is the case tracemalloc is best at distinguishing from the other two).


Most interview answers stop at "Python has garbage collection." The stronger answer is being able to say which of these three a given symptom points to.


Interview Questions (with the answer behind the answer)

Q: How does Python manage memory?
Reference counting is the primary mechanism — deterministic, immediate, on by default. The cyclic garbage collector is a secondary mechanism that only exists to catch reference cycles, which reference counting structurally cannot detect. Underneath both, CPython uses a private heap with pymalloc to make small-object allocation cheap.

Q: Why have garbage collection at all, if reference counting already runs?
Because two objects referencing each other never hit a ref count of zero on their own, even when nothing external points to them anymore. GC's only job is finding and breaking these unreachable cycles.

Q: What's the practical difference between stack and heap in Python?
Stack holds names (references) tied to function call frames — cleanup is automatic and immediate on return. Heap holds the actual objects — cleanup depends on ref count, not on any function returning. A leak is always a heap problem; the stack can't leak.

Q: If you suspect a memory leak in a long-running Python service, what's your first move?
Check for accidental reference retention first (caches, globals, closures) since that's both the most common cause and the easiest to confirm. Only reach for gc / objgraph / tracemalloc if that's ruled out — they're for the cyclic and fragmentation cases, which are rarer.


Production Relevance — concrete, not generic


Backend APIs: a per-request cache that never expires is reference retention, not a "GC problem" — gc.collect() won't fix it, because the references are real and intentional, just wrong.
Background workers / long-running processes: these are the workloads where the cyclic collector's periodic scan cost is actually felt — high object churn means more candidate objects tracked, more frequent collection passes.
ML/AI services: large tensors held by a reference inside a closure (e.g., a callback that captured the wrong scope) are a textbook reference-counting leak — tracemalloc will point at the exact allocation line.
Caching systems: this is precisely where weakref earns its keep — a cache that holds strong references keeps entries alive forever; one built on weakref lets entries die when nothing else needs them.


Tools, ranked by what they actually tell you:

ToolAnswerssys.getrefcount()"How many things point at this object right now?"gc.get_objects() / gc.collect()"Are there cycles, and can I force-clean them?"tracemalloc"Which line of code allocated this memory?"objgraph"What's the reference chain keeping this object alive?"

Knowing which tool answers which question is the difference between guessing and debugging.
