import tkinter as tk

# 建立主視窗
window = tk.Tk()
window.title("股票")
window.geometry("1600x900")  # 視窗大小：寬400 x 高300

left_frame = tk.Frame(window, bg="lightblue", width=300, height=400)
left_frame.pack(side="left", fill="both")

# 右邊 Frame
right_frame = tk.Frame(window, bg="lightgreen", width=300, height=400)
right_frame.pack(side="right", fill="both")

# 在左邊加一個標籤
tk.Label(left_frame, text="這是左邊", font=("Arial", 14)).pack(pady=20)

# 在右邊加一個標籤
tk.Label(right_frame, text="這是右邊", font=("Arial", 14)).pack(pady=20)

window.mainloop()