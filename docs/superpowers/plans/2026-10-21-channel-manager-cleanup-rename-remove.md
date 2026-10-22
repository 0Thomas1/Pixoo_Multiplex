# ChannelManager Cleanup: Rename Members and Remove Dead Code

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename ChannelManager's internal data members for clarity and remove unused/dead members (`urgent_queue`, `interrupt_event`, `sleep_interruptible`) and the `urgent_queue_size` field from the public status API, while keeping `self.pixoo` as an instance attribute (do not convert it to a local).

**Architecture:** Make two commits. Commit 1 is pure rename (no behavior/API change). Commit 2 removes dead paths and updates API surface (drops `urgent_queue_size` from GET /status), updates router/docs/tests accordingly. All renames are mechanical and must keep behavior identical.

**Tech Stack:** Python 3.x, FastAPI, asyncio, Pixoo library

**Spec:** User request: "rename some datamembers in channel manager and remove unused data memeber" (approved approach B).

## Global Constraints

- Keep `self.pixoo` as an instance attribute (explicitly requested).
- No backwards-compat aliases for renamed members.
- Remove `urgent_queue`, `interrupt_event`, and `sleep_interruptible()`. Replace all uses with `await asyncio.sleep(duration)`.
- `GET /api/v1/status` must no longer return `urgent_queue_size`.
- Update docs/tests to match (remove references to dead code/API).
- Follow existing code style (tabs in src/ as per AGENTS.md).

## Review Focus

- [ ] **Status API change:** After commit 2, `GET /api/v1/status` must not include `urgent_queue_size`; tests and docs must be updated. (Covers API contract change.)
- [ ] **Worker behavior unchanged by renames:** Commit 1 must be pure rename with identical behavior; no logic changes.
- [ ] **Dead code fully removed:** No references to `urgent_queue`, `interrupt_event`, or `sleep_interruptible` remain in src/ after commit 2.
- [ ] **Queue semantics preserved:** Carousel/manual behavior must remain the same after renames/removals.
- [ ] **Admin flow preserved:** `admin_commands` rename must not affect admin command detection/enforcement.

---
### Task 1: Rename ChannelManager members (pure rename, no behavior change)

**Files:**
- Modify: `src/services/channel_manager.py`
- Modify: `src/router.py` (uses `manager.channels`, `manager.channel_0` in status; update names)

**Interfaces:**
- Consumes: none (internal)
- Produces: renamed members on ChannelManager:
  - `channel_0` -> `carousel`
  - `mode` -> `display_mode`
  - `manual_app` -> `manual_app_id`
  - `commands` -> `command_map`
  - `admin_commands` -> `admin_command_names`

- [ ] **Step 1: Update ChannelManager internal names**

Edit `src/services/channel_manager.py`:
- In `__init__`: `self.commands = ...` -> `self.command_map = ...`; `self.admin_commands = set(DEVICE_CONTROL_COMMANDS)` -> `self.admin_command_names = set(DEVICE_CONTROL_COMMANDS)`; `self.channel_0 = []` -> `self.carousel = []`; `self.mode = "manual"` -> `self.display_mode = "manual"`; `self.manual_app = None` -> `self.manual_app_id = None`. Keep `self.pixoo = Pixoo(pixoo_ip)`, `self.channels = {}`, `self.urgent_queue`, `self.interrupt_event` unchanged in this task.
- In `worker_loop`: replace `self.mode`, `self.manual_app` with `self.display_mode`, `self.manual_app_id`; replace `self.channel_0` with `self.carousel`.
- In `enqueue_request`: replace `self.admin_commands` with `self.admin_command_names`, `self.channel_0` with `self.carousel`.
- In `switch_channel`: replace `self.channel_0` with `self.carousel`, `self.mode` with `self.display_mode`, `self.manual_app` with `self.manual_app_id`.
- In `set_mode`: replace `self.mode` with `self.display_mode`, `self.manual_app` with `self.manual_app_id`.
- In `send_to_pixoo`: replace `self.commands` with `self.command_map`.

- [ ] **Step 2: Update router to use renamed members (if accessed directly)**

Edit `src/router.py`:
- In `get_status`: `"channels": list(manager.channels.keys())`, `"carousel": manager.carousel` (was `manager.channel_0`).

- [ ] **Step 3: Verify no other references to old names in src**

Run: `grep -rn "\bchannel_0\b\|\bself\.mode\b\|\bself\.manual_app\b\|\bself\.commands\b\|\bself\.admin_commands\b" src/`
Expected: no matches (all renamed)

- [ ] **Step 4: Commit**

```bash
git add src/services/channel_manager.py src/router.py
git commit -m "refactor(channel-manager): rename members for clarity (carousel/display_mode/manual_app_id/command_map/admin_command_names)"
```

### Task 2: Remove dead code and drop urgent_queue_size from API

**Files:**
- Modify: `src/services/channel_manager.py`
- Modify: `src/router.py`
- Modify: `tests/test_endpoints.py`
- Modify: `docs/api.md`
- Modify: `docs/architecture.md`
- Modify: `README.md` (remove references to urgent_queue/dead code where easy)
- Modify: `AGENTS.md` (update "Unfinished plumbing" / relevant notes)

**Interfaces:**
- Consumes: renamed members from Task 1
- Produces: ChannelManager without `urgent_queue`, `interrupt_event`, `sleep_interruptible()`; GET /status without `urgent_queue_size`

- [ ] **Step 1: Remove dead members and urgent branch from ChannelManager**

Edit `src/services/channel_manager.py`:
- Remove `self.urgent_queue = asyncio.Queue()` and `self.interrupt_event = asyncio.Event()` from `__init__` (keep `self.pixoo`).
- In `worker_loop`: remove the urgent queue check block (lines checking `urgent_queue`), remove `interruptable` parameter usage. Replace all `await self.sleep_interruptible(request.duration, interruptable=...)` with `await asyncio.sleep(request.duration)`. Remove the `sleep_interruptible` method entirely.
- Ensure logic flow is: if display_mode == "manual" and manual_app_id: process that app queue else if carousel not empty: round-robin; else sleep.

- [ ] **Step 2: Update router status endpoint**

Edit `src/router.py`:
- In `get_status`: remove `"urgent_queue_size": manager.urgent_queue.qsize()` from return dict.

- [ ] **Step 3: Update tests**

Edit `tests/test_endpoints.py`:
- Remove assertion `assert "urgent_queue_size" in data` from `test_status_endpoint()`.

- [ ] **Step 4: Update docs**

Edit `docs/api.md`:
- In GET /api/v1/status response example, remove `"urgent_queue_size": 0`.
- Remove row for `urgent_queue_size` from status fields table.
- Update any other references if present.

Edit `docs/architecture.md`:
- Remove urgent_queue box from ASCII diagram and update diagram text.
- Update State Model table: remove rows for `urgent_queue` and `interrupt_event`.
- Update Worker Loop pseudocode to remove urgent branch; replace `sleep_interruptible(...)` with `sleep(...)`.
- Remove "Urgent Queue — Dead Code" and "Interrupt Event — Dead Code" sections (or rewrite).
- Update API Endpoints table description if it mentions urgent queue size.

Edit `README.md`:
- Remove references to `urgent_queue_size` in status examples and text.
- Remove mentions of urgent queue dead code / interrupt_event where present.

Edit `AGENTS.md`:
- Update "Architecture" bullets to remove `urgent_queue` and `interrupt_event` (and update names to new names if desired).
- Update "Unfinished plumbing" section to remove bullets about urgent_queue/interrupt_event; adjust notes about default mode/manual_app_id if needed (behavior unchanged).

- [ ] **Step 5: Verify no references to removed members remain**

Run: `grep -rn "urgent_queue\|interrupt_event\|sleep_interruptible\|urgent_queue_size" src/ tests/ docs/ README.md AGENTS.md`
Expected: no matches

- [ ] **Step 6: Smoke check**

Run: `python -c "from src.main import app; print('ok')"`
Expected: imports successfully

- [ ] **Step 7: Commit**

```bash
git add src/services/channel_manager.py src/router.py tests/test_endpoints.py docs/api.md docs/architecture.md README.md AGENTS.md
git commit -m "refactor(channel-manager): remove urgent_queue/interrupt_event/sleep_interruptible and drop urgent_queue_size from status"
```
