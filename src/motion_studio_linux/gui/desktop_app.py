"""Desktop GUI shell for Motion Studio Linux workflows."""

from __future__ import annotations

import json
import queue
import threading
import traceback
from collections.abc import Callable
from pathlib import Path
import tkinter as tk
from tkinter import BooleanVar, StringVar, Tk, filedialog, messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from typing import Any

from motion_studio_linux.gui.desktop_controller import DesktopShellController
from motion_studio_linux.gui.facade import ServiceGuiFacade
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
        self.recipe_var = StringVar(value="smoke_v1")
        self.test_report_dir_var = StringVar(value="reports")
        self.test_csv_var = BooleanVar(value=True)
        self.reports_dir_var = StringVar(value="reports")
        self.status_var = StringVar(value="idle")

        self._build_ui()
        self._update_status()
        self._refresh_ports()
        self._refresh_reports()
        self.root.after(100, self._poll_results)

    def _build_ui(self) -> None:
        root_frame = ttk.Frame(self.root, padding=10)
        root_frame.pack(fill="both", expand=True)
        root_frame.columnconfigure(0, weight=1)
        root_frame.rowconfigure(1, weight=1)
        root_frame.rowconfigure(2, weight=0)

        header = ttk.Frame(root_frame)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.columnconfigure(7, weight=1)

        ttk.Label(header, text="Port").grid(row=0, column=0, padx=(0, 6))
        self.port_combo = ttk.Combobox(header, textvariable=self.port_var, state="readonly", width=28)
        self.port_combo.grid(row=0, column=1, padx=(0, 12))
        ttk.Button(header, text="Refresh Ports", command=self._refresh_ports).grid(row=0, column=2, padx=(0, 12))

        ttk.Label(header, text="Address").grid(row=0, column=3, padx=(0, 6))
        ttk.Entry(header, textvariable=self.address_var, width=10).grid(row=0, column=4, padx=(0, 12))
        ttk.Button(header, text="Info", command=self._on_info).grid(row=0, column=5, padx=(0, 6))
        ttk.Button(header, text="Dump", command=self._on_dump).grid(row=0, column=6, padx=(0, 6))

        self.notebook = ttk.Notebook(root_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew")

        self._build_tab_device()
        self._build_tab_config()
        self._build_tab_test()
        self._build_tab_reports()

        footer = ttk.Frame(root_frame)
        footer.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        footer.columnconfigure(0, weight=1)
        ttk.Label(footer, textvariable=self.status_var, anchor="w").grid(row=0, column=0, sticky="ew")

    def _build_tab_device(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Device")
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        ttk.Label(
            tab,
            text="Device/Session Overview\nUse this panel to validate port/address and firmware before other actions.",
            justify="left",
        ).grid(row=0, column=0, sticky="w")

        self.device_text = ScrolledText(tab, height=20)
        self.device_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

    def _build_tab_config(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Config + Flash")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(6, weight=1)
        tab.rowconfigure(8, weight=1)

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

        buttons = ttk.Frame(tab)
        buttons.grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 3))
        ttk.Button(buttons, text="Dump Config", command=self._on_dump).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Load JSON", command=self._load_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Save JSON", command=self._save_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Format JSON", command=self._format_config_editor).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Flash Config", command=self._on_flash).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Flash Editor", command=self._flash_from_editor).pack(side="left")

        ttk.Label(tab, text="Config Editor (JSON)").grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))
        self.config_editor = ScrolledText(tab, height=12)
        self.config_editor.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

        ttk.Label(tab, text="Workflow Output").grid(row=7, column=0, columnspan=3, sticky="w", pady=(10, 0))
        self.config_text = ScrolledText(tab, height=12)
        self.config_text.grid(row=8, column=0, columnspan=3, sticky="nsew", pady=(6, 0))

    def _build_tab_test(self) -> None:
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Test")
        tab.columnconfigure(1, weight=1)
        tab.rowconfigure(4, weight=1)

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

        self.test_text = ScrolledText(tab, height=16)
        self.test_text.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(10, 0))

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
        if command == "info":
            self._append_text(self.device_text, serialized)
        elif command in {"dump", "flash"}:
            self._append_text(self.config_text, serialized)
        elif command == "test":
            self._append_text(self.test_text, serialized)

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

    def _save_config_editor(self, *, show_message: bool = True) -> bool:
        path = self.config_path_var.get().strip()
        if not path:
            messagebox.showerror("Missing Config Path", "Provide a config file path first.")
            return False

        raw = self.config_editor.get("1.0", "end").strip()
        if not raw:
            messagebox.showerror("Missing Config JSON", "Config editor is empty.")
            return False

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", str(exc))
            return False
        if not isinstance(payload, dict):
            messagebox.showerror("Invalid JSON", "Config root must be a JSON object.")
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
        raw = self.config_editor.get("1.0", "end").strip()
        if not raw:
            return
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", str(exc))
            return
        formatted = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        self.config_editor.delete("1.0", "end")
        self.config_editor.insert("end", formatted)

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
