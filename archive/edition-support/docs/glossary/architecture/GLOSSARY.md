# Architecture

The deep-module vocabulary. codebase-dic is the source. Use these words for module design. Domain words for a product stay in that product's glossary, not here.

Do not invent a Chinese name for a term in this file, or for any MMW skill. Use the English name.

An adapter here sits at a seam. It is not the release manifest, whose filename happens to contain the letters adapter.

## Language

**module**:
Anything with an interface and an implementation. The word does not pick a size: a function, a class, a package, or a slice across tiers.
_Avoid_: unit, component, service, and any invented Chinese name.

**interface**:
Everything a caller must know to use the module correctly: the type signature, invariants, ordering, error modes, required configuration, and performance.
_Avoid_: API, signature, and any invented Chinese name.

**implementation**:
The code inside a module.
_Avoid_: any invented Chinese name.

**depth**:
Leverage at the interface: how much behaviour a caller can exercise per unit of interface they have to learn.
_Avoid_: any invented Chinese name.

**deep module**:
A module with a lot of behaviour behind a small interface.
_Avoid_: any invented Chinese name.

**shallow module**:
A module whose interface is nearly as complex as its implementation.
_Avoid_: any invented Chinese name.

**seam**:
A place where behaviour can change without an edit in that place. It is where a module's interface lives, and it is the public boundary you test at.
_Avoid_: boundary, and any invented Chinese name.

**internal seam**:
A seam private to a module's implementation, used by that module's own tests.
_Avoid_: any invented Chinese name.

**external seam**:
The seam at a module's interface, where callers and tests cross.
_Avoid_: any invented Chinese name.

**adapter**:
A concrete thing that satisfies an interface at a seam. The word names the slot it fills.
_Avoid_: any invented Chinese name.

**leverage**:
What callers get from depth: more capability per unit of interface they learn.
_Avoid_: any invented Chinese name.

**locality**:
What maintainers get from depth: change, bugs, knowledge, and verification sit in one place.
_Avoid_: any invented Chinese name.

**deletion test**:
The question of whether deleting a module makes complexity vanish, or makes that complexity reappear across callers.
_Avoid_: any invented Chinese name.

**pass-through**:
A module that fails the deletion test because deleting it makes complexity vanish.
_Avoid_: any invented Chinese name.

**sketch**:
The types, signatures, and module structure chosen before the code. codebase-design returns it.
_Avoid_: contract, and any invented Chinese name.

**contract**:
The promised behavior a caller or a test is entitled to rely on.
_Avoid_: any invented Chinese name.
