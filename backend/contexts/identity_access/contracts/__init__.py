"""Public contracts for Identity Access.

Import the specific contract submodule you need
(e.g. ``from contexts.identity_access.contracts.access_control import ...``).

This package intentionally does not eagerly re-export its submodules: doing so
forced every submodule to load during package initialization and created an
import-ordering cycle (a submodule importing a sibling contract while the
package was still initializing left it partially defined). All consumers use
submodule imports, so the flattened re-exports were unused.
"""
