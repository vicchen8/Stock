from __future__ import annotations

import json
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
from tkinter import messagebox, ttk

import fetch
import filter as stock_filter


STATE_FILE = Path("fetch_state.json")


class StockFilterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("股票篩選工具")
        self.root.geometry("1200x760")
        self.root.minsize(980, 620)

        self.var_ma5 = tk.BooleanVar(value=True)
        self.var_middle = tk.BooleanVar(value=True)
        self.var_volume = tk.BooleanVar(value=True)

        self.fetch_running = False
        self.fetch_last_time = self._load_last_fetch_time()
        self.fetch_last_summary = self._load_last_fetch_summary()
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

        self.chk_ma5 = tk.Checkbutton(
            left,
            text=stock_filter.CONDITIONS["price_above_ma5"].label,
            variable=self.var_ma5,
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
        self.chk_ma5.pack(anchor="w", pady=4, fill="x")

        self.chk_middle = tk.Checkbutton(
            left,
            text=stock_filter.CONDITIONS["price_above_middle"].label,
            variable=self.var_middle,
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
        self.chk_middle.pack(anchor="w", pady=4, fill="x")

        self.chk_volume = tk.Checkbutton(
            left,
            text=stock_filter.CONDITIONS["volume_above_10m"].label,
            variable=self.var_volume,
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
        self.chk_volume.pack(anchor="w", pady=4, fill="x")

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=12)

        self.fetch_button = ttk.Button(left, text="抓取符合名單", command=self.start_fetch)
        self.fetch_button.pack(fill="x", pady=4)

        ttk.Separator(left, orient="horizontal").pack(fill="x", pady=12)

        self.filter_status_label = ttk.Label(left, text="", justify="left")
        self.filter_status_label.pack(anchor="w", pady=(0, 10))

        self.fetch_status_label = ttk.Label(left, text="", justify="left")
        self.fetch_status_label.pack(anchor="w")

        result_title = ttk.Label(right, text="符合條件的股票", font=("Microsoft JhengHei", 18, "bold"))
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
        # 綠色勾勾
        on.put("#3aa655", to=(4, 8, 7, 11))
        on.put("#3aa655", to=(7, 11, 13, 5))

        self._checkbox_off_image = off
        self._checkbox_on_image = on

    def _selected_conditions(self) -> list[str]:
        selected = []
        if self.var_ma5.get():
            selected.append("price_above_ma5")
        if self.var_middle.get():
            selected.append("price_above_middle")
        if self.var_volume.get():
            selected.append("volume_above_10m")
        return selected

    def run_filter(self) -> None:
        try:
            selected = self._selected_conditions()
            result = stock_filter.filter_stocks(selected)
            self._refresh_table(result)

            labels = [stock_filter.CONDITIONS[key].label for key in selected]
            if labels:
                self.filter_status_label.config(text="已啟用:\n" + "\n".join(f"• {label}" for label in labels))
            else:
                self.filter_status_label.config(text="未勾選任何條件\n目前會顯示所有股票")

            self.summary_label.config(text=f"符合股票數量: {len(result)}")
        except Exception as exc:
            messagebox.showerror("篩選失敗", str(exc))

    def start_fetch(self) -> None:
        if self.fetch_running:
            return

        self.fetch_running = True
        self.fetch_button.config(state="disabled")
        self.fetch_status_label.config(text="抓取狀態: 正在抓取...")

        thread = threading.Thread(target=self._fetch_worker, daemon=True)
        thread.start()

    def _fetch_worker(self) -> None:
        error = None
        summary = None
        try:
            summary = fetch.fetch()
            self.fetch_last_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.fetch_last_summary = (
                f"成功 {summary['success']} 檔，失敗 {summary['failed']} 檔，共 {summary['total']} 檔"
            )
            self._save_fetch_state()
        except Exception as exc:
            error = exc

        self.root.after(0, self._finish_fetch, error, summary)

    def _finish_fetch(self, error: Exception | None, summary: dict | None) -> None:
        self.fetch_running = False
        self.fetch_button.config(state="normal")

        if error is not None:
            self.fetch_status_label.config(text="抓取狀態: 抓取失敗")
            messagebox.showerror("抓取失敗", str(error))
            return

        self._refresh_fetch_status_label()
        if summary is not None:
            messagebox.showinfo(
                "抓取完成",
                f"已完成抓取\n成功 {summary['success']} 檔，失敗 {summary['failed']} 檔，共 {summary['total']} 檔",
            )

    def _refresh_table(self, df) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=(row["股票代碼"], row["股票名稱"]))

    def _fetch_status_text(self) -> str:
        if self.fetch_running:
            return "抓取狀態: 正在抓取..."
        if self.fetch_last_time:
            summary_text = f"\n{self.fetch_last_summary}" if self.fetch_last_summary else ""
            return f"抓取狀態: 已抓取\n上次抓取時間: {self.fetch_last_time}{summary_text}"
        return "抓取狀態: 尚未抓取"

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
