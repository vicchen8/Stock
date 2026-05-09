from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

import calculate
import fetch
import filter as stock_filter
import rounder


STATE_FILE = Path("fetch_state.json")


class StockFilterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("股票篩選器")
        self.root.geometry("1200x760")
        self.root.minsize(980, 620)

        self.vars = {
            "price_above_ma5": tk.BooleanVar(value=True),
            "price_above_ma10": tk.BooleanVar(value=True),
            "price_above_ma20": tk.BooleanVar(value=True),
            "price_above_ma60": tk.BooleanVar(value=True),
            "price_above_middle": tk.BooleanVar(value=True),
            "price_below_middle": tk.BooleanVar(value=True),
            "volume_above_10m": tk.BooleanVar(value=True),
        }

        self.fetch_running = False
        self.fetch_last_time = self._load_last_fetch_time()
        self.fetch_last_summary = self._load_last_fetch_summary()
        self._pipeline_conditions: list[str] = self._selected_conditions()

        self._checkbox_off_image = None
        self._checkbox_on_image = None

        self._build_ui()
        self.run_filter()
        self._refresh_fetch_status_label()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        left = ttk.Frame(self.root, padding=16)
        left.grid(row=0, column=0, sticky="nsw")

        right = ttk.Frame(self.root, padding=16)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        title = ttk.Label(left, text="篩選條件", font=("Microsoft JhengHei", 18, "bold"))
        title.pack(anchor="w", pady=(0, 12))

        self._create_checkbox_images()

        self._add_checkbox(left, "price_above_ma5")
        self._add_checkbox(left, "price_above_ma10")
        self._add_checkbox(left, "price_above_ma20")
        self._add_checkbox(left, "price_above_ma60")
        self._add_checkbox(left, "price_above_middle")
        self._add_checkbox(left, "price_below_middle")
        self._add_checkbox(left, "volume_above_10m")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=12)

        self.fetch_button = ttk.Button(left, text="抓取並更新", command=self.start_fetch)
        self.fetch_button.pack(fill="x", pady=4)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=12)

        self.filter_status_label = ttk.Label(left, text="", justify="left")
        self.filter_status_label.pack(anchor="w", pady=(0, 10))

        self.fetch_progress_label = ttk.Label(left, text="抓取進度：0/0", justify="left")
        self.fetch_progress_label.pack(anchor="w")

        self.process_progress_label = ttk.Label(left, text="處理進度：0/0", justify="left")
        self.process_progress_label.pack(anchor="w", pady=(0, 10))

        self.fetch_status_label = ttk.Label(left, text="", justify="left")
        self.fetch_status_label.pack(anchor="w")

        result_title = ttk.Label(right, text="篩選結果", font=("Microsoft JhengHei", 18, "bold"))
        result_title.grid(row=0, column=0, sticky="w", pady=(0, 12))

        table_frame = ttk.Frame(right)
        table_frame.grid(row=1, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_frame, columns=("code", "name"), show="headings", height=20)
        self.tree.heading("code", text="股票代碼")
        self.tree.heading("name", text="股票名稱")
        self.tree.column("code", width=140, anchor="center")
        self.tree.column("name", width=260, anchor="w")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        self.summary_label = ttk.Label(right, text="", anchor="w")
        self.summary_label.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _add_checkbox(self, parent: tk.Widget, condition_key: str) -> None:
        checkbox = tk.Checkbutton(
            parent,
            text=stock_filter.CONDITIONS[condition_key].label,
            variable=self.vars[condition_key],
            command=self.run_filter,
            image=self._checkbox_off_image,
            selectimage=self._checkbox_on_image,
            compound="left",
            indicatoron=False,
            selectcolor="#e8f7e8",
            background="white",
            activebackground="white",
            relief="flat",
            anchor="w",
            padx=8,
            pady=4,
            borderwidth=0,
            highlightthickness=0,
        )
        checkbox.pack(anchor="w", pady=4, fill="x")

    def _create_checkbox_images(self) -> None:
        off = tk.PhotoImage(width=16, height=16)
        off.put("#ffffff", to=(0, 0, 16, 16))
        off.put("#8b8b8b", to=(0, 0, 16, 1))
        off.put("#8b8b8b", to=(0, 0, 1, 16))
        off.put("#8b8b8b", to=(15, 0, 16, 16))
        off.put("#8b8b8b", to=(0, 15, 16, 16))

        on = tk.PhotoImage(width=16, height=16)
        on.put("#ffffff", to=(0, 0, 16, 16))
        on.put("#3aa655", to=(0, 0, 16, 1))
        on.put("#3aa655", to=(0, 0, 1, 16))
        on.put("#3aa655", to=(15, 0, 16, 16))
        on.put("#3aa655", to=(0, 15, 16, 16))
        on.put("#3aa655", to=(4, 8, 7, 11))
        on.put("#3aa655", to=(7, 11, 13, 5))

        self._checkbox_off_image = off
        self._checkbox_on_image = on

    def _selected_conditions(self) -> list[str]:
        return [key for key, var in self.vars.items() if var.get()]

    def run_filter(self) -> None:
        try:
            selected = self._selected_conditions()
            result = stock_filter.filter_stocks(selected)
            self._refresh_table(result)

            labels = [stock_filter.CONDITIONS[key].label for key in selected]
            if labels:
                self.filter_status_label.config(text="已啟用條件：\n" + "\n".join(f"• {label}" for label in labels))
            else:
                self.filter_status_label.config(text="未勾選任何條件\n目前會顯示所有已下載股票")

            self.summary_label.config(text=f"符合股票數量: {len(result)}")
        except Exception as exc:
            messagebox.showerror("篩選失敗", str(exc))

    def start_fetch(self) -> None:
        if self.fetch_running:
            return

        if not messagebox.askyesno("確認更新", "是否要開始抓取並更新資料？"):
            return

        self.fetch_running = True
        self.fetch_button.config(state="disabled")
        self._pipeline_conditions = self._selected_conditions()
        self._set_fetch_status_text("更新中...")
        self._set_fetch_progress(0, 0)
        self._set_process_progress(0, 0)

        thread = threading.Thread(target=self._fetch_worker, daemon=True)
        thread.start()

    def _fetch_worker(self) -> None:
        error = None
        summary = None
        filtered_result = None
        try:
            self._set_fetch_status_text("抓取中...")
            summary = fetch.fetch(progress_callback=self._report_fetch_progress)

            self._set_fetch_status_text("處理中：rounder")
            self._set_process_progress(0, 0)
            rounder.rounder(progress_callback=self._report_process_progress)

            self._set_fetch_status_text("處理中：calculate")
            self._set_process_progress(0, 0)
            calculate.calculate(progress_callback=self._report_process_progress)

            self.fetch_last_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.fetch_last_summary = (
                f"抓取成功 {summary['success']} 筆，失敗 {summary['failed']} 筆，共 {summary['total']} 筆"
            )
            filtered_result = stock_filter.filter_stocks(self._pipeline_conditions)
            self._save_fetch_state()
        except Exception as exc:
            error = exc

        self.root.after(0, self._finish_fetch, error, summary, filtered_result)

    def _finish_fetch(self, error: Exception | None, summary: dict | None, filtered_result=None) -> None:
        self.fetch_running = False
        self.fetch_button.config(state="normal")

        if error is not None:
            self._set_fetch_status_text("更新失敗")
            messagebox.showerror("更新失敗", str(error))
            return

        if filtered_result is not None:
            self._refresh_table(filtered_result)
            self.summary_label.config(text=f"符合股票數量: {len(filtered_result)}")

        self._refresh_fetch_status_label()
        if summary is not None:
            messagebox.showinfo(
                "更新完成",
                f"已完成抓取、round、calculate、filter\n{self.fetch_last_summary}",
            )

    def _set_fetch_status_text(self, text: str) -> None:
        self.root.after(0, lambda: self.fetch_status_label.config(text=text))

    def _set_fetch_progress(self, current: int, total: int) -> None:
        self.root.after(0, lambda: self.fetch_progress_label.config(text=f"抓取進度：{current}/{total}"))

    def _set_process_progress(self, current: int, total: int) -> None:
        self.root.after(0, lambda: self.process_progress_label.config(text=f"處理進度：{current}/{total}"))

    def _report_fetch_progress(self, current: int, total: int) -> None:
        self._set_fetch_progress(current, total)

    def _report_process_progress(self, current: int, total: int) -> None:
        self._set_process_progress(current, total)

    def _refresh_table(self, df) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row["股票代碼"], row["股票名稱"]))

    def _fetch_status_text(self) -> str:
        if self.fetch_running:
            return "更新中..."
        if self.fetch_last_time:
            summary_text = f"\n{self.fetch_last_summary}" if self.fetch_last_summary else ""
            return f"最後更新時間: {self.fetch_last_time}{summary_text}"
        return "尚未更新"

    def _refresh_fetch_status_label(self) -> None:
        self.fetch_status_label.config(text=self._fetch_status_text())

    def _load_last_fetch_time(self) -> str | None:
        if not STATE_FILE.exists():
            return None
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            value = data.get("last_fetch_time")
            return value or None
        except Exception:
            return None

    def _load_last_fetch_summary(self) -> str | None:
        if not STATE_FILE.exists():
            return None
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            value = data.get("last_fetch_summary")
            return value or None
        except Exception:
            return None

    def _save_fetch_state(self) -> None:
        data = {}
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        data["last_fetch_time"] = self.fetch_last_time
        data["last_fetch_summary"] = self.fetch_last_summary
        STATE_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


def main() -> None:
    root = tk.Tk()
    try:
        style = ttk.Style()
        style.theme_use("clam")
    except Exception:
        pass
    StockFilterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
