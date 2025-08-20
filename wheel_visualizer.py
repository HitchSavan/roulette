"""
Roulette wheel visualization module

Draws a wheel with the controls for simulating and
adjusting roulette parameters
"""

try:
    from RangeSlider.RangeSlider import RangeSliderH
except ModuleNotFoundError:
    print("\nRangeSlider module not found, unable to use stages duration slider")

import datetime
import tkinter as tk
import math
import random
from colorsys import hls_to_rgb
import roulette
import utils


class WheelVisualizer:
    def __init__(self, app_root):
        self.root = app_root
        self.canvas = tk.Canvas(app_root, width=400, height=450, bg="white")
        self.canvas.pack()

        self.angle = 0
        self.initial_angle = 0
        self.speed = 0
        self.running = False
        self.sectors_amount_input = tk.IntVar(value=6)
        self.sectors_amount = 6
        self.colors = []

        self.acceleration = 0
        self.initial_speed = 0
        self.linear_speed = 0
        self.spins_amount = 0
        self.spins_amount_input = tk.IntVar(value=10)
        self.spin_time = 5
        self.spin_time_input = tk.IntVar(value=5)
        self.target_angle = 0
        self.target_angle_input = tk.IntVar(value=100)
        self.spin_coeff = tk.IntVar(value=1)

        self.stages_controller = roulette.StagesController(self.spin_time)
        self.current_stage = roulette.STOP_STAGE

        self.stages_controller.emplace_stage(
            roulette.Stages.DECCELERATION_STAGE,
            self.spin_time * 0.3)
        self.stages_controller.emplace_stage(
            roulette.Stages.LINEAR_STAGE,
            self.spin_time * 0.3)
        self.stages_controller.emplace_stage(
            roulette.Stages.DECCELERATION_STAGE,
            self.spin_time - self.stages_controller.total_stages_duration)

        self.start_time = datetime.datetime.now()

        self.create_controls()
        self.apply_settings()

    def generate_colors(self):
        self.colors = []
        for _ in range(self.sectors_amount):
            h = random.uniform(0, 1)  # Full hue range
            s = random.uniform(0.2, 1.0)  # Saturation
            l = random.uniform(0.5, 0.9)  # Pastel range
            r, g, b = hls_to_rgb(h, l, s)
            self.colors.append(
                "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))
            )

    def draw_wheel(self):
        self.canvas.delete("wheel")
        cx, cy, r = 200, 250, 100
        sectors_amount = self.sectors_amount
        sector_size = 360 / sectors_amount

        selected_sector = utils.angle_to_sector(
            self.angle, self.sectors_amount)

        for i in range(sectors_amount):
            start_angle = (360 / sectors_amount) * i + self.angle + 90
            width = 2 if i == selected_sector else 1
            self.canvas.create_arc(
                cx - r,
                cy - r,
                cx + r,
                cy + r,
                start=start_angle,
                extent=sector_size,
                fill=self.colors[i % len(self.colors)],
                width=width,
                outline="black",
                tags="wheel",
            )
            mid_angle = math.radians(start_angle + sector_size / 2)
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

        self.canvas.delete("time_text")
        self.canvas.create_text(
            200,
            10,
            text=f"""Time left: {
                round(self.spin_time - 
                (datetime.datetime.now() - self.start_time).total_seconds(),
                    1)}""",
            font=("Arial", 14, "bold"),
            tags="time_text",
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
            text=f"Target: {utils.angle_to_sector(self.target_angle, self.sectors_amount) + 1}",
            font=("Arial", 14, "bold"),
            tags="target_text",
        )

        self.canvas.delete("stage_text")
        self.canvas.create_text(
            200,
            110,
            text=f"""Current stage: {
                self.current_stage.stage_type.name
                }""",
            font=("Arial", 14, "bold"),
            tags="stage_text",
        )

    def update(self):
        time = datetime.datetime.now() - self.start_time
        time = time.total_seconds()

        if (self.current_stage !=
                self.stages_controller.get_current_stage(time)):
            roulette.logging.debug(
                f'''stage switch {
                    self.current_stage.stage_type.name} -> {
                        self.stages_controller.get_current_stage(time).stage_type.name}
                    time {time}
                    speed {self.speed}
                    acceleration {self.acceleration}'''
            )
            self.current_stage = self.stages_controller.get_current_stage(time)
            if self.speed <= 0 or self.current_stage == roulette.STOP_STAGE:
                self.draw_wheel()
                # self.stop()
                return
            self.initial_angle = roulette.get_angle(
                self.initial_speed,
                self.acceleration,
                self.stages_controller.prev_stage(time).duration,
                self.initial_angle
            )
            self.acceleration = self.current_stage.acceleration
            self.initial_speed = self.current_stage.start_speed

        stage_time = time
        if self.current_stage.start_time > 0:
            stage_time -= self.current_stage.start_time

        self.speed = roulette.get_speed(
            self.initial_speed, self.acceleration, stage_time)
        self.angle = roulette.get_angle(
            self.initial_speed, self.acceleration, stage_time, self.initial_angle
        )

        self.angle_slider.set(self.angle)

        self.draw_wheel()
        self.root.after(10, self.update)

    def start(self):
        self.stop()
        self.apply_settings()
        if self.speed <= 0:
            self.start_time = datetime.datetime.now()

            self.linear_speed = roulette.get_simple_initial_speed(
                self.target_angle, self.spins_amount, self.spin_time, self.initial_angle)
            self.initial_speed = self.linear_speed
            acceleration_sign = self.stages_controller.stage_order[0].stage_type.value

            # ???? stupid
            if acceleration_sign > 0:
                self.initial_speed /= 2
            elif acceleration_sign < 0:
                self.linear_speed /= 2

            self.stages_controller.stage_order[0].start_speed = self.initial_speed
            self.stages_controller.stage_order[0].end_speed = self.linear_speed

            self.stages_controller.stage_order[1].start_speed = self.linear_speed
            self.stages_controller.stage_order[1].acceleration = 0
            self.stages_controller.stage_order[1].end_speed = self.linear_speed

            self.stages_controller.stage_order[2].start_speed = self.linear_speed
            self.stages_controller.stage_order[2].end_speed = 0

            # order for 3 stages with second being linear
            for stage in self.stages_controller.stage_order:
                if stage.stage_type != roulette.Stages.LINEAR_STAGE:
                    stage.update_acceleration()

            self.initial_speed = roulette.get_initial_speed(
                self.target_angle, self.spins_amount,
                self.stages_controller.stage_order,
                self.initial_angle)

            for stage_no, stage in enumerate(self.stages_controller.stage_order):
                stage.start_speed = (
                    (self.stages_controller.stage_order[stage_no-1].start_speed)
                    if stage_no > 0
                    else self.initial_speed) + \
                    ((self.stages_controller.stage_order[stage_no-1].acceleration *
                      self.stages_controller.stage_order[stage_no-1].duration)
                     if stage_no > 0
                     else 0)

            self.current_stage = self.stages_controller.stage_order[0]

            self.acceleration = self.current_stage.acceleration
            self.speed = self.initial_speed

            roulette.logging.debug(f'''
                  initial 1st phase speed: {self.stages_controller.stage_order[0].start_speed}
                  1st phase duration: {self.stages_controller.stage_order[0].duration}
                  1st phase accel: {self.stages_controller.stage_order[0].acceleration}

                  initial 2nd phase speed: {self.stages_controller.stage_order[1].start_speed}
                  2nd phase duration: {self.stages_controller.stage_order[1].duration}
                  2nd phase accel: {self.stages_controller.stage_order[1].acceleration}

                  initial 3rd phase speed: {self.stages_controller.stage_order[2].start_speed}
                  3rd phase duration: {self.stages_controller.stage_order[2].duration}
                  3rd phase accel: {self.stages_controller.stage_order[2].acceleration}

                  total spin path: {self.stages_controller.stage_order[0].get_total_path()+
                                    self.stages_controller.stage_order[1].get_total_path()+
                                    self.stages_controller.stage_order[2].get_total_path()}
                  total 1st phase path: {self.stages_controller.stage_order[0].get_total_path()}
                  total 2nd phase path: {self.stages_controller.stage_order[1].get_total_path()}
                  total 3rd phase path: {self.stages_controller.stage_order[2].get_total_path()}

                  relative spin path: {(self.stages_controller.stage_order[0].get_total_path() +
                                        self.stages_controller.stage_order[1].get_total_path() +
                                        self.stages_controller.stage_order[2].get_total_path() ) % 360}
                  relative 1st phase path: {self.stages_controller.stage_order[0].get_total_path() % 360}
                  relative 2nd phase path: {self.stages_controller.stage_order[1].get_total_path() % 360}
                  relative 3rd phase path: {self.stages_controller.stage_order[2].get_total_path() % 360}
                  
                  total duration: {self.stages_controller.stage_order[0].duration +
                                   self.stages_controller.stage_order[1].duration +
                                   self.stages_controller.stage_order[2].duration}

                  target angle: {self.target_angle}
                  target total path: {self.target_angle + 360 * self.spins_amount - self.initial_angle}
                  target time: {self.spin_time}
            ''')

            self.update()

    def stop(self):
        self.speed = 0
        self.draw_wheel()
        self.angle_slider.set(self.angle)
        self.stages_controller.active_stage_id = 0

    def apply_settings(self):
        self.sectors_amount = self.sectors_amount_input.get()
        self.spin_time = self.spin_time_input.get()
        self.target_angle = self.target_angle_input.get()

        self.spins_amount_input.set(
            roulette.get_spins_amount(self.spin_coeff.get(), self.spin_time)
        )
        self.spins_amount = self.spins_amount_input.get()

        self.initial_angle = self.angle

        if self.angle - self.target_angle >= 0:
            self.initial_angle -= 360

        try:
            self.update_durations()
        except AttributeError:
            pass

        self.stages_controller.update_total_time(self.spin_time)

        self.generate_colors()
        self.draw_wheel()

    def update_angle(self, value):
        self.angle = float(value)
        self.draw_wheel()

    def update_spin_coeff(self, value):
        self.spin_coeff.set(value)

    def update_durations(self):
        coeffs = [0]
        coeffs += self.stages_slider.getValues()
        coeffs.append(1)

        for [stage_no, stage] in enumerate(self.stages_controller.stage_order):
            stage.time_coefficient = coeffs[stage_no+1] - coeffs[stage_no]

    def random_target(self):
        self.target_angle_input.set(int(random.uniform(0, 360)))

    def create_controls(self):
        frame = tk.Frame(self.root)
        frame.pack()
        tk.Button(frame, text="Start", command=self.start).pack(side=tk.LEFT)
        tk.Button(frame, text="Stop", command=self.stop).pack(side=tk.LEFT)
        tk.Label(frame, text="Sectors:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.sectors_amount_input, width=5).pack(
            side=tk.LEFT
        )
        tk.Label(frame, text="Spin count:").pack(side=tk.LEFT)
        self.spins_amount_field = tk.Entry(
            frame, textvariable=self.spins_amount_input, width=5
        )
        self.spins_amount_field.pack(side=tk.LEFT)
        tk.Label(frame, text="Spin time:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.spin_time_input,
                 width=5).pack(side=tk.LEFT)
        tk.Label(frame, text="Target angle:").pack(side=tk.LEFT)
        tk.Entry(frame, textvariable=self.target_angle_input, width=5).pack(
            side=tk.LEFT
        )
        tk.Button(frame, text="Rand", command=self.random_target).pack(
            side=tk.LEFT)
        tk.Button(frame, text="Apply",
                  command=self.apply_settings).pack(side=tk.LEFT)

        # self.spins_amount_field.config(state="disabled")

        self.angle_slider = tk.Scale(
            self.root, from_=0, to=360, orient=tk.HORIZONTAL, command=self.update_angle
        )
        self.spin_coeff_slider = tk.Scale(
            from_=1, to=10, orient=tk.HORIZONTAL, command=self.update_spin_coeff
        )

        self.angle_slider.pack(fill=tk.X)
        self.spin_coeff_slider.pack(fill=tk.X)

        try:
            slider_left_handle = tk.DoubleVar(value=0.3)
            slider_right_handle = tk.DoubleVar(value=0.6)
            self.stages_slider = RangeSliderH(
                self.root, [slider_left_handle, slider_right_handle], padX=12)
            self.stages_slider.pack()
        except NameError:
            pass


if __name__ == "__main__":
    root = tk.Tk()
    app = WheelVisualizer(root)
    root.mainloop()
