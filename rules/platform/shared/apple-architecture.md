## Architecture (A)

- **A-1** Screens display, view models prepare display state, only services hold business rules, repositories access data; the UI never touches storage. [check: scan:layer-import, review]
- **A-2** Dependencies go one way with no cycles; features depend on domain abstractions, never on each other or concrete data code. [check: scan:import-matrix]
- **A-3** One job per type or module; split rather than add a second. Size warnings are hints, not failures. [check: advisory:type-size, review]
- **A-4** Add a protocol only for a second implementation, a test fake or a module boundary. [check: review]
- **A-5** Use the platform's standard navigation, state and dependency wiring, never a home-made framework. [check: scan:native-pattern]
- **A-6** Names use standard terms and never claim a role the code does not play (a ViewModel prepares display state, a Repository accesses data, a Screen is navigable). [check: review]
- **A-7** Use the platform feature for window chrome, toolbar, navigation, tab bars, modals, alerts, search, sidebars, split views, menus, lists, progress and pickers; a rebuild from native parts (custom title bar, overlay modal, own search field, overridden focus) is a substitute and needs a deviation the plan approved. Each UI plan item names the native feature it uses. [check: scan:native-pattern]
