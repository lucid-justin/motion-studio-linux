"""Desktop GUI shell for Motion Studio Linux workflows."""

from __future__ import annotations

import json
import queue
import threading
import traceback
from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import BooleanVar, DoubleVar, IntVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from motion_studio_linux.gui.desktop_controller import DesktopShellController
from motion_studio_linux.gui.facade import ServiceGuiFacade
from motion_studio_linux.gui.setup_form import (
    SetupFormModel,
    config_payload_from_model,
    model_from_config_payload,
    unsupported_parameter_keys,
)
from motion_studio_linux.gui.state import AppState


class MotionStudioDesktopShell:
    """Tkinter shell that runs on top of backend service contracts."""

    def __init__(self, root: Tk, *, facade: ServiceGuiFacade | None = None) -> None:
        self.root = root
        self.controller = DesktopShellController(facade or ServiceGuiFacade())
        self._result_queue: queue.Queue[tuple[str, dict[str, Any], str | None]] = queue.Queue()

        self.root.title("Motion Studio Linux Shell")
        self.root.geometry("1120x760")
        self.root.minsize(960, 640)

        self.port_var = StringVar(value="")
        self.address_var = StringVar(value="0x80")
        self.dump_out_var = StringVar(value="config.json")
        self.config_path_var = StringVar(value="config.json")
        self.flash_report_dir_var = StringVar(value="reports")
        self.flash_verify_var = BooleanVar(value=True)
        self.setup_mode_var = StringVar(value="3")
        self.setup_use_unified_current_var = BooleanVar(value=True)
        self.setup_max_current_var = StringVar(value="12000")
        self.setup_max_current_m1_var = StringVar(value="")
        self.setup_max_current_m2_var = StringVar(value="")
        self.setup_form_status_var = StringVar(value="Form is in sync with supported fields only.")
        self.recipe_var = StringVar(value="smoke_v1")
        self.test_report_dir_var = StringVar(value="reports")
        self.test_csv_var = BooleanVar(value=True)
        self.pwm_duty_m1_var = IntVar(value=0)
        self.pwm_duty_m2_var = IntVar(value=0)
        self.pwm_runtime_s_var = DoubleVar(value=0.5)
        self.reports_dir_var = StringVar(value="reports")
        self.live_firmware_var = StringVar(value="-")
        self.live_battery_var = StringVar(value="-")
        self.live_logic_battery_var = StringVar(value="-")
        self.live_m1_current_var = StringVar(value="-")
        self.live_m2_current_var = StringVar(value="-")
        self.live_enc1_var = StringVar(value="-")
        self.live_enc2_var = StringVar(value="-")
        self.live_error_bits_var = StringVar(value="-")
        self.status_var = StringVar(value="idle")

        self._build_ui()
        self.setup_use_unified_current_var.trace_add("write", self._on_setup_toggle_current_mode)
        self._on_setup_toggle_current_mode()
        self.root.bind("<space>", self._on_space_stop)
        self._update_status()
        self._refresh_ports()
        self._refresh_reports()
        self.root.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(2, weight=1)
        root_frame.rowconfigure(3, weight=0)

        header = ttk.Frame(root_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(9, weight=1)

        ttk.Label(header, text="Port").grid(row=0, column=0, padx=(0, 6))
        self.port_combo = ttk.Combobox(header, textvariable=self.port_var, state="readonly", width=28)
        self.port_combo.grid(row=0, column=1, padx=(0, 12))
        ttk.Button(header, text="Refresh Ports", command=self._refresh_ports).grid(row=0, column=2, padx=(0, 12))

        ttk.Label(header, text="Address").grid(row=0, column=3, padx=(0, 6))
        ttk.Entry(header, textvariable=self.address_var, width=10).grid(row=0, column=4, padx=(0, 12))
        ttk.Button(header, text="Info", command=self._on_info).grid(row=0, column=5, padx=(0, 6))
        ttk.Button(header, text="Dump", command=self._on_dump).grid(row=0, column=6, padx=(0, 6))
        ttk.Button(header, text="Refresh Status", command=self._on_status_refresh).grid(row=0, column=7, padx=(0, 6))
        ttk.Button(header, text="STOP ALL", command=self._on_stop_all).grid(row=0, column=8, padx=(0, 6))

        live_strip = ttk.LabelFrame(root_frame, text="Live Status")
        live_strip.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for col in range(8):
            live_strip.columnconfigure(col, weight=1)
        self._add_live_value(live_strip, row=0, col=0, label="Firmware", variable=self.live_firmware_var)
        self._add_live_value(live_strip, row=0, col=1, label="Main Battery", variable=self.live_battery_var)
        self._add_live_value(live_strip, row=0, col=2, label="Logic Battery", variable=self.live_logic_battery_var)
        self._add_live_value(live_strip, row=0, col=3, label="M1 Current", variable=self.live_m1_current_var)
        self._add_live_value(live_strip, row=0, col=4, label="M2 Current", variable=self.live_m2_current_var)
        self._add_live_value(live_strip, row=0, col=5, label="Encoder1", variable=self.live_enc1_var)
        self._add_live_value(live_strip, row=0, col=6, label="Encoder2", variable=self.live_enc2_var)
        self._add_live_value(live_strip, row=0, col=7, label="Error Bits", variable=self.live_error_bits_var)

        self.notebook = ttk.Notebook(root_frame)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        self._build_tab_device()
        self._build_tab_config()
        self._build_tab_test()
        self._build_tab_reports()

        footer = ttk.Frame(root_frame)
        footer.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, anchor="w").grid(row=0, column=0, sticky="ew")

    def _add_live_value(self, parent: ttk.LabelFrame, *, row: int, col: int, label: str, variable: StringVar) -> None:
        group = ttk.Frame(parent, padding=(6, 3))
        group.grid(row=row, column=col, sticky="ew")
        ttk.Label(group, text=label).grid(row=0, column=0, sticky="w")
        ttk.Label(group, textvariable=variable).grid(row=1, column=0, sticky="w")

    def _build_tab_device(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Device")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        ttk.Label(
            tab,
            text=(
                "Device/Session Overview\n"
                "Match Motion Studio workflow: connect target, read status, then configure/test.\n"
                "Use Refresh Status for live values and STOP ALL for immediate halt."
            ),
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        actions = ttk.Frame(tab)
        actions.grid(row=1, column=0, sticky="w", pady=(10, 0))
        ttk.Button(actions, text="Refresh Status", command=self._on_status_refresh).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="STOP ALL", command=self._on_stop_all).pack(side="left", padx=(0, 8))
        ttk.Label(actions, text="Spacebar shortcut: STOP ALL").pack(side="left")

        self.device_text = ScrolledText(tab, height=20)
        self.device_text.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

    def _build_tab_config(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Config + Flash")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(9, weight=1)
        tab.rowconfigure(11, weight=1)

        ttk.Label(tab, text="Dump Output Path").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(tab, textvariable=self.dump_out_var).grid(row=0, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="Browse", command=self._choose_dump_out_path).grid(row=0, column=2, padx=6, pady=3)

        ttk.Label(tab, text="Flash Config Path").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(tab, textvariable=self.config_path_var).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="Browse", command=self._choose_config_path).grid(row=1, column=2, padx=6, pady=3)

        ttk.Label(tab, text="Flash Report Directory").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Entry(tab, textvariable=self.flash_report_dir_var).grid(row=2, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="Browse", command=self._choose_flash_report_dir).grid(row=2, column=2, padx=6, pady=3)

        ttk.Checkbutton(tab, text="Verify after flash (reload/readback)", variable=self.flash_verify_var).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=3,
        )

        setup_frame = ttk.LabelFrame(tab, text="Setup Forms (Motion Studio Style, Supported Fields)")
        setup_frame.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        for col in range(4):
            setup_frame.columnconfigure(col, weight=1)

        general = ttk.LabelFrame(setup_frame, text="General")
        general.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        ttk.Label(general, text="Mode").grid(row=0, column=0, sticky="w", padx=6, pady=(6, 2))
        ttk.Combobox(
            general,
            textvariable=self.setup_mode_var,
            values=("0", "1", "2", "3"),
            state="readonly",
            width=8,
        ).grid(row=1, column=0, sticky="w", padx=6, pady=(0, 6))
        ttk.Label(general, text="Packet serial motion enabled when mode=3").grid(
            row=2, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        serial = ttk.LabelFrame(setup_frame, text="Serial")
        serial.grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        ttk.Label(serial, text="Port and address are controlled in the header.").grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 2)
        )
        ttk.Label(serial, text="Schema v1 does not persist baud/address fields yet.").grid(
            row=1, column=0, sticky="w", padx=6, pady=(0, 6)
        )
        ttk.Label(serial, textvariable=self.port_var).grid(row=2, column=0, sticky="w", padx=6, pady=(0, 2))
        ttk.Label(serial, textvariable=self.address_var).grid(row=3, column=0, sticky="w", padx=6, pady=(0, 6))

        battery = ttk.LabelFrame(setup_frame, text="Battery / Current")
        battery.grid(row=0, column=2, sticky="nsew", padx=6, pady=6)
        ttk.Checkbutton(
            battery,
            text="Unified current limit",
            variable=self.setup_use_unified_current_var,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=6, pady=(6, 4))

        ttk.Label(battery, text="max_current").grid(row=1, column=0, sticky="w", padx=6, pady=2)
        self.setup_max_current_entry = ttk.Entry(battery, textvariable=self.setup_max_current_var, width=10)
        self.setup_max_current_entry.grid(row=1, column=1, sticky="w", padx=6, pady=2)

        ttk.Label(battery, text="max_current_m1").grid(row=2, column=0, sticky="w", padx=6, pady=2)
        self.setup_max_current_m1_entry = ttk.Entry(
            battery, textvariable=self.setup_max_current_m1_var, width=10
        )
        self.setup_max_current_m1_entry.grid(row=2, column=1, sticky="w", padx=6, pady=2)

        ttk.Label(battery, text="max_current_m2").grid(row=3, column=0, sticky="w", padx=6, pady=2)
        self.setup_max_current_m2_entry = ttk.Entry(
            battery, textvariable=self.setup_max_current_m2_var, width=10
        )
        self.setup_max_current_m2_entry.grid(row=3, column=1, sticky="w", padx=6, pady=(2, 6))

        rc_inputs = ttk.LabelFrame(setup_frame, text="RC / Inputs")
        rc_inputs.grid(row=0, column=3, sticky="nsew", padx=6, pady=6)
        ttk.Label(rc_inputs, text="RC/PWM mapping is planned for expanded schema").grid(
            row=0, column=0, sticky="w", padx=6, pady=(6, 2)
        )
        ttk.Label(rc_inputs, text="Use JSON editor for unsupported keys.").grid(
            row=1, column=0, sticky="w", padx=6, pady=(0, 6)
        )

        ttk.Label(tab, textvariable=self.setup_form_status_var).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

        button_row_1 = ttk.Frame(tab)
        button_row_1.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 3))
        ttk.Button(button_row_1, text="Dump Config", command=self._on_dump).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_1, text="Load JSON", command=self._load_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_1, text="Load Form from JSON", command=self._load_setup_form_from_editor).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(button_row_1, text="Apply Form to JSON", command=self._apply_setup_form_to_editor).pack(
            side="left", padx=(0, 8)
        )

        button_row_2 = ttk.Frame(tab)
        button_row_2.grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 3))
        ttk.Button(button_row_2, text="Save JSON", command=self._save_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_2, text="Format JSON", command=self._format_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_2, text="Flash Config", command=self._on_flash).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_2, text="Flash Editor", command=self._flash_from_editor).pack(side="left", padx=(0, 8))
        ttk.Button(button_row_2, text="Flash Form", command=self._flash_setup_form).pack(side="left")

        ttk.Label(tab, text="Config Editor (JSON)").grid(row=8, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.config_editor = ScrolledText(tab, height=12)
        self.config_editor.grid(row=9, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

        ttk.Label(tab, text="Workflow Output").grid(row=10, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.config_text = ScrolledText(tab, height=12)
        self.config_text.grid(row=11, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

    def _build_tab_test(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Test")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(7, weight=1)

        ttk.Label(tab, text="Recipe").grid(row=0, column=0, sticky="w", pady=3)
        ttk.Entry(tab, textvariable=self.recipe_var).grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(tab, text="Test Report Directory").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Entry(tab, textvariable=self.test_report_dir_var).grid(row=1, column=1, sticky="ew", pady=3)
        ttk.Button(tab, text="Browse", command=self._choose_test_report_dir).grid(row=1, column=2, padx=6, pady=3)

        ttk.Checkbutton(tab, text="Write telemetry CSV", variable=self.test_csv_var).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=3,
        )
        ttk.Button(tab, text="Run Test", command=self._on_test).grid(row=3, column=0, sticky="w", pady=(8, 3))

        pwm_group = ttk.LabelFrame(tab, text="Manual PWM Pulse (Safety Capped)")
        pwm_group.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        pwm_group.columnconfigure(1, weight=1)
        pwm_group.columnconfigure(3, weight=1)

        ttk.Label(pwm_group, text="Duty M1 (-100..100)").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        ttk.Scale(
            pwm_group,
            from_=-100,
            to=100,
            variable=self.pwm_duty_m1_var,
            orient="horizontal",
        ).grid(row=0, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(pwm_group, textvariable=self.pwm_duty_m1_var).grid(row=0, column=2, sticky="w", padx=6, pady=4)

        ttk.Label(pwm_group, text="Duty M2 (-100..100)").grid(row=1, column=0, sticky="w", padx=6, pady=4)
        ttk.Scale(
            pwm_group,
            from_=-100,
            to=100,
            variable=self.pwm_duty_m2_var,
            orient="horizontal",
        ).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
        ttk.Label(pwm_group, textvariable=self.pwm_duty_m2_var).grid(row=1, column=2, sticky="w", padx=6, pady=4)

        ttk.Label(pwm_group, text="Pulse Runtime (s, <=2.0)").grid(row=2, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(pwm_group, textvariable=self.pwm_runtime_s_var, width=10).grid(
            row=2,
            column=1,
            sticky="w",
            padx=6,
            pady=4,
        )
        ttk.Button(pwm_group, text="Run PWM Pulse", command=self._on_pwm_pulse).grid(
            row=2,
            column=2,
            sticky="w",
            padx=6,
            pady=4,
        )
        ttk.Button(pwm_group, text="STOP ALL", command=self._on_stop_all).grid(
            row=2,
            column=3,
            sticky="w",
            padx=6,
            pady=4,
        )

        ttk.Label(tab, text="Workflow Output").grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.test_text = ScrolledText(tab, height=16)
        self.test_text.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

    def _build_tab_reports(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Reports")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(1, weight=1)
        tab.rowconfigure(2, weight=2)

        ttk.Label(tab, text="Reports Directory").grid(row=0, column=0, sticky="w")
        ttk.Entry(tab, textvariable=self.reports_dir_var).grid(row=0, column=1, sticky="ew")
        ttk.Button(tab, text="Browse", command=self._choose_reports_dir).grid(row=0, column=2, padx=6)
        ttk.Button(tab, text="Refresh", command=self._refresh_reports).grid(row=0, column=3)

        list_frame = ttk.Frame(tab)
        list_frame.grid(row=1, column=0, columnspan=4, sticky="nsew", pady=(10, 0))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.report_list = tk.Listbox(list_frame, height=10)
        self.report_list.grid(row=0, column=0, sticky="nsew")
        self.report_list.bind("<<ListboxSelect>>", self._on_report_selected)

        list_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.report_list.yview)
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.report_list.configure(yscrollcommand=list_scroll.set)

        self.report_text = ScrolledText(tab, height=20)
        self.report_text.grid(row=2, column=0, columnspan=4, sticky="nsew", pady=(10, 0))

    @property
    def state(self) -> AppState:
        return self.controller.state

    def _append_text(self, widget: ScrolledText, text: str) -> None:
        widget.insert("end", text + "\n")
        widget.see("end")

    def _select_target(self) -> tuple[str, int] | None:
        try:
            return self.controller.select_target(port=self.port_var.get(), address_raw=self.address_var.get())
        except ValueError as exc:
            title = "Missing Port" if "port" in str(exc).lower() else "Invalid Address"
            messagebox.showerror(title, str(exc))
            return None

    def _run_async(self, command: str, worker: Callable[[], dict[str, Any]]) -> None:
        self.controller.mark_job_started(command=command, message=f"Running {command}")
        self._update_status()

        def target() -> None:
            traceback_text: str | None = None
            try:
                result = worker()
            except Exception as exc:  # noqa: BLE001
                traceback_text = traceback.format_exc()
                result = {
                    "ok": False,
                    "error": {"code": "gui_unhandled_exception", "message": str(exc), "details": {}},
                }
            self._result_queue.put((command, result, traceback_text))

        threading.Thread(target=target, daemon=True).start()

    def _poll_results(self) -> None:
        try:
            while True:
                command, payload, traceback_text = self._result_queue.get_nowait()
                self.controller.mark_job_result(command=command, payload=payload)
                if traceback_text:
                    self._append_text(self.device_text, traceback_text)
                self._render_command_result(command, payload)
                self._update_status()
        except queue.Empty:
            pass
        self.root.after(100, self._poll_results)

    def _update_status(self) -> None:
        current = self.state.job
        command = current.active_command or "-"
        msg = current.message or "-"
        self.status_var.set(f"job={current.status} command={command} message={msg}")

    def _render_command_result(self, command: str, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        if command in {"info", "status", "stop_all"}:
            self._append_text(self.device_text, serialized)
        elif command in {"dump", "flash"}:
            self._append_text(self.config_text, serialized)
        elif command in {"test", "pwm_pulse"}:
            self._append_text(self.test_text, serialized)

        if bool(payload.get("ok")):
            self._update_live_status(payload)

        if command == "dump" and bool(payload.get("ok")):
            out_path = payload.get("out_path")
            if out_path is not None:
                self.config_path_var.set(str(out_path))
                self._load_config_editor()

        report_value = payload.get("report")
        if report_value is not None:
            report_path = Path(str(report_value))
            self.reports_dir_var.set(str(report_path.parent))
            self._refresh_reports()

    def _update_live_status(self, payload: dict[str, Any]) -> None:
        firmware = payload.get("firmware")
        if isinstance(firmware, str) and firmware.strip():
            self.live_firmware_var.set(firmware.strip())

        telemetry = payload.get("telemetry")
        if not isinstance(telemetry, dict):
            return

        self.live_battery_var.set(_format_deci_volts(telemetry.get("battery_voltage")))
        self.live_logic_battery_var.set(_format_deci_volts(telemetry.get("logic_battery_voltage")))
        self.live_m1_current_var.set(_format_raw(telemetry.get("motor1_current")))
        self.live_m2_current_var.set(_format_raw(telemetry.get("motor2_current")))
        self.live_enc1_var.set(_format_raw(telemetry.get("encoder1")))
        self.live_enc2_var.set(_format_raw(telemetry.get("encoder2")))
        self.live_error_bits_var.set(_format_error_bits(telemetry.get("error_bits")))

    def _refresh_ports(self) -> None:
        ports = self.controller.refresh_ports()
        self.port_combo["values"] = ports
        if ports:
            if self.port_var.get() not in ports:
                self.port_var.set(ports[0])
        else:
            self.port_var.set("")
        self._append_text(self.device_text, json.dumps({"ports": list(ports)}, sort_keys=True))

    def _on_info(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        self._run_async("info", lambda: self.controller.run_info(port=port, address=address))

    def _on_status_refresh(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        self._run_async("status", lambda: self.controller.run_status(port=port, address=address))

    def _on_dump(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        out_path = self.dump_out_var.get().strip()
        if not out_path:
            messagebox.showerror("Missing Output Path", "Provide a dump output path.")
            return
        self._run_async(
            "dump",
            lambda: self.controller.run_dump(port=port, address=address, out_path=out_path),
        )

    def _on_flash(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        config_path = self.config_path_var.get().strip()
        report_dir = self.flash_report_dir_var.get().strip() or "reports"
        if not config_path:
            messagebox.showerror("Missing Config Path", "Provide a config file path.")
            return
        self._run_async(
            "flash",
            lambda: self.controller.run_flash(
                port=port,
                address=address,
                config_path=config_path,
                verify=bool(self.flash_verify_var.get()),
                report_dir=report_dir,
            ),
        )

    def _on_test(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        recipe = self.recipe_var.get().strip() or "smoke_v1"
        report_dir = self.test_report_dir_var.get().strip() or "reports"
        self._run_async(
            "test",
            lambda: self.controller.run_test(
                port=port,
                address=address,
                recipe=recipe,
                report_dir=report_dir,
                csv=bool(self.test_csv_var.get()),
            ),
        )

    def _on_pwm_pulse(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        runtime_s = float(self.pwm_runtime_s_var.get())
        self._run_async(
            "pwm_pulse",
            lambda: self.controller.run_pwm_pulse(
                port=port,
                address=address,
                duty_m1=int(self.pwm_duty_m1_var.get()),
                duty_m2=int(self.pwm_duty_m2_var.get()),
                runtime_s=runtime_s,
            ),
        )

    def _on_stop_all(self) -> None:
        target = self._select_target()
        if target is None:
            return
        port, address = target
        self._run_async("stop_all", lambda: self.controller.run_stop_all(port=port, address=address))

    def _on_space_stop(self, _event: object) -> None:
        self._on_stop_all()

    def _on_setup_toggle_current_mode(self, *_args: object) -> None:
        unified = bool(self.setup_use_unified_current_var.get())
        if unified:
            self.setup_max_current_entry.configure(state="normal")
            self.setup_max_current_m1_entry.configure(state="disabled")
            self.setup_max_current_m2_entry.configure(state="disabled")
        else:
            self.setup_max_current_entry.configure(state="disabled")
            self.setup_max_current_m1_entry.configure(state="normal")
            self.setup_max_current_m2_entry.configure(state="normal")

    def _load_setup_form_from_editor(self) -> None:
        self._try_sync_form_from_editor(show_feedback=True)

    def _try_sync_form_from_editor(self, *, show_feedback: bool) -> bool:
        payload = self._read_editor_payload()
        if payload is None:
            return False

        model = model_from_config_payload(payload)
        self._set_setup_form_model(model)

        unsupported = unsupported_parameter_keys(payload)
        if unsupported:
            msg = f"Loaded form with unsupported keys present: {', '.join(unsupported)}"
        else:
            msg = "Loaded form from JSON editor."
        self.setup_form_status_var.set(msg)
        if show_feedback:
            messagebox.showinfo("Setup Form", msg)
        return True

    def _apply_setup_form_to_editor(self) -> bool:
        model = self._read_setup_form_model()
        if model is None:
            return False

        payload = config_payload_from_model(model)
        self.config_editor.delete("1.0", "end")
        self.config_editor.insert("end", json.dumps(payload, indent=2, sort_keys=True) + "\n")
        self.setup_form_status_var.set("Applied setup form to JSON editor.")
        return True

    def _flash_setup_form(self) -> None:
        if not self._apply_setup_form_to_editor():
            return
        self._flash_from_editor()

    def _read_setup_form_model(self) -> SetupFormModel | None:
        mode_raw = self.setup_mode_var.get().strip()
        try:
            mode = int(mode_raw)
        except ValueError:
            messagebox.showerror("Invalid Mode", "Mode must be one of: 0, 1, 2, 3.")
            return None
        if mode not in {0, 1, 2, 3}:
            messagebox.showerror("Invalid Mode", "Mode must be one of: 0, 1, 2, 3.")
            return None

        unified = bool(self.setup_use_unified_current_var.get())
        if unified:
            max_current = self._parse_optional_non_negative_int(
                self.setup_max_current_var.get(),
                "max_current",
            )
            if max_current is None and self.setup_max_current_var.get().strip():
                return None
            return SetupFormModel(mode=mode, use_unified_current=True, max_current=max_current)

        max_current_m1 = self._parse_optional_non_negative_int(
            self.setup_max_current_m1_var.get(),
            "max_current_m1",
        )
        if max_current_m1 is None and self.setup_max_current_m1_var.get().strip():
            return None
        max_current_m2 = self._parse_optional_non_negative_int(
            self.setup_max_current_m2_var.get(),
            "max_current_m2",
        )
        if max_current_m2 is None and self.setup_max_current_m2_var.get().strip():
            return None

        return SetupFormModel(
            mode=mode,
            use_unified_current=False,
            max_current_m1=max_current_m1,
            max_current_m2=max_current_m2,
        )

    def _set_setup_form_model(self, model: SetupFormModel) -> None:
        self.setup_mode_var.set(str(model.mode if model.mode is not None else 3))
        self.setup_use_unified_current_var.set(bool(model.use_unified_current))
        self.setup_max_current_var.set("" if model.max_current is None else str(model.max_current))
        self.setup_max_current_m1_var.set("" if model.max_current_m1 is None else str(model.max_current_m1))
        self.setup_max_current_m2_var.set("" if model.max_current_m2 is None else str(model.max_current_m2))
        self._on_setup_toggle_current_mode()

    def _parse_optional_non_negative_int(self, raw: str, field_name: str) -> int | None:
        value = raw.strip()
        if not value:
            return None
        try:
            parsed = int(value)
        except ValueError:
            messagebox.showerror("Invalid Number", f"{field_name} must be an integer.")
            return None
        if parsed < 0:
            messagebox.showerror("Invalid Number", f"{field_name} must be >= 0.")
            return None
        return parsed

    def _read_editor_payload(self) -> dict[str, Any] | None:
        raw = self.config_editor.get("1.0", "end").strip()
        if not raw:
            messagebox.showerror("Missing Config JSON", "Config editor is empty.")
            return None
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", str(exc))
            return None
        if not isinstance(payload, dict):
            messagebox.showerror("Invalid JSON", "Config root must be a JSON object.")
            return None
        return payload

    def _load_config_editor(self) -> None:
        path = self.config_path_var.get().strip()
        if not path:
            messagebox.showerror("Missing Config Path", "Provide a config file path first.")
            return
        try:
            raw = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Load Failed", str(exc))
            return
        self.config_editor.delete("1.0", "end")
        self.config_editor.insert("end", raw)
        self._try_sync_form_from_editor(show_feedback=False)

    def _save_config_editor(self, *, show_message: bool = True) -> bool:
        path = self.config_path_var.get().strip()
        if not path:
            messagebox.showerror("Missing Config Path", "Provide a config file path first.")
            return False

        payload = self._read_editor_payload()
        if payload is None:
            return False

        normalized = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        try:
            Path(path).write_text(normalized, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Save Failed", str(exc))
            return False
        if show_message:
            messagebox.showinfo("Saved", f"Saved config JSON to {path}.")
        return True

    def _format_config_editor(self) -> None:
        if not self.config_editor.get("1.0", "end").strip():
            return
        payload = self._read_editor_payload()
        if payload is None:
            return
        formatted = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        self.config_editor.delete("1.0", "end")
        self.config_editor.insert("end", formatted)
        self._try_sync_form_from_editor(show_feedback=False)

    def _flash_from_editor(self) -> None:
        if not self._save_config_editor(show_message=False):
            return
        self._on_flash()

    def _refresh_reports(self) -> None:
        report_dir = Path(self.reports_dir_var.get().strip() or "reports")
        files = self.controller.list_reports(report_dir=report_dir)
        self.report_list.delete(0, "end")
        for file in files:
            self.report_list.insert("end", str(file))

    def _on_report_selected(self, _event: object) -> None:
        if not self.report_list.curselection():
            return
        index = self.report_list.curselection()[0]
        path = Path(str(self.report_list.get(index)))
        try:
            preview = self.controller.read_report_preview(path=path)
        except Exception as exc:  # noqa: BLE001
            preview = f"Failed to read report: {exc}"
        self.report_text.delete("1.0", "end")
        self.report_text.insert("end", preview)

    def _choose_dump_out_path(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Choose Dump Output",
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.dump_out_var.set(path)

    def _choose_config_path(self) -> None:
        path = filedialog.askopenfilename(
            title="Choose Config File",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if path:
            self.config_path_var.set(path)

    def _choose_flash_report_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose Flash Report Directory")
        if path:
            self.flash_report_dir_var.set(path)

    def _choose_test_report_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose Test Report Directory")
        if path:
            self.test_report_dir_var.set(path)

    def _choose_reports_dir(self) -> None:
        path = filedialog.askdirectory(title="Choose Reports Directory")
        if path:
            self.reports_dir_var.set(path)
            self._refresh_reports()


def _format_raw(value: object) -> str:
    if value is None:
        return "-"
    return str(value)


def _format_deci_volts(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return f"{float(value) / 10.0:.1f} V ({value})"
    return str(value)


def _format_error_bits(value: object) -> str:
    if isinstance(value, int):
        return f"0x{value:04X}"
    if value is None:
        return "-"
    return str(value)


def main() -> int:
    root = Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    MotionStudioDesktopShell(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
