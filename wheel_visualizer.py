import datetime
import tkinter as tk
import math
import random
from colorsys import hls_to_rgb
from roulette import *

def angle_to_sector_num(angle, num_sectors):
    extent = 360 / num_sectors
    return int((360 - angle) / (extent)) % num_sectors

class WheelVisualizer:
    def __init__(self, root):
        self.root = root
        self.canvas = tk.Canvas(root, width=400, height=450, bg="white")
        self.canvas.pack()

        self.angle = 0
        self.initial_angle = 0
        self.speed = 0
        self.running = False
        self.num_sectors_input = tk.IntVar(value=6)
        self.num_sectors = 6
        self.colors = []

        self.acceleration = 0
        self.initial_speed = 0
        self.spin_count = 0
        self.spin_count_input = tk.IntVar(value=10)
        self.spin_time = 5
        self.spin_time_input = tk.IntVar(value=5)
        self.target_angle = 0
        self.target_angle_input = tk.IntVar(value=100)

        self.start_time = None

        self.create_controls()
        self.apply_settings()

    def generate_colors(self):
        self.colors = []
        for _ in range(self.num_sectors):
            h = random.uniform(0, 1)  # Full hue range
            s = random.uniform(0.2, 1.0)  # Saturation
            l = random.uniform(0.5, 0.9)  # Pastel range
            r, g, b = hls_to_rgb(h, l, s)
            self.colors.append("#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255)))

    def draw_wheel(self):
        self.canvas.delete("wheel")
        cx, cy, r = 200, 250, 100
        num_sectors = self.num_sectors
        extent = 360 / num_sectors

        selected_sector = angle_to_sector_num(self.angle, self.num_sectors)

        for i in range(num_sectors):
            start_angle = (360 / num_sectors) * i + self.angle + 90
            width = 2 if i == selected_sector else 1
            self.canvas.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=start_angle,
                extent=extent,
                fill=self.colors[i % len(self.colors)],
                width=width,
                outline="black",
                tags="wheel",
            )
            mid_angle = math.radians(start_angle + extent / 2)
            text_x = cx + r * 0.6 * math.cos(mid_angle)
            text_y = cy - r * 0.6 * math.sin(mid_angle)
            self.canvas.create_text(
                text_x,
                text_y,
                text=str(i + 1),
                font=("Arial", 14, "bold"),
                tags="wheel",
            )

        # target pointer arc
        self.canvas.create_arc(
            cx - r,
            cy - r,
            cx + r,
            cy + r,
            start=self.angle - self.target_angle + 90 - 1,
            extent=3,
            fill="red",
            tags="wheel",
        )

        # Draw arrow
        self.canvas.create_polygon(
            190, 120, 210, 120, 200, 160, outline="black", fill="gray", tags="wheel"
        )

        # Display selected sector
        self.canvas.delete("sector_text")
        self.canvas.create_text(
            200,
            30,
            text=f"Selected: {selected_sector + 1}",
            font=("Arial", 14, "bold"),
            tags="sector_text",
        )

        self.canvas.delete("speed_text")
        self.canvas.create_text(
            200,
            50,
            text=f"Speed: {self.speed:.1f}",
            font=("Arial", 14, "bold"),
            tags="speed_text",
        )

        self.canvas.delete("acc_text")
        self.canvas.create_text(
            200,
            70,
            text=f"Acceleration: {self.acceleration:.1f}",
            font=("Arial", 14, "bold"),
            tags="acc_text",
        )

        self.canvas.delete("target_text")
        self.canvas.create_text(
            200,
            90,
            text=f"Target: {angle_to_sector_num(self.target_angle, self.num_sectors) + 1}",
            font=("Arial", 14, "bold"),
            tags="acc_text",
        )

    def update(self):
        if self.speed > 0:
            time = datetime.datetime.now() - self.start_time
            time = time.total_seconds()
            self.angle, self.speed = get_pos(self.initial_angle, time, self.initial_speed, self.acceleration)

            self.angle %= 360
            self.angle_slider.set(self.angle)

            self.draw_wheel()
            self.root.after(10, self.update)

    def start(self):
        # self.stop()
        self.stop()
        self.apply_settings()
        if self.speed <= 0:
            self.start_time = datetime.datetime.now()

            total_path = self.target_angle + 360 * self.spin_count - self.initial_angle
            self.acceleration, self.initial_speed = get_spin_stats(self.spin_time, total_path)

            self.speed = self.initial_speed
            self.update()

    def stop(self):
        # if not self.speed:
        #     self.angle = 0

        self.speed = 0
        self.draw_wheel()
        self.angle_slider.set(self.angle)

    def apply_settings(self):
        self.num_sectors = self.num_sectors_input.get()
        self.spin_time = self.spin_time_input.get()
        self.spin_count = self.spin_count_input.get()
        self.target_angle = self.target_angle_input.get()

        self.initial_angle = self.angle - 360

        self.generate_colors()
        self.draw_wheel()

    def update_angle(self, value):
        self.angle = float(value)
        self.draw_wheel()

    def random_target(self):
        self.target_angle_input.set(random.uniform(0, 360))

    def create_controls(self):
        frame = tk.Frame(self.root)
        frame.pack()
        tk.Button(frame, text="Start", command=self.start).pack(side=tk.LEFT)
        tk.Button(frame, text="Stop", command=self.stop).pack(side=tk.LEFT)
        tk.Label(frame, text="Sectors:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.num_sectors_input, width=5).pack(side=tk.LEFT)
        tk.Label(frame, text="Spin count:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.spin_count_input, width=5).pack(side=tk.LEFT)
        tk.Label(frame, text="Spin time:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.spin_time_input, width=5).pack(side=tk.LEFT)
        tk.Label(frame, text="Target angle:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.target_angle_input, width=5).pack(side=tk.LEFT)
        tk.Button(frame, text="Rand", command=self.random_target).pack(side=tk.LEFT)
        tk.Button(frame, text="Apply", command=self.apply_settings).pack(side=tk.LEFT)

        self.angle_slider = tk.Scale(self.root, from_=0, to=360, orient=tk.HORIZONTAL, command=self.update_angle)
        self.angle_slider.pack(fill=tk.X)


if __name__ == "__main__":
    root = tk.Tk()
    app = WheelVisualizer(root)
    root.mainloop()