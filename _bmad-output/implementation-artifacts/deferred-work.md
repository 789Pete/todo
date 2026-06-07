# Deferred Work

## Deferred from: code review of 4.2.story.md (2026-06-06)

- **SW fetch handler no static-only scope guard** (`static/js/service-worker.js`): The fetch handler intercepts all GET requests with no path restriction. Currently network-first so no data corruption, but could cache dynamic endpoints if they are ever matched. Accepted per story 4.2 risk notes; revisit if expanding SW caching strategy.
- **`_apply_tag_filter` accepts foreign-user tag UUIDs** (`apps/tasks/views.py`): Passing a tag UUID owned by another user results in silent zero-result filtering rather than an error. No data leak (queryset is user-scoped). Pre-existing behavior from earlier stories.
- **Suggest dropdown doesn't close on `touchstart` outside on iOS Safari** (`static/js/keyboard-shortcuts.js`): `document.addEventListener('click', ...)` does not fire on touch taps on non-focusable elements in iOS Safari. Dropdown may persist after tapping elsewhere on mobile. Acceptable for MVP.
- **Story 4.2 AC1: FAB test missing `aria-label` assertion** (`apps/tasks/tests/test_views.py`): Test verifies `task-create` URL and `d-md-none` in rendered content but not `aria-label="New Task"`. Very minor gap; functional behavior is correct.
