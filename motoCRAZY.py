import math
import random
import time
import tkinter as tk


class MotorcycleSimulator:
    BG = "#0a0c10"
    PANEL = "#11151c"
    CARD = "#161b22"
    TEXT = "#f0f6fc"
    MUTED = "#8b949e"
    ACCENT = "#ff7b72"
    CYAN = "#38d430"
    GREEN = "#3fb950"
    YELLOW = "#d29922"
    RED = "#f85149"

    def __init__(self, root):
        self.COLOR_GREEN = "#1AE000"
        self.COLOR_DARK_GREEN = "#118A00"
        self.COLOR_BLACK = "#121212"
        self.COLOR_LIGHT_GRAY = "#D0D0D0"
        self.COLOR_WINDSHIELD = "#10141d"
        self.COLOR_HEADLIGHT = "#E8F5E9"

        self.root = root
        self.root.title("Симулятор мотоцикла — Crazy Nitro Ninja 400")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)
        self.root.configure(bg=self.BG)

        # ---------------- Физика ----------------
        self.mass = 243.0
        self.g = 9.81
        self.air_density = 1.225
        self.cd_a = 0.36
        self.rolling_coeff = 0.018
        self.drivetrain_eff = 0.88
        self.wheel_radius = 0.312

        self.engine_idle_rpm = 1300.0
        self.engine_redline = 14000.0
        self.final_drive = 2.928
        self.gear_ratios = {
            1: 2.928,
            2: 2.055,
            3: 1.619,
            4: 1.333,
            5: 1.153,
            6: 1.037,
        }
        self.max_gear = 6

        # ---------------- Состояние ----------------
        self.speed = 0.0
        self.rpm = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        self.gear = 1
        self.distance = 0.0
        self.fuel = 100.0
        self.engine_temp = 24.0

        # Нитро и лазер
        self.nitro_active = False
        self.nitro_fuel = 100.0
        self.laser_cooldown = 0.0
        self.laser_active_timer = 0.0

        self.engine_on = False
        self.engine_state = "off"
        self.start_timer = 0.0
        self.start_duration = 1.2
        self.shift_flash = 0.0

        self.steer = 0.0
        self.lateral = 0.0
        self.lateral_velocity = 0.0
        self.roll = 0.0
        self.pitch = 0.0

        # Эффекты
        self.cam_offset_x = 0.0
        self.cam_offset_y = 0.0
        self.cam_shake = 0.0
        self.glitch_timer = 0.0
        self.brake_lever_anim = 0.0

        self.damage = 0.0
        self.crashed = False
        self.crash_timer = 0.0
        self.crash_vx = 0.0

        self.wobble = 0.0
        self.road_time = 0.0
        self.wheel_angle = 0.0

        # Объекты
        self.enemies = []
        self.splats = []
        self.explosions = []

        self.keys = set()
        self.action_keys_down = set()
        self.last_time = time.perf_counter()

        self.route = self.build_route()

        self.build_ui()
        self.bind_keys()
        self.update_loop()

    def build_ui(self):
        header = tk.Frame(self.root, bg=self.PANEL, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.PANEL)
        brand.pack(side="left", padx=20)
        tk.Label(
            brand,
            text="KAWASAKI NINJA 400 — CRAZY EDITION",
            fg="#ff0055",
            bg=self.PANEL,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor="w", pady=(6, 0))
        tk.Label(
            brand,
            text="Безумный Симулятор",
            fg=self.TEXT,
            bg=self.PANEL,
            font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")

        self.status_label = tk.Label(
            header,
            text="● ДВИГАТЕЛЬ ВЫКЛЮЧЕН",
            fg=self.RED,
            bg=self.PANEL,
            font=("Segoe UI", 10, "bold"),
        )
        self.status_label.pack(side="right", padx=20)

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        scene_card = tk.Frame(
            main, bg=self.CARD, highlightbackground="#30363d", highlightthickness=1
        )
        scene_card.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(scene_card, bg="#05070a", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.build_dashboard(main)

    def build_dashboard(self, parent):
        panel = tk.Frame(parent, bg=self.PANEL, width=310)
        panel.pack(side="right", fill="y", padx=(12, 0))
        panel.pack_propagate(False)

        tk.Label(
            panel,
            text="ИНФОРМАЦИЯ",
            fg=self.MUTED,
            bg=self.PANEL,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=16, pady=(14, 8))

        speed_card = tk.Frame(panel, bg=self.CARD, height=100)
        speed_card.pack(fill="x", padx=12)
        speed_card.pack_propagate(False)

        tk.Label(
            speed_card,
            text="СКОРОСТЬ",
            fg=self.MUTED,
            bg=self.CARD,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(8, 0))

        speed_row = tk.Frame(speed_card, bg=self.CARD)
        speed_row.pack(anchor="w", padx=12)
        self.speed_var = tk.StringVar(value="0.0")
        tk.Label(
            speed_row,
            textvariable=self.speed_var,
            fg=self.TEXT,
            bg=self.CARD,
            font=("Segoe UI", 32, "bold"),
        ).pack(side="left")
        tk.Label(
            speed_row,
            text="км/ч",
            fg=self.MUTED,
            bg=self.CARD,
            font=("Segoe UI", 10),
        ).pack(side="left", padx=(6, 0), pady=(14, 0))

        self.speed_hint = tk.Label(
            speed_card,
            text="Мотор выключен",
            fg="#8b949e",
            bg=self.CARD,
            font=("Segoe UI", 8),
        )
        self.speed_hint.pack(anchor="w", padx=12)

        metrics = tk.Frame(panel, bg=self.PANEL)
        metrics.pack(fill="x", padx=12, pady=10)

        self.gear_var = tk.StringVar(value="1")
        self.nitro_var = tk.StringVar(value="100%")
        self.temp_var = tk.StringVar(value="24 °C")
        self.distance_var = tk.StringVar(value="0.000 км")

        self.metric_card(metrics, 0, 0, "ПЕРЕДАЧА", self.gear_var, 18)
        self.metric_card(metrics, 0, 1, "НИТРО N2O", self.nitro_var, 14)
        self.metric_card(metrics, 1, 0, "ТЕМПЕРАТУРА", self.temp_var, 14)
        self.metric_card(metrics, 1, 1, "ДИСТАНЦИЯ", self.distance_var, 12)

        controls_card = tk.Frame(panel, bg=self.CARD)
        controls_card.pack(fill="x", padx=12, pady=(10, 0))

        tk.Label(
            controls_card,
            text="УПРАВЛЕНИЕ",
            fg="#ff0055",
            bg=self.CARD,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(6, 2))

        controls = [
            ("W / S", "Газ / Тормоз"),
            ("A / D", "Руление"),
            ("Shift", "⚡ ЛАЗЕРНЫЙ ЗАЛП"),
            ("F / X", "🔥 НИТРО УСКОРЕНИЕ"),
            ("Q / E", "Передача − / +"),
            ("Space", "Зажигание"),
            ("R", "Сброс"),
        ]
        for key, desc in controls:
            row = tk.Frame(controls_card, bg=self.CARD)
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(
                row,
                text=key,
                fg=self.TEXT,
                bg="#21262d",
                font=("Consolas", 8, "bold"),
                padx=4,
                pady=1,
            ).pack(side="left")
            tk.Label(
                row, text=desc, fg=self.MUTED, bg=self.CARD, font=("Segoe UI", 8)
            ).pack(side="left", padx=6)

        buttons = tk.Frame(panel, bg=self.PANEL)
        buttons.pack(side="bottom", fill="x", padx=12, pady=10)

        self.engine_button = tk.Button(
            buttons,
            text="ЗАПУСТИТЬ ДВИГАТЕЛЬ",
            command=self.handle_engine_button,
            bg="#21262d",
            fg=self.TEXT,
            activebackground="#30363d",
            activeforeground=self.TEXT,
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=6,
            cursor="hand2",
        )
        self.engine_button.pack(fill="x", pady=2)

        tk.Button(
            buttons,
            text="СБРОСИТЬ СИМУЛЯЦИЮ",
            command=self.reset,
            bg="#238636",
            fg="white",
            activebackground="#2ea043",
            activeforeground="white",
            relief="flat",
            borderwidth=0,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=6,
            cursor="hand2",
        ).pack(fill="x", pady=2)

    def metric_card(self, parent, r, c, title, variable, size):
        card = tk.Frame(parent, bg=self.CARD, height=55)
        card.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        parent.grid_columnconfigure(c, weight=1)
        card.pack_propagate(False)

        tk.Label(
            card,
            text=title,
            fg=self.MUTED,
            bg=self.CARD,
            font=("Segoe UI", 7, "bold"),
        ).pack(anchor="w", padx=8, pady=(4, 0))
        tk.Label(
            card,
            textvariable=variable,
            fg=self.TEXT,
            bg=self.CARD,
            font=("Segoe UI", size, "bold"),
        ).pack(anchor="w", padx=8)

    def bind_keys(self):
        self.root.bind_all("<KeyPress>", self.on_key_press, add="+")
        self.root.bind_all("<KeyRelease>", self.on_key_release, add="+")
        self.root.focus_force()

    def normalize_key(self, event):
        code_map = {
            65: "a",
            68: "d",
            69: "e",
            81: "q",
            82: "r",
            83: "s",
            87: "w",
            70: "f",
            88: "x",
        }
        if getattr(event, "keycode", None) in code_map:
            return code_map[event.keycode]
        if event.keysym in ["Shift_L", "Shift_R"]:
            return "shift"
        aliases = {
            "ц": "w",
            "ф": "a",
            "ы": "s",
            "в": "d",
            "й": "q",
            "у": "e",
            "к": "r",
            "а": "f",
            "ч": "x",
        }
        return aliases.get(event.keysym.lower(), event.keysym.lower())

    def on_key_press(self, event):
        key = self.normalize_key(event)
        self.keys.add(key)
        if key in self.action_keys_down:
            return
        self.action_keys_down.add(key)

        if key == "e":
            self.set_gear(self.gear + 1)
        elif key == "q":
            self.set_gear(self.gear - 1)
        elif key == "r":
            self.reset()
        elif key == "space":
            self.toggle_engine()
        elif key == "shift":
            self.fire_laser()

    def on_key_release(self, event):
        key = self.normalize_key(event)
        self.keys.discard(key)
        self.action_keys_down.discard(key)

    def handle_engine_button(self):
        if self.crashed:
            self.reset()
        else:
            self.toggle_engine()

    def toggle_engine(self):
        if self.engine_state == "starting":
            return
        if self.engine_state == "running":
            self.stop_engine()
        else:
            self.start_engine()

    def start_engine(self):
        if self.fuel <= 0:
            return
        self.engine_state = "starting"
        self.engine_on = False
        self.start_timer = 0.0
        self.rpm = 0.0

    def stop_engine(self):
        self.engine_state = "off"
        self.engine_on = False
        self.throttle = 0.0

    def reset(self):
        self.speed = 0.0
        self.rpm = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        self.gear = 1
        self.distance = 0.0
        self.fuel = 100.0
        self.nitro_fuel = 100.0
        self.engine_temp = 24.0

        self.engine_on = False
        self.engine_state = "off"
        self.start_timer = 0.0

        self.steer = 0.0
        self.lateral = 0.0
        self.lateral_velocity = 0.0
        self.roll = 0.0
        self.pitch = 0.0

        self.damage = 0.0
        self.crashed = False
        self.crash_timer = 0.0
        self.crash_vx = 0.0
        self.wobble = 0.0

        self.enemies.clear()
        self.splats.clear()
        self.explosions.clear()

    def set_gear(self, gear):
        if self.engine_state != "running":
            return
        gear = max(1, min(self.max_gear, gear))
        if gear != self.gear:
            self.gear = gear
            self.shift_flash = 0.3
            self.rpm *= 0.82

    def build_route(self):
        rng = random.Random(2026)
        segments = []
        for _ in range(32):
            straight = rng.uniform(0.3, 0.7)
            segments.append({"length": straight, "curve": 0.0})
            if rng.random() < 0.75:
                turn_len = rng.uniform(0.2, 0.5)
                sign = rng.choice([-1.0, 1.0])
                segments.append(
                    {"length": turn_len, "curve": sign * rng.uniform(0.5, 1.2)}
                )
        return segments

    def route_offset(self, distance_km):
        total = sum(x["length"] for x in self.route)
        if total <= 0:
            return 0.0
        d = max(0.0, distance_km) % total
        offset = 0.0
        for seg in self.route:
            if d <= seg["length"]:
                return offset + seg["curve"] * d
            offset += seg["curve"] * seg["length"]
            d -= seg["length"]
        return offset

    def route_slope(self, distance_km):
        total = sum(x["length"] for x in self.route)
        if total <= 0:
            return 0.0
        d = max(0.0, distance_km) % total
        for seg in self.route:
            if d <= seg["length"]:
                return seg["curve"]
            d -= seg["length"]
        return 0.0

    def upcoming_turn(self):
        total = sum(x["length"] for x in self.route)
        if total <= 0:
            return "ПРЯМО", 0.0
        d = max(0.0, self.distance) % total
        accum = 0.0
        for seg in self.route:
            if d <= seg["length"]:
                dist_to_end = seg["length"] - d
                if seg["curve"] != 0.0:
                    turn_type = (
                        "ПОВОРОТ ВЛЕВО" if seg["curve"] < 0 else "ПОВОРОТ ВПРАВО"
                    )
                    return turn_type, dist_to_end * 1000.0
                accum += dist_to_end
                break
            d -= seg["length"]

        start_idx = 0
        curr_d = max(0.0, self.distance) % total
        temp_d = 0.0
        for i, seg in enumerate(self.route):
            if temp_d + seg["length"] >= curr_d:
                start_idx = i
                break
            temp_d += seg["length"]

        for i in range(1, len(self.route)):
            idx = (start_idx + i) % len(self.route)
            seg = self.route[idx]
            if seg["curve"] != 0.0:
                turn_type = "ПОВОРОТ ВЛЕВО" if seg["curve"] < 0 else "ПОВОРОТ ВПРАВО"
                return turn_type, accum * 1000.0
            accum += seg["length"]

        return "ПРЯМО", 0.0

    def fire_laser(self):
        if self.laser_cooldown <= 0 and not self.crashed:
            self.laser_cooldown = 0.25
            self.laser_active_timer = 0.12

            w = max(650, self.canvas.winfo_width())
            h = max(500, self.canvas.winfo_height())
            center_x = w / 2

            remaining_enemies = []
            for e in self.enemies:
                ex = center_x + e["x"] * (w / 2) * (1.0 / max(0.01, e["z"]))
                if abs(ex - center_x) < 90 and e["z"] < 0.8:
                    self.explosions.append(
                        {"x": ex, "y": h * 0.5, "radius": 20, "life": 0.3}
                    )
                else:
                    remaining_enemies.append(e)
            self.enemies = remaining_enemies

    def update_loop(self):
        now = time.perf_counter()
        dt = min(0.035, max(0.001, now - self.last_time))
        self.last_time = now

        self.road_time += dt
        self.read_inputs()
        self.simulate_startup(dt)
        self.simulate(dt)
        self.update_enemies(dt)
        self.animate(dt)
        self.update_labels()
        self.update_status()
        self.draw_scene()

        self.root.after(16, self.update_loop)

    def read_inputs(self):
        up = "w" in self.keys or "up" in self.keys
        down = "s" in self.keys or "down" in self.keys
        left = "a" in self.keys or "left" in self.keys
        right = "d" in self.keys or "right" in self.keys
        nitro = ("f" in self.keys or "x" in self.keys) and self.nitro_fuel > 0

        self.nitro_active = nitro and up and self.engine_state == "running"

        target_throttle = 1.0 if up and self.engine_state == "running" else 0.0
        target_brake = 1.0 if down else 0.0

        self.throttle += (target_throttle - self.throttle) * min(1.0, 12.0 * 0.016)
        self.brake += (target_brake - self.brake) * min(1.0, 18.0 * 0.016)

        target_steer = (-1.0 if left else 0.0) + (1.0 if right else 0.0)
        self.steer += (target_steer - self.steer) * min(1.0, 12.0 * 0.016)

    def simulate_startup(self, dt):
        if self.engine_state != "starting":
            return
        self.start_timer += dt
        t = min(1.0, self.start_timer / self.start_duration)

        if t < 0.20:
            self.rpm = 900 + 2800 * (t / 0.20)
        elif t < 0.45:
            p = (t - 0.20) / 0.25
            self.rpm = 3700 + 3300 * math.sin(p * math.pi * 1.6)
        elif t < 0.72:
            p = (t - 0.45) / 0.27
            self.rpm = 2400 + (1 - p) * 700 + 280 * math.sin(p * math.pi * 6)
        else:
            p = (t - 0.72) / 0.28
            self.rpm = 1950 - 700 * p

        if self.start_timer >= self.start_duration:
            self.engine_state = "running"
            self.engine_on = True
            self.rpm = self.engine_idle_rpm
            self.engine_temp = 65.0

    def torque_curve(self, rpm):
        if rpm < 1300:
            return 15.0
        x = (rpm - 1300.0) / (12000.0 - 1300.0)
        torque = 22.0 + (16.0 * math.sin(x * math.pi * 0.85))
        if self.nitro_active:
            torque *= 2.8
        return max(10.0, torque)

    def simulate(self, dt):
        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt
        if self.laser_active_timer > 0:
            self.laser_active_timer -= dt
        if self.glitch_timer > 0:
            self.glitch_timer -= dt

        if self.shift_flash > 0:
            self.shift_flash = max(0.0, self.shift_flash - dt)

        if self.crashed:
            self.animate_crash(dt)
            return

        # ---------------- Нитро и Температура ----------------
        if self.nitro_active:
            self.nitro_fuel = max(0.0, self.nitro_fuel - dt * 30.0)
            # Нагрев двигателя при использовании нитро
            self.engine_temp = min(130.0, self.engine_temp + dt * 28.0)
        else:
            # Восстановление нитро, когда оно не используется
            self.nitro_fuel = min(100.0, self.nitro_fuel + dt * 10.0)

        if self.engine_state != "running":
            if self.engine_state == "off":
                self.rpm += (0.0 - self.rpm) * min(1.0, dt * 4.0)
                self.speed = max(0.0, self.speed - 3.2 * dt)
                self.lateral_velocity *= max(0.0, 1.0 - dt * 3.0)
                self.lateral += self.lateral_velocity * dt
                self.roll += (0.0 - self.roll) * min(1.0, dt * 5.0)
                # Охлаждение мотора в выключенном состоянии
                self.engine_temp += (24.0 - self.engine_temp) * min(1.0, dt * 0.2)
            return

        velocity = self.speed / 3.6
        overall_ratio = self.gear_ratios[self.gear] * self.final_drive
        wheel_rps = velocity / max(0.01, 2.0 * math.pi * self.wheel_radius)
        locked_rpm = wheel_rps * 60.0 * overall_ratio

        clutch_slip = max(0.0, math.exp(-velocity * 0.25))
        target_rpm = max(
            self.engine_idle_rpm, locked_rpm + clutch_slip * 2200.0 * self.throttle
        )
        if self.nitro_active:
            target_rpm = self.engine_redline

        self.rpm += (target_rpm - self.rpm) * min(1.0, dt * 12.0)

        engine_torque = self.torque_curve(self.rpm) * self.throttle
        wheel_force = (
            engine_torque * overall_ratio * self.drivetrain_eff / self.wheel_radius
        )

        aero_force = 0.5 * self.air_density * self.cd_a * velocity * velocity
        rolling_force = self.rolling_coeff * self.mass * self.g
        brake_force = self.mass * self.g * 1.15 * self.brake
        net_force = wheel_force - aero_force - rolling_force - brake_force
        acceleration = net_force / self.mass

        self.speed = max(0.0, self.speed + acceleration * dt)

        road_slope = self.route_slope(self.distance)
        road_center_velocity = velocity * road_slope

        gyro_stability = max(0.2, 1.0 - (velocity / 120.0) * 0.6)
        steering_strength = (2.0 + 0.015 * velocity) * gyro_stability
        target_lateral_v = (self.steer * steering_strength) + (
            road_center_velocity * 0.15
        )

        self.lateral_velocity += (target_lateral_v - self.lateral_velocity) * min(
            1.0, dt * 6.0
        )
        self.lateral += self.lateral_velocity * dt

        # ---------------- Наклоны (Roll) ----------------
        speed_factor = min(1.0, self.speed / 15.0)
        desired_roll = self.steer * (12.0 + speed_factor * 33.0)
        self.roll += (desired_roll - self.roll) * min(1.0, dt * 8.0)
        self.pitch = (self.throttle * 0.8 - self.brake * 1.2) * 2.5

        if abs(self.lateral) > 14.0 or (
            velocity > 25.0 and abs(self.roll) > 52.0 and abs(self.steer) > 0.8
        ):
            self.trigger_crash()

        self.distance += velocity * dt / 1000.0
        self.fuel = max(
            0.0,
            self.fuel - (0.000014 * self.rpm + 0.00042 * self.throttle) * dt,
        )

        # Стандартная температура двигателя без нитро
        if not self.nitro_active:
            target_temp = 72.0 + (self.rpm / self.engine_redline) * 25.0
            self.engine_temp += (target_temp - self.engine_temp) * min(
                1.0, dt * 0.5
            )

    def trigger_crash(self):
        if self.crashed:
            return
        self.crashed = True
        self.crash_timer = 0.0
        self.damage = max(self.damage, 35.0)
        self.engine_state = "off"
        self.engine_on = False
        self.throttle = 0.0
        self.brake = 0.0
        self.rpm = 0.0
        self.crash_vx = (
            self.lateral_velocity
            if abs(self.lateral_velocity) > 0.5
            else (self.steer * 3.0)
        )

    def animate_crash(self, dt):
        self.crash_timer += dt
        self.lateral += self.crash_vx * dt
        self.speed = max(0.0, self.speed - 50.0 * dt)
        decay = max(0.0, 1.0 - dt * 3.5)
        self.crash_vx *= decay
        if self.speed <= 0.1:
            target_dead_roll = 50.0 if self.roll >= 0 else -50.0
            self.roll += (target_dead_roll - self.roll) * min(1.0, dt * 5.0)
        else:
            self.roll += self.crash_vx * dt * 10.0

    def animate(self, dt):
        target_cam_x = -self.roll * 0.8
        target_cam_y = self.brake * 12.0 - self.throttle * 6.0
        self.cam_offset_x += (target_cam_x - self.cam_offset_x) * min(
            1.0, dt * 8.0
        )
        self.cam_offset_y += (target_cam_y - self.cam_offset_y) * min(
            1.0, dt * 8.0
        )

        rpm_factor = (self.rpm / self.engine_redline) if self.engine_on else 0.0
        speed_factor = min(1.0, self.speed / 150.0)
        shake_amplitude = (
            (rpm_factor * 1.5)
            + (speed_factor * 2.5)
            + (10.0 if self.nitro_active else 0.0)
        )
        self.cam_shake = math.sin(self.road_time * 50.0) * shake_amplitude

        self.brake_lever_anim += (self.brake - self.brake_lever_anim) * min(
            1.0, dt * 15.0
        )

        wheel_circumference = 2.0 * math.pi * self.wheel_radius
        self.wheel_angle = (
            self.wheel_angle
            + (self.speed / 3.6)
            / max(0.01, wheel_circumference)
            * 360.0
            * dt
        ) % 360.0

    def update_enemies(self, dt):
        if self.speed > 5.0 and not self.crashed:
            spawn_rate = 0.05 + (self.speed / 100.0) * 0.4
            if random.random() < spawn_rate:
                enemy_type = random.choices(
                    ["fly", "bee", "mosquito", "ufo"],
                    weights=[0.5, 0.25, 0.2, 0.05],
                )[0]
                angle = random.uniform(0, math.pi * 2)
                self.enemies.append(
                    {
                        "type": enemy_type,
                        "x": math.cos(angle) * random.uniform(0.1, 0.8),
                        "y": math.sin(angle) * random.uniform(0.1, 0.8),
                        "z": 1.0,
                        "vx": random.uniform(-0.1, 0.1),
                        "vy": random.uniform(-0.1, 0.1),
                        "speed": random.uniform(0.8, 1.5),
                    }
                )

        speed_mult = max(0.4, self.speed / 35.0)
        survived = []
        w = max(650, self.canvas.winfo_width())
        h = max(500, self.canvas.winfo_height())

        for e in self.enemies:
            e["z"] -= dt * 1.2 * speed_mult * e["speed"]
            e["x"] += e["vx"] * dt
            e["y"] += e["vy"] * dt

            if e["z"] <= 0.05:
                cx = w / 2 + e["x"] * (w / 2)
                cy = h / 2 + e["y"] * (h / 2)

                if e["type"] == "ufo":
                    self.glitch_timer = 0.5
                    self.explosions.append(
                        {"x": cx, "y": cy, "radius": 40, "life": 0.5}
                    )
                else:
                    color_map = {
                        "fly": random.choice(["#2d3748", "#111827", "#3f6212"]),
                        "bee": "#eab308",
                        "mosquito": "#dc2626",
                    }
                    self.splats.append(
                        {
                            "x": cx,
                            "y": cy,
                            "radius": random.uniform(8, 22)
                            * (self.speed / 80.0 + 0.5),
                            "life": random.uniform(5.0, 10.0),
                            "color": color_map[e["type"]],
                        }
                    )
            else:
                survived.append(e)

        self.enemies = survived

        for ex in self.explosions:
            ex["life"] -= dt
        self.explosions = [ex for ex in self.explosions if ex["life"] > 0]

        for splat in self.splats:
            splat["life"] -= dt
        self.splats = [s for s in self.splats if s["life"] > 0]

    def update_labels(self):
        self.speed_var.set(f"{self.speed:5.1f}")
        self.gear_var.set(str(self.gear))
        self.nitro_var.set(f"{self.nitro_fuel:3.0f}%")
        self.temp_var.set(f"{self.engine_temp:3.0f} °C")
        self.distance_var.set(f"{self.distance:7.3f} км")

        if self.engine_state == "off":
            hint = "Space — запустить двигатель"
        elif self.nitro_active:
            hint = "🔥 НИТРО АКТИВИРОВАНО!"
        elif self.laser_active_timer > 0:
            hint = "⚡ ЛАЗЕРНЫЙ ЗАЛП!"
        else:
            turn, dist = self.upcoming_turn()
            hint = (
                f"{turn} через {dist:.0f} м" if turn != "ПРЯМО" else "Трасса свободна"
            )
        self.speed_hint.config(text=hint)

    def update_status(self):
        if self.crashed:
            self.status_label.config(text="✕ СТОЛКНОВЕНИЕ", fg=self.RED)
            self.engine_button.config(text="СБРОСИТЬ СОСТОЯНИЕ")
        elif self.engine_state == "off":
            self.status_label.config(text="● ДВИГАТЕЛЬ ВЫКЛЮЧЕН", fg=self.MUTED)
            self.engine_button.config(text="ЗАПУСТИТЬ ДВИГАТЕЛЬ")
        elif self.engine_state == "starting":
            self.status_label.config(text="◉ ЗАПУСК...", fg=self.YELLOW)
            self.engine_button.config(text="ИДЕТ ЗАПУСК...")
        else:
            self.status_label.config(text="● ДВИГАТЕЛЬ РАБОТАЕТ", fg=self.GREEN)
            self.engine_button.config(text="ВЫКЛЮЧИТЬ ДВИГАТЕЛЬ")

    def draw_scene(self):
        c = self.canvas
        w = max(650, c.winfo_width())
        h = max(500, c.winfo_height())
        c.delete("all")

        horizon = int(h * 0.40) + int(self.cam_offset_y)
        center = w * 0.50 + self.cam_offset_x

        if self.nitro_active:
            sky_colors = ["#2e1065", "#581c87", "#7e22ce", "#a855f7"]
        else:
            sky_colors = ["#030509", "#0a0d18", "#121829", "#1c2438"]

        band_h = horizon / len(sky_colors)
        for i, col in enumerate(sky_colors):
            c.create_rectangle(
                0,
                int(i * band_h),
                w,
                int((i + 1) * band_h) + 1,
                fill=col,
                outline="",
            )

        sun_color = "#ff0055" if self.nitro_active else "#e63946"
        sun_y = horizon - 15
        c.create_oval(
            center - 80,
            sun_y - 80,
            center + 80,
            sun_y + 80,
            fill=sun_color,
            outline="",
        )
        c.create_oval(
            center - 60, sun_y - 60, center + 60, sun_y + 60, fill="#f1faee", outline=""
        )

        mountains = [
            (0, horizon),
            (w * 0.12, horizon - 30),
            (w * 0.28, horizon - 75),
            (w * 0.45, horizon - 25),
            (w * 0.58, horizon - 85),
            (w * 0.75, horizon - 20),
            (w * 0.88, horizon - 65),
            (w, horizon),
        ]
        c.create_polygon(mountains, fill="#080b12", outline="#1e293b", width=1)
        c.create_rectangle(0, horizon, w, h, fill="#0a0c10", outline="")

        top_y = horizon
        bottom_y = h + 20
        top_half = w * 0.05
        bottom_half = w * 0.58

        current_offset = self.route_offset(self.distance)
        samples = 22
        left_edge, right_edge, road_centers = [], [], []

        for i in range(samples + 1):
            t = i / samples
            depth_km = t * (0.6 + self.speed * 0.003)
            d = self.distance + depth_km
            rel = self.route_offset(d) - current_offset
            curve_px = rel * (w * 0.4)
            y = top_y + (bottom_y - top_y) * (t**1.8)
            half = top_half + (bottom_half - top_half) * (t**1.4)
            cx = center + curve_px
            left_edge.append((cx - half, y))
            right_edge.append((cx + half, y))
            road_centers.append((cx, y))

        road_poly = left_edge + list(reversed(right_edge))
        c.create_polygon(
            [v for pt in road_poly for v in pt], fill="#14171f", outline=""
        )

        edge_color = "#00f0ff" if self.nitro_active else "#1AE000"
        c.create_line([v for pt in left_edge for v in pt], fill=edge_color, width=2)
        c.create_line(
            [v for pt in right_edge for v in pt], fill=edge_color, width=2
        )

        scroll_phase = (
            (self.road_time * (self.speed / 35.0)) % 1.0
            if self.speed > 0.5
            else 0.0
        )
        for i in range(14):
            t = (i / 14.0 + scroll_phase * 0.071) % 1.0
            idx = min(samples, int(t * samples))
            cx, y = road_centers[idx]
            dash_len = max(4, 10 + 40 * t)
            width = max(2, int(1 + 6 * t))
            c.create_rectangle(
                cx - width / 2,
                y,
                cx + width / 2,
                min(bottom_y, y + dash_len),
                fill="#f8fafc",
                outline="",
            )

        for e in self.enemies:
            scale_f = 1.0 / max(0.01, e["z"])
            fx = center + e["x"] * w * scale_f * 0.3
            fy = horizon + e["y"] * h * scale_f * 0.3
            cur_size = max(2, 6 * scale_f * 0.3)

            if 0 <= fx <= w and 0 <= fy <= h:
                if e["type"] == "fly":
                    c.create_oval(
                        fx - cur_size,
                        fy - cur_size,
                        fx + cur_size,
                        fy + cur_size,
                        fill="#0f172a",
                    )
                elif e["type"] == "bee":
                    c.create_oval(
                        fx - cur_size * 1.3,
                        fy - cur_size,
                        fx + cur_size * 1.3,
                        fy + cur_size,
                        fill="#eab308",
                    )
                elif e["type"] == "mosquito":
                    c.create_line(
                        fx - cur_size,
                        fy - cur_size,
                        fx + cur_size,
                        fy + cur_size,
                        fill="#dc2626",
                        width=2,
                    )
                elif e["type"] == "ufo":
                    c.create_oval(
                        fx - cur_size * 2,
                        fy - cur_size * 0.8,
                        fx + cur_size * 2,
                        fy + cur_size * 0.8,
                        fill="#a855f7",
                    )
                    c.create_oval(
                        fx - cur_size,
                        fy - cur_size * 1.2,
                        fx + cur_size,
                        fy,
                        fill="#00f0ff",
                    )

        for ex in self.explosions:
            c.create_oval(
                ex["x"] - ex["radius"],
                ex["y"] - ex["radius"],
                ex["x"] + ex["radius"],
                ex["y"] + ex["radius"],
                fill="#ff0055",
                outline="#facc15",
                width=3,
            )

        road_visual_shift = self.lateral * 30.0
        bike_x = center + road_visual_shift + self.wobble * 10.0
        bike_y = h * 0.82 + self.cam_shake + self.pitch * 2.0
        scale = min(w, h) / 600.0

        # Отрисовка байка
        self.draw_ninja_first_person(c, bike_x, bike_y, scale, self.roll, self.steer)

        # ---------------- Привязка Лазеров к Мотоциклу ----------------
        if self.laser_active_timer > 0:
            rad = math.radians(self.roll)
            cos_r, sin_r = math.cos(rad), math.sin(rad)

            def get_headlight_pos(lx, ly):
                sx, sy = lx * scale, ly * scale
                rx = sx * cos_r - sy * sin_r
                ry = sx * sin_r + sy * cos_r
                return bike_x + rx, bike_y + ry

            # Координаты левой и правой фары байка
            left_hl = get_headlight_pos(-60, -25)
            right_hl = get_headlight_pos(60, -25)

            target_left = (center - w * 0.1, horizon)
            target_right = (center + w * 0.1, horizon)

            c.create_line(
                left_hl[0],
                left_hl[1],
                target_left[0],
                target_left[1],
                fill="#00f0ff",
                width=6,
            )
            c.create_line(
                right_hl[0],
                right_hl[1],
                target_right[0],
                target_right[1],
                fill="#00f0ff",
                width=6,
            )
            c.create_line(
                left_hl[0],
                left_hl[1],
                target_left[0],
                target_left[1],
                fill="#ffffff",
                width=2,
            )
            c.create_line(
                right_hl[0],
                right_hl[1],
                target_right[0],
                target_right[1],
                fill="#ffffff",
                width=2,
            )

        for splat in self.splats:
            r = splat["radius"]
            sx, sy = splat["x"], splat["y"]
            c.create_oval(
                sx - r,
                sy - r * 0.7,
                sx + r,
                sy + r * 0.7,
                fill=splat["color"],
                outline="#facc15",
                width=1,
            )
            c.create_oval(
                sx - r * 0.4,
                sy - r * 0.3,
                sx + r * 0.4,
                sy + r * 0.3,
                fill="#84cc16",
                outline="",
            )

        if self.glitch_timer > 0:
            for _ in range(8):
                gx = random.randint(0, int(w))
                gy = random.randint(0, int(h))
                gw = random.randint(50, 200)
                gh = random.randint(5, 20)
                c.create_rectangle(
                    gx,
                    gy,
                    gx + gw,
                    gy + gh,
                    fill=random.choice(["#ff0055", "#00f0ff", "#facc15"]),
                )

        c.create_rectangle(
            12, h - 36, w - 12, h - 12, fill="#0d1117", outline="#21262d"
        )
        bottom_str = (
            f"  GEAR: {self.gear}  |  THROTTLE: {self.throttle*100:3.0f}%  |  "
            f"BRAKE: {self.brake*100:3.0f}%  |  N2O: {self.nitro_fuel:3.0f}%"
        )
        c.create_text(
            20,
            h - 24,
            anchor="w",
            text=bottom_str,
            fill="#8b949e",
            font=("Consolas", 9, "bold"),
        )

    def draw_ninja_first_person(self, c, cx, cy, scale, roll_deg, steer_val):
        rad = math.radians(roll_deg)
        cos_r = math.cos(rad)
        sin_r = math.sin(rad)

        def tr(x, y):
            sx, sy = x * scale, y * scale
            rx = sx * cos_r - sy * sin_r
            ry = sx * sin_r + sy * cos_r
            return cx + rx, cy + ry

        def poly(pts, **kw):
            t_pts = []
            for x, y in pts:
                tx, ty = tr(x, y)
                t_pts.extend([tx, ty])
            return c.create_polygon(t_pts, **kw)

        def line(pt1, pt2, **kw):
            x1, y1 = tr(*pt1)
            x2, y2 = tr(*pt2)
            return c.create_line(x1, y1, x2, y2, **kw)

        def oval(pt1, pt2, **kw):
            x1, y1 = tr(*pt1)
            x2, y2 = tr(*pt2)
            return c.create_oval(x1, y1, x2, y2, **kw)

        def text(pt, txt, **kw):
            tx, ty = tr(*pt)
            return c.create_text(tx, ty, text=txt, angle=-roll_deg, **kw)

        steer_px = steer_val * 25.0

        body_color = "#ff0055" if self.nitro_active else self.COLOR_GREEN
        poly(
            [
                (-120, -100),
                (0, -180),
                (120, -100),
                (180, 20),
                (140, 80),
                (-140, 80),
                (-180, 20),
            ],
            fill=body_color,
            outline=self.COLOR_DARK_GREEN,
            width=2,
        )
        poly(
            [(-70, -110), (0, -210), (70, -110), (90, -40), (-90, -40)],
            fill=self.COLOR_WINDSHIELD,
            outline="#1f293d",
            width=2,
        )

        glow = (
            "#00f0ff"
            if self.nitro_active
            else ("#ffffff" if self.engine_state == "running" else "#334155")
        )
        poly(
            [(-110, -30), (-40, -40), (-20, -10), (-90, -5)],
            fill=self.COLOR_HEADLIGHT,
            outline=glow,
            width=2,
        )
        poly(
            [(110, -30), (40, -40), (20, -10), (90, -5)],
            fill=self.COLOR_HEADLIGHT,
            outline=glow,
            width=2,
        )

        poly(
            [(-100, 70), (0, 30), (100, 70), (130, 180), (-130, 180)],
            fill=body_color,
            outline="#15803d",
        )
        poly(
            [(-40, 50), (0, 40), (40, 50), (50, 120), (-50, 120)],
            fill=self.COLOR_BLACK,
            outline="#262626",
        )

        poly(
            [(-80, -45), (0, -60), (80, -45), (90, 25), (-90, 25)],
            fill="#0f172a",
            outline="#334155",
            width=2,
        )
        poly([(-70, -35), (70, -35), (75, 15), (-75, 15)], fill="#020617")

        if self.engine_state == "running" or self.engine_state == "starting":
            rpm_pct = min(1.0, self.rpm / self.engine_redline)
            bar_w = 120 * rpm_pct
            bar_color = (
                self.COLOR_GREEN
                if rpm_pct < 0.8
                else (self.YELLOW if rpm_pct < 0.9 else self.RED)
            )
            poly(
                [(-60, -28), (-60 + bar_w, -28), (-60 + bar_w, -20), (-60, -20)],
                fill=bar_color,
            )

            for i in range(13):
                dx = -60 + i * 10
                line((dx, -31), (dx, -29), fill="#64748b", width=1)

            text(
                (0, -5),
                f"{int(self.speed)}",
                fill="#f8fafc",
                font=("Consolas", int(18 * scale), "bold"),
            )
            text((25, 0), "km/h", fill="#94a3b8", font=("Consolas", int(7 * scale)))

            gear_str = (
                "N"
                if (self.speed < 1.0 and self.throttle < 0.05)
                else str(self.gear)
            )
            poly(
                [(-55, -15), (-35, -15), (-35, 8), (-55, 8)],
                fill="#1e293b",
                outline="#475569",
            )
            text(
                (-45, -3),
                gear_str,
                fill="#38bdf8",
                font=("Consolas", int(14 * scale), "bold"),
            )

            text(
                (-50, 12), "N2O", fill="#ff0055", font=("Consolas", int(5 * scale))
            )
            nitro_bar_w = 20 * (self.nitro_fuel / 100.0)
            poly(
                [
                    (-35, 11),
                    (-35 + nitro_bar_w, 11),
                    (-35 + nitro_bar_w, 13),
                    (-35, 13),
                ],
                fill="#ff0055",
            )

            text(
                (20, 12),
                f"{int(self.engine_temp)}°C",
                fill="#64748b",
                font=("Consolas", int(6 * scale)),
            )

            if self.rpm > 10500 or self.shift_flash > 0:
                oval((-10, -52), (10, -42), fill="#ffffff", outline="#f85149")
        else:
            text(
                (0, -10),
                "KAWASAKI",
                fill="#1e293b",
                font=("Consolas", int(10 * scale), "bold"),
            )

        poly(
            [(-140, -110), (-230, -180), (-190, -190), (-120, -125)],
            fill=self.COLOR_BLACK,
        )
        poly(
            [(140, -110), (230, -180), (190, -190), (120, -125)],
            fill=self.COLOR_BLACK,
        )

        handle_y = 60
        line(
            (-110 + steer_px, handle_y - 10),
            (-210 + steer_px, handle_y + 15),
            fill="#1e293b",
            width=int(14 * scale),
        )
        line(
            (110 + steer_px, handle_y - 10),
            (210 + steer_px, handle_y + 15),
            fill="#1e293b",
            width=int(14 * scale),
        )

        brake_press = self.brake_lever_anim * 12.0
        line(
            (130 + steer_px, handle_y),
            (220 + steer_px - brake_press, handle_y + 10 - brake_press * 0.5),
            fill=self.COLOR_LIGHT_GRAY,
            width=int(4 * scale),
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = MotorcycleSimulator(root)
    root.mainloop()