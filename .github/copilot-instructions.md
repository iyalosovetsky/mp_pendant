# copilot-instructions for **mp_pendant**

This repository contains a MicroPython application that runs on an RP2040‑based
"smart pendant" for a GRBL‑HAL CNC controller.  There is no traditional build
system or unit tests; development consists of editing `.py` files on the host
and copying them to the board (Thonny, `mpremote`, `rshell`, etc.) followed by
resetting the Pico.  The device boots `main.py` and everything else is imported
from there.

## Big‑picture architecture

1. **`main.py`** – entry point.  Sets CPU clock, configures hardware (UART,
   pins, display via `nanoguilib`), instantiates a `GrblState` object, a
   rotary encoder, buttons, touchscreen and a `TermReader`.  Enters a tight
   loop that calls `st.p_RTLoop()` and handles terminal/keyboard input.
2. **`grblUartState.py`** – contains `GrblState` and `GrblParams`.  This class
   encapsulates all state coming from the CNC (M‑pos, W‑pos, MPG, WCS, status
   text, errors, alarms, etc.) and manages the UART conversation with GRBL.
   It uses a simple real‑time scheduler (`self.rt` dictionary) where each task
   has an `interval` expressed in **nanoseconds**.  `p_RTLoop()` iterates the
   enabled tasks and calls their `proc` callback.
3. **`gui.py`** – user‑interface logic built on top of the `nanoguilib`
   library (included as a subdirectory).  Most visual elements are configured
   in `_msg_conf` and drawn by `Gui`.  UI modes are tracked with
   `_ui_modes`/`_ui_mode` and there are helper objects such as `NeoLabelObj`.
4. **`template.py`** + `templates/` – simple plug‑in system for G‑code
   generators.  `Template` loads a Python module from the `/templates` folder
   and expects it to provide an `App` class with `getGcode()`/`getIcon()`.
5. **Peripheral helpers** –
   * `rotary.py` / `rotaryIRQ.py` – standard MicroPython rotary encoder
     implementation (the latter is Pico‑specific).  `main.py` wires a
     `rotary_listener0` callback from `GrblState`.
   * `button.py` – debounce/long‑press helper for GPIO buttons.
   * `TermReader.py` – non‑blocking terminal reader for the REPL UART.
   * `ns2009.py` – touch‑screen driver.
   * `SmartKbd.py` – on‑screen keyboard.

The `old/` directory holds legacy examples – ignore for new development.

## Coding conventions and gotchas

* **MicroPython constraints** – memory is tight, so many classes use
  `__slots__`.  Avoid large data structures and `import` only what's needed.
* **Time units** – all scheduling intervals use `time.time_ns()` and compare
  against nanosecond constants defined at top of `grblUartState.py` and
  `gui.py`.  Don’t mix with `ticks_ms()` except where the helper classes
  (e.g. `Button`) explicitly do so.
* **UI layout** – see `_msg_conf` in `gui.py` for how labels are positioned and
  coloured; updating the display simply sets `self.neo_refresh = True`.
* **Global state** – there is a single `objgrblState` global set in
  `GrblState.__init__`; the UART interrupt handler (`uart_callback`) writes to
  `rx_buffer` and calls `objgrblState.procUartInByte()`.
* **Templates** – filenames in `templates/` must be lowercase and the module
  should define `class App` with an `__slots__` list for parameters.
* **Debugging** – use `print()` extensively; no logger infrastructure exists.
  The `DEBUG` global constant toggles some verbosity.
* **Hardware pins** – hard‑coded in `main.py`.  To support a different board
  change the `UART(0, ..., tx=0, rx=1)`, rotary pins, button pins, etc.

## Developer workflow

1. Edit Python files locally.
2. Upload changed files to the Pico (Thonny/`mpremote cp`/`rshell`/etc.).
3. Press `CTRL‑D` or power‑cycle the board to restart the script.
4. Observe output on the screen or via the serial REPL for errors.

There is no automated test suite; manual smoke‑testing on hardware is the only
verification.  Some helper scripts (e.g. in `old/`) can be used for
experimentation.

## External dependencies

* Native MicroPython modules (`machine`, `time`, `micropython`,
  `uos`, `select`).
* `nanoguilib` – bundled in the workspace.  Do not modify the library unless
  you know what you’re doing; treat it as a third‑party dependency.
* GRBL‑HAL CNC firmware on the other end of the UART link (not part of this
  repo).  The pendant speaks plain GRBL text commands and parses responses.

## Common tasks for GitHub Copilot agents

* **Adding a new UI element** – modify `_msg_conf` or create a new
  `NeoLabelObj`, update `Gui.draw_screen()` accordingly and mark
  `neo_refresh` to force a redraw.
* **Implementing a new GRBL command** – add a method to `GrblState` that
  pushes a string onto `self.grblCmd2send` and adjust `popCmd2grbl()`.
* **Changing rotary behaviour** – edit `GrblState.rotary_listener0()` or the
  `rotate_obj` setup in `main.py`.
* **Creating a template macro** – add a file in `templates/` with a
  lowercase name and an `App` class; use `Template` from GUI to load it.

> **Note:** Copilot answers should reference actual file names (e.g.
> `grblUartState.py`, `gui.py`), show example snippets, and beware that the
> code runs on MicroPython with very limited resources.

Please review these instructions and let me know if any important patterns or
workflows are missing or unclear.