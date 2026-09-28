import math
import random
import time
import tkinter as tk
from tkinter import ttk   


class MotorcycleSimulator:
    # -------------------------------------------------------------------------
    # ЦВЕТОВАЯ ПАЛИТРА И СТИЛИ
    # -------------------------------------------------------------------------
    BG = "#0a0c10"
    PANEL = "#11151c"
    CARD = "#161b22"
    TEXT = "#f0f6fc"
    MUTED = "#8b949e"
    ACCENT = "#ff7b72"
    CYAN = "#38d430"
    NEON_BLUE = "#58a6ff"
    NEON_PURPLE = "#bc8cff"
    GREEN = "#3fb950"
    YELLOW = "#d29922"
    RED = "#f85149"

    COLOR_GREEN = "#1AE000"
    COLOR_DARK_GREEN = "#118A00"
    COLOR_BLACK = "#121212"
    COLOR_FRAME = "#2B2B2B"
    COLOR_LIGHT_GRAY = "#D0D0D0"
    COLOR_WINDSHIELD = "#10141d"
    COLOR_HEADLIGHT = "#E8F5E9"

    def __init__(self, root):
        self.root = root
        self.root.title("Симулятор мотоцикла — Kawasaki Ninja 400")
        self.root.geometry("1280x820")
        self.root.minsize(1080, 700)
        self.root.configure(bg=self.BG)

        self.log_enabled = True
        self.log_interval = 0.5
        self.log_timer = 0.0

        # =====================================================================
        # ФИЗИЧЕСКАЯ МОДЕЛЬ И ЛОГИКА
        # =====================================================================
        self.mass = 215.0
        self.g = 9.81
        self.air_density = 1.225
        self.cd_a = 0.34
        self.rolling_coeff = 0.015
        self.drivetrain_eff = 0.91
        self.wheel_radius = 0.31

        self.engine_idle_rpm = 1250.0
        self.engine_redline = 10500.0
        self.engine_max_torque = 112.0
        self.final_drive = 2.85
        self.gear_ratios = {
            1: 2.65, 2: 1.95, 3: 1.55,
            4: 1.29, 5: 1.11, 6: 0.96,
        }
        self.max_gear = 6

        # ---------------- Состояние Мотоцикла ----------------
        self.speed = 0.0
        self.rpm = 0.0
        self.throttle = 0.0
        self.brake = 0.0
        self.gear = 1
        self.distance = 0.0
        self.fuel = 100.0
        self.engine_temp = 24.0

        self.engine_on = False
        self.engine_state = "off"        # off / starting / running
        self.start_timer = 0.0
        self.start_duration = 1.2
        self.takeoff_anim = 0.0
        self.first_move = True
        self.ignition_flash = 0.0
        self.shift_flash = 0.0

        self.steer = 0.0
        self.lateral = 0.0
        self.lateral_velocity = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.road_heading = 0.0
        self.road_distance = 0.0

        self.damage = 0.0
        self.crashed = False
        self.crash_timer = 0.0
        self.crash_vx = 0.0
        self.crash_vy = 0.0
        self.wobble = 0.0
        self.road_time = 0.0
        self.wheel_angle = 0.0
        self.headlight_phase = 0.0
        self.camera_bob = 0.0

        # Анимационные эффекты
        self.cam_offset_x = 0.0
        self.cam_offset_y = 0.0
        self.cam_shake = 0.0
        self.brake_lever_anim = 0.0

        # Динамика подвески, переноса веса и wheelie/stoppie
        self.suspension_offset = 0.0
        self.suspension_velocity = 0.0
        self.bump_phase = random.uniform(0, 1000)
        self.weight_transfer = 0.0          # -1 (зад) .. +1 (перед)
        self.wheelie = 0.0                  # 0..1 подъём переднего колеса
        self.stoppie = 0.0                  # 0..1 подъём заднего колеса
        self.wind_gust = 0.0
        self.wind_gust_timer = random.uniform(1.5, 4.0)
        self.slide = 0.0                    # занос заднего колеса 0..1

        # Частицы (выхлоп, дым, искры, пыль)
        self.particles = []

        self.keys = set()
        self.action_keys_down = set()
        self.last_time = time.perf_counter()

        self.route = self.build_route()

        self.build_ui()
        self.bind_keys()
        self.update_loop()

    def log(self, msg):
        if self.log_enabled:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    def log_state(self):
        self.log(
            f"STATE | speed={self.speed:.1f} km/h | lateral={self.lateral:.2f} m | "
            f"roll={self.roll:.1f}° | steer={self.steer:.2f} | "
            f"lateral_v={self.lateral_velocity:.2f} | "
            f"distance={self.distance:.3f} km | gear={self.gear}"
        )

    # =====================================================================
    # ИНТЕРФЕЙС И ГРАФИКА
    # =====================================================================
    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Dark.Horizontal.TProgressbar",
            troughcolor="#21262d",
            background=self.COLOR_GREEN,
            bordercolor="#21262d",
            lightcolor=self.COLOR_GREEN,
            darkcolor=self.COLOR_GREEN,
            thickness=6,
        )

        header = tk.Frame(self.root, bg=self.PANEL, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        brand = tk.Frame(header, bg=self.PANEL)
        brand.pack(side="left", padx=20)
        tk.Label(
            brand, text="KAWASAKI NINJA 400", fg=self.COLOR_GREEN, bg=self.PANEL,
            font=("Segoe UI", 9, "bold")
        ).pack(anchor="w", pady=(6, 0))
        tk.Label(
            brand, text="Симулятор мотоцикла", fg=self.TEXT, bg=self.PANEL,
            font=("Segoe UI", 15, "bold")
        ).pack(anchor="w")

        self.status_label = tk.Label(
            header, text="● ДВИГАТЕЛЬ ВЫКЛЮЧЕН",
            fg=self.RED, bg=self.PANEL,
            font=("Segoe UI", 10, "bold")
        )
        self.status_label.pack(side="right", padx=20)

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=12, pady=12)

        scene_card = tk.Frame(main, bg=self.CARD, highlightbackground="#30363d", highlightthickness=1)
        scene_card.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(scene_card, bg="#05070a", highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.build_dashboard(main)

    def build_dashboard(self, parent):
        panel = tk.Frame(parent, bg=self.PANEL, width=310)
        panel.pack(side="right", fill="y", padx=(12, 0))
        panel.pack_propagate(False)

        tk.Label(
            panel, text="ИНФОРМАЦИЯ", fg=self.MUTED, bg=self.PANEL,
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=16, pady=(14, 8))

        speed_card = tk.Frame(panel, bg=self.CARD, height=100)
        speed_card.pack(fill="x", padx=12)
        speed_card.pack_propagate(False)

        tk.Label(
            speed_card, text="СКОРОСТЬ", fg=self.MUTED, bg=self.CARD,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 0))

        speed_row = tk.Frame(speed_card, bg=self.CARD)
        speed_row.pack(anchor="w", padx=12)
        self.speed_var = tk.StringVar(value="0.0")
        tk.Label(
            speed_row, textvariable=self.speed_var, fg=self.TEXT, bg=self.CARD,
            font=("Segoe UI", 32, "bold")
        ).pack(side="left")
        tk.Label(
            speed_row, text="км/ч", fg=self.MUTED, bg=self.CARD,
            font=("Segoe UI", 10)
        ).pack(side="left", padx=(6, 0), pady=(14, 0))

        self.speed_hint = tk.Label(
            speed_card, text="Мотор выключен",
            fg="#8b949e", bg=self.CARD, font=("Segoe UI", 8)
        )
        self.speed_hint.pack(anchor="w", padx=12)

        metrics = tk.Frame(panel, bg=self.PANEL)
        metrics.pack(fill="x", padx=12, pady=10)

        self.gear_var = tk.StringVar(value="1")
        self.fuel_var = tk.StringVar(value="100%")
        self.temp_var = tk.StringVar(value="24 °C")
        self.distance_var = tk.StringVar(value="0.000 км")

        self.metric_card(metrics, 0, 0, "ПЕРЕДАЧА", self.gear_var, 18)
        self.metric_card(metrics, 0, 1, "ТОПЛИВО", self.fuel_var, 14)
        self.metric_card(metrics, 1, 0, "ТЕМПЕРАТУРА", self.temp_var, 14)
        self.metric_card(metrics, 1, 1, "ДИСТАНЦИЯ", self.distance_var, 12)

        controls_card = tk.Frame(panel, bg=self.CARD)
        controls_card.pack(fill="x", padx=12, pady=(10, 0))

        tk.Label(
            controls_card, text="УПРАВЛЕНИЕ", fg=self.TEXT, bg=self.CARD,
            font=("Segoe UI", 8, "bold")
        ).pack(anchor="w", padx=12, pady=(6, 2))

        controls = [
            ("W / ↑", "Газ"), ("S / ↓", "Тормоз"),
            ("A / D", "Руление"), ("Q / E", "Передача − / +"),
            ("Space", "Зажигание"), ("R", "Сброс"),
        ]
        for key, desc in controls:
            row = tk.Frame(controls_card, bg=self.CARD)
            row.pack(fill="x", padx=12, pady=2)
            tk.Label(
                row, text=key, fg=self.TEXT, bg="#21262d",
                font=("Consolas", 8, "bold"), padx=4, pady=1
            ).pack(side="left")
            tk.Label(
                row, text=desc, fg=self.MUTED, bg=self.CARD,
                font=("Segoe UI", 8)
            ).pack(side="left", padx=6)

        buttons = tk.Frame(panel, bg=self.PANEL)
        buttons.pack(side="bottom", fill="x", padx=12, pady=10)

        self.engine_button = tk.Button(
            buttons, text="ЗАПУСТИТЬ ДВИГАТЕЛЬ",
            command=self.handle_engine_button,
            bg="#21262d", fg=self.TEXT,
            activebackground="#30363d", activeforeground=self.TEXT,
            relief="flat", borderwidth=0,
            font=("Segoe UI", 9, "bold"), padx=8, pady=6, cursor="hand2",
        )
        self.engine_button.pack(fill="x", pady=2)

        tk.Button(
            buttons, text="СБРОСИТЬ СИМУЛЯЦИЮ",
            command=self.reset,
            bg="#238636", fg="white",
            activebackground="#2ea043", activeforeground="white",
            relief="flat", borderwidth=0,
            font=("Segoe UI", 9, "bold"), padx=8, pady=6, cursor="hand2",
        ).pack(fill="x", pady=2)

    def metric_card(self, parent, r, c, title, variable, size):
        card = tk.Frame(parent, bg=self.CARD, height=55)
        card.grid(row=r, column=c, sticky="nsew", padx=2, pady=2)
        parent.grid_columnconfigure(c, weight=1)
        card.pack_propagate(False)

        tk.Label(
            card, text=title, fg=self.MUTED, bg=self.CARD,
            font=("Segoe UI", 7, "bold")
        ).pack(anchor="w", padx=8, pady=(4, 0))
        tk.Label(
            card, textvariable=variable, fg=self.TEXT, bg=self.CARD,
            font=("Segoe UI", size, "bold")
        ).pack(anchor="w", padx=8)

    def bind_keys(self):
        self.root.bind_all("<KeyPress>", self.on_key_press, add="+")
        self.root.bind_all("<KeyRelease>", self.on_key_release, add="+")
        self.root.focus_force()

    def normalize_key(self, event):
        code_map = {65: "a", 68: "d", 69: "e", 81: "q", 82: "r", 83: "s", 87: "w"}
        if getattr(event, "keycode", None) in code_map:
            return code_map[event.keycode]
        aliases = {"ц": "w", "ф": "a", "ы": "s", "в": "d", "й": "q", "у": "e", "к": "r"}
        return aliases.get(event.keysym.lower(), event.keysym.lower())

    def on_key_press(self, event):
        key = self.normalize_key(event)
        self.keys.add(key)
        
        # Защита от автоповтора ОС при зажатии клавиш
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
        self.log("Engine starting...")
        if self.fuel <= 0:
            return
        self.engine_state = "starting"
        self.engine_on = False
        self.start_timer = 0.0
        self.rpm = 0.0
        self.ignition_flash = 0.0

    def stop_engine(self):
        self.log("Engine stopped")
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
        self.engine_temp = 24.0

        self.engine_on = False
        self.engine_state = "off"
        self.start_timer = 0.0
        self.takeoff_anim = 0.0
        self.first_move = True
        self.ignition_flash = 0.0
        self.shift_flash = 0.0

        self.steer = 0.0
        self.lateral = 0.0
        self.lateral_velocity = 0.0
        self.roll = 0.0
        self.pitch = 0.0
        self.road_heading = 0.0
        self.road_distance = 0.0

        self.damage = 0.0
        self.crashed = False
        self.crash_timer = 0.0
        self.crash_vx = 0.0
        self.crash_vy = 0.0
        self.wobble = 0.0
        self.wheel_angle = 0.0
        self.headlight_phase = 0.0
        self.camera_bob = 0.0

        self.suspension_offset = 0.0
        self.suspension_velocity = 0.0
        self.weight_transfer = 0.0
        self.wheelie = 0.0
        self.stoppie = 0.0
        self.wind_gust = 0.0
        self.wind_gust_timer = random.uniform(1.5, 4.0)
        self.slide = 0.0
        self.particles = []

    def set_gear(self, gear):
        if self.engine_state != "running":
            return
        new_gear = max(1, min(self.max_gear, gear))
        if new_gear != self.gear:
            self.log(f"Gear shifted to {new_gear} (was {self.gear})")
            self.gear = new_gear
            self.shift_flash = 0.22
            self.rpm *= 0.82

    # =====================================================================
    # ЛОГИКА ТРАССЫ И РАСЧЕТОВ
    # =====================================================================
    def build_route(self):
        rng = random.Random(2026)
        segments = []
        for _ in range(32):
            straight = rng.uniform(0.22, 0.65)
            segments.append({"length": straight, "curve": 0.0})
            if rng.random() < 0.78:
                turn_len = rng.uniform(0.20, 0.52)
                sign = rng.choice([-1.0, 1.0])
                strength = rng.uniform(0.65, 1.35)
                segments.append({"length": turn_len, "curve": sign * strength})
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
        d = self.distance % total
        passed = 0.0
        for idx, seg in enumerate(self.route):
            if d <= passed + seg["length"]:
                next_idx = (idx + 1) % len(self.route)
                next_seg = self.route[next_idx]
                if abs(next_seg["curve"]) > 0.15:
                    remaining = (passed + seg["length"] - d) * 1000.0
                    return ("ЛЕВЫЙ поворот" if next_seg["curve"] > 0 else "ПРАВЫЙ поворот", remaining)
                return "ПРЯМО", 0.0
            passed += seg["length"]
        return "ПРЯМО", 0.0

    def max_speed_for_current_gear(self):
        ratio = self.gear_ratios[self.gear] * self.final_drive
        wheel_rpm = self.engine_redline / ratio
        wheel_rps = wheel_rpm / 60.0
        v = wheel_rps * (2.0 * math.pi * self.wheel_radius)
        return v * 3.6

    def torque_curve(self, rpm):
        x = max(0.0, min(1.0, (rpm - 1800.0) / 8200.0))
        peak = math.exp(-((x - 0.62) / 0.32) ** 2)
        low_end = 0.72 + 0.20 * x
        torque = self.engine_max_torque * (0.72 + 0.28 * peak) * low_end
        if rpm > 9000:
            torque *= max(0.70, 1.0 - (rpm - 9000.0) / 4500.0)
        return max(35.0, torque)

    # =====================================================================
    # ЦИКЛ ОБНОВЛЕНИЯ И ФИЗИЧЕСКАЯ СИМУЛЯЦИЯ
    # =====================================================================
    def update_loop(self):
        now = time.perf_counter()
        dt = min(0.035, max(0.001, now - self.last_time))
        self.last_time = now

        self.road_time += dt
        self.log_timer += dt
        if self.log_timer >= self.log_interval:
            self.log_state()
            self.log_timer = 0.0

        self.read_inputs(dt)
        self.simulate_startup(dt)
        self.simulate(dt)
        self.update_particles(dt)
        self.animate(dt)
        self.update_labels()
        self.update_status()
        self.draw_scene()

        self.root.after(16, self.update_loop)

    def read_inputs(self, dt):
        up = "w" in self.keys or "up" in self.keys
        down = "s" in self.keys or "down" in self.keys
        left = "a" in self.keys or "left" in self.keys
        right = "d" in self.keys or "right" in self.keys

        target_throttle = 1.0 if up and self.engine_state == "running" else 0.0
        target_brake = 1.0 if down else 0.0

        self.throttle += (target_throttle - self.throttle) * min(1.0, 12.0 * dt)
        self.brake += (target_brake - self.brake) * min(1.0, 18.0 * dt)

        target_steer = (-1.0 if left else 0.0) + (1.0 if right else 0.0)
        self.steer += (target_steer - self.steer) * min(1.0, 12.0 * dt)

    def simulate_startup(self, dt):
        if self.engine_state != "starting":
            return

        self.start_timer += dt
        t = min(1.0, self.start_timer / self.start_duration)

        if t < 0.20:
            p = t / 0.20
            self.rpm = 900 + 2800 * p
        elif t < 0.45:
            p = (t - 0.20) / 0.25
            self.rpm = 3700 + 3300 * math.sin(p * math.pi * 1.6)
            self.ignition_flash = max(0.0, math.sin(p * math.pi * 5.0)) * 0.9
        elif t < 0.72:
            p = (t - 0.45) / 0.27
            self.rpm = 2400 + (1 - p) * 700 + 280 * math.sin(p * math.pi * 6)
        else:
            p = (t - 0.72) / 0.28
            self.rpm = 1950 - 700 * p

        self.ignition_flash = max(self.ignition_flash, max(0.0, math.sin(self.start_timer * 30.0)) * 0.22)

        if self.start_timer >= self.start_duration:
            self.engine_state = "running"
            self.engine_on = True
            self.rpm = self.engine_idle_rpm
            self.engine_temp = 65.0

    def simulate(self, dt):
        if self.crashed:
            self.animate_crash(dt)
            return

        if self.engine_state != "running":
            if self.engine_state == "off":
                self.rpm += (0.0 - self.rpm) * min(1.0, dt * 4.0)
                self.speed = max(0.0, self.speed - 2.6 * dt)
                self.lateral_velocity *= max(0.0, 1.0 - dt * 3.0)
                self.lateral += self.lateral_velocity * dt
            return

        velocity = self.speed / 3.6
        overall_ratio = self.gear_ratios[self.gear] * self.final_drive
        wheel_rps = velocity / max(0.01, 2.0 * math.pi * self.wheel_radius)
        locked_rpm = wheel_rps * 60.0 * overall_ratio

        clutch_slip = max(0.0, math.exp(-velocity * 0.3))
        target_rpm = max(
            self.engine_idle_rpm,
            locked_rpm + clutch_slip * 1800.0 * self.throttle,
        )
        self.rpm += (target_rpm - self.rpm) * min(1.0, dt * 10.0)
        self.rpm = max(self.engine_idle_rpm, min(self.engine_redline, self.rpm))

        engine_torque = self.torque_curve(self.rpm) * self.throttle
        wheel_force = engine_torque * overall_ratio * self.drivetrain_eff / self.wheel_radius
        max_traction = self.mass * self.g * 0.9
        wheel_force = min(wheel_force, max_traction)

        aero_force = 0.5 * self.air_density * self.cd_a * velocity * velocity
        rolling_force = self.rolling_coeff * self.mass * self.g

        engine_brake = 0.0
        if self.throttle < 0.05 and velocity > 0.5:
            # Чем ниже передача, тем сильнее торможение двигателем
            gear_factor = 1.55 - 0.10 * self.gear
            engine_brake = min(150.0, (15.0 + velocity * 1.5 + self.rpm * 0.002) * gear_factor)

        brake_force = self.mass * self.g * 1.2 * self.brake
        net_force = wheel_force - aero_force - rolling_force - engine_brake - brake_force
        acceleration = net_force / self.mass

        # ---------- Перенос веса, wheelie/stoppie ----------
        # Продольное ускорение смещает нагрузку между колёсами
        target_weight_transfer = max(-1.0, min(1.0, -acceleration * 0.16))
        self.weight_transfer += (target_weight_transfer - self.weight_transfer) * min(1.0, dt * 6.0)

        target_wheelie = 0.0
        if self.gear <= 2 and velocity < 40.0 and acceleration > 3.2:
            target_wheelie = min(1.0, (acceleration - 3.2) / 4.0) * (1.0 - velocity / 45.0)
        self.wheelie += (target_wheelie - self.wheelie) * min(1.0, dt * 5.0)
        self.wheelie = max(0.0, self.wheelie)

        target_stoppie = 0.0
        if self.brake > 0.85 and velocity > 20.0:
            target_stoppie = min(1.0, (self.brake - 0.85) / 0.15) * min(1.0, velocity / 60.0)
        self.stoppie += (target_stoppie - self.stoppie) * min(1.0, dt * 6.0)
        self.stoppie = max(0.0, self.stoppie)

        # Тяга падает, когда переднее колесо в воздухе (сложнее рулить/тормозить)
        if self.wheelie > 0.4:
            acceleration *= max(0.4, 1.0 - (self.wheelie - 0.4) * 0.6)

        self.speed += acceleration * dt
        self.speed = max(0.0, min(270.0, self.speed))

        if self.rpm >= self.engine_redline - 30 and self.throttle > 0.95:
            self.speed = min(self.speed, self.max_speed_for_current_gear() * 0.99)

        road_slope = self.route_slope(self.distance)
        road_center_velocity = velocity * road_slope

        # Порывы бокового ветра на высокой скорости — добавляют непредсказуемости
        self.wind_gust_timer -= dt
        if self.wind_gust_timer <= 0.0:
            self.wind_gust_timer = random.uniform(2.0, 5.0)
            self.wind_gust = random.uniform(-1.0, 1.0) * min(1.0, velocity / 90.0)
        self.wind_gust *= max(0.0, 1.0 - dt * 0.8)

        steering_strength = 0.8 + 0.035 * velocity
        desired_lateral_speed = self.steer * steering_strength + self.wind_gust * 0.6

        curve_follow = road_center_velocity * 0.30

        lateral_accel = (
            (desired_lateral_speed - self.lateral_velocity)
            * 5.0 + curve_follow * 2.0
        )
        self.lateral_velocity += lateral_accel * dt
        self.lateral += self.lateral_velocity * dt

        road_limit = 15.0

        turn_load = abs(self.steer) * max(0.0, velocity - 9.0) / 22.0
        if turn_load > 0.95:
            self.wobble += (turn_load - 0.95) * dt * 1.8
        else:
            self.wobble = max(0.0, self.wobble - dt * 0.6)

        desired_roll = (
            self.steer * min(65.0, velocity * 1.2)
            + road_slope * min(40.0, velocity * 0.4)
        )
        max_safe_roll = 62.0 + min(15.0, velocity * 0.045)
        # Торможение или резкий газ во время наклона снижают запас сцепления
        max_safe_roll -= abs(self.weight_transfer) * 6.0
        self.roll += (desired_roll - self.roll) * min(1.0, dt * 15.0)

        # Лёгкое покачивание подвески от неровностей дороги
        bump_noise = math.sin((self.distance * 1000.0 + self.bump_phase) * 0.9) * 0.5
        bump_noise += math.sin((self.distance * 1000.0 + self.bump_phase) * 2.7) * 0.25
        target_susp = bump_noise * min(1.0, velocity / 50.0) * 3.0
        self.suspension_velocity += (target_susp - self.suspension_offset) * dt * 40.0
        self.suspension_velocity *= max(0.0, 1.0 - dt * 6.0)
        self.suspension_offset += self.suspension_velocity * dt

        self.pitch = (
            (self.throttle - self.brake) * 3.2
            - self.wheelie * 14.0
            + self.stoppie * 10.0
            + self.suspension_offset
        )

        # Занос заднего колеса: избыток тяги в повороте на большом наклоне
        traction_demand = (abs(self.roll) / max_safe_roll) + (wheel_force / max(1.0, max_traction)) * 0.4
        target_slide = max(0.0, traction_demand - 1.0) * 1.6 if velocity > 12.0 else 0.0
        self.slide += (target_slide - self.slide) * min(1.0, dt * 6.0)

        offroad = abs(self.lateral) > road_limit
        high_side_load = (
            velocity > 25.0 and
            abs(self.roll) > max_safe_roll and
            abs(self.steer) > 0.75
        )
        hard_crash = (
            self.brake > 0.95 and
            velocity > 72.0 and
            abs(self.steer) > 0.82
        )
        traction_loss_crash = self.slide > 1.0 and velocity > 20.0

        if offroad or high_side_load or hard_crash or traction_loss_crash:
            excess = 0.0
            if offroad:
                excess += max(0.0, abs(self.lateral) - road_limit) * 2.2
            if high_side_load:
                excess += max(0.0, abs(self.roll) - max_safe_roll) * 1.8
            if hard_crash:
                excess += 12.0
            if traction_loss_crash:
                excess += (self.slide - 1.0) * 10.0
            self.crash_vx = self.lateral_velocity
            self.crash_vy = -max(2.0, velocity * 0.25)
            self.trigger_crash(min(100.0, 35.0 + excess * 3.0))

        # ---------- Частицы выхлопа ----------
        if self.engine_state == "running" and random.random() < 0.55:
            self.spawn_exhaust_particle()

        self.distance += velocity * dt / 1000.0

        fuel_rate = 0.000018 * self.rpm + 0.00055 * self.throttle
        self.fuel = max(0.0, self.fuel - fuel_rate * dt)
        if self.fuel <= 0:
            self.stop_engine()

        target_temp = 65.0 + 0.0018 * self.rpm + 7.5 * self.throttle + 0.025 * velocity
        self.engine_temp += (target_temp - self.engine_temp) * min(1.0, dt * 0.7)
        self.engine_temp = max(65.0, min(112.0, self.engine_temp))

        self.road_distance = self.distance

    def trigger_crash(self, initial_damage=35.0):
        if self.crashed:
            return
        self.crashed = True
        self.crash_timer = 0.0
        self.damage = max(self.damage, min(100.0, initial_damage))
        self.engine_state = "off"
        self.engine_on = False
        self.throttle = 0.0
        self.brake = 0.0
        self.rpm = max(0.0, self.rpm * 0.35)
        self.crash_vx = self.crash_vx if abs(self.crash_vx) > 0.5 else self.steer * 4.0
        self.crash_vy = self.crash_vy if abs(self.crash_vy) > 0.5 else -4.0
        for _ in range(26):
            self.spawn_spark_particle()

    def animate_crash(self, dt):
        self.crash_timer += dt
        self.lateral += self.crash_vx * dt
        self.speed = max(0.0, self.speed - 42.0 * dt)
        self.roll += self.crash_vx * dt * 8.0
        self.pitch += self.crash_vy * dt * 2.0
        self.crash_vx *= max(0.0, 1.0 - dt * 2.2)
        self.crash_vy *= max(0.0, 1.0 - dt * 1.8)

        if self.crash_timer > 0.55:
            self.damage = min(100.0, self.damage + dt * 3.0)

        if random.random() < 0.6:
            self.spawn_dust_particle()

    # -------------------------------------------------------------------
    # ЧАСТИЦЫ (выхлоп, искры, пыль)
    # -------------------------------------------------------------------
    def spawn_exhaust_particle(self):
        strength = 0.3 + 0.7 * self.throttle
        self.particles.append({
            "type": "smoke",
            "x": random.uniform(-6, 6),
            "y": random.uniform(-4, 4),
            "vx": random.uniform(-8, 8),
            "vy": -30 - 40 * strength,
            "life": random.uniform(0.35, 0.65),
            "age": 0.0,
            "size": random.uniform(3, 6) * (0.6 + strength),
        })

    def spawn_spark_particle(self):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(60, 260)
        self.particles.append({
            "type": "spark",
            "x": 0.0, "y": 0.0,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed * 0.6 - 40,
            "life": random.uniform(0.25, 0.55),
            "age": 0.0,
            "size": random.uniform(1.5, 3.0),
        })

    def spawn_dust_particle(self):
        self.particles.append({
            "type": "dust",
            "x": random.uniform(-40, 40),
            "y": random.uniform(-5, 5),
            "vx": random.uniform(-20, 20) + self.crash_vx * 10.0,
            "vy": random.uniform(-25, -5),
            "life": random.uniform(0.5, 1.0),
            "age": 0.0,
            "size": random.uniform(4, 9),
        })

    def update_particles(self, dt):
        alive = []
        for p in self.particles:
            p["age"] += dt
            if p["age"] >= p["life"]:
                continue
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["vy"] += 60.0 * dt  # лёгкая гравитация/торможение
            p["vx"] *= max(0.0, 1.0 - dt * 1.2)
            alive.append(p)
        self.particles = alive[-220:]

    def animate(self, dt):
        if self.shift_flash > 0:
            self.shift_flash = max(0.0, self.shift_flash - dt)

        # Динамика камеры от первого лица
        target_cam_x = -self.roll * 1.5
        target_cam_y = self.brake * 12.0 - self.throttle * 6.0
        self.cam_offset_x += (target_cam_x - self.cam_offset_x) * min(1.0, dt * 8.0)
        self.cam_offset_y += (target_cam_y - self.cam_offset_y) * min(1.0, dt * 8.0)

        rpm_factor = (self.rpm / self.engine_redline) if self.engine_on else 0.0
        speed_factor = min(1.0, self.speed / 150.0)
        shake_amplitude = (rpm_factor * 1.5) + (speed_factor * 2.5)
        self.cam_shake = math.sin(self.road_time * 40.0) * shake_amplitude

        self.brake_lever_anim += (self.brake - self.brake_lever_anim) * min(1.0, dt * 15.0)

        wheel_circumference = 2.0 * math.pi * self.wheel_radius
        self.wheel_angle = (
            self.wheel_angle +
            (self.speed / 3.6) / max(0.01, wheel_circumference) * 360.0 * dt
        ) % 360.0

    def update_labels(self):
        self.speed_var.set(f"{self.speed:5.1f}")
        self.gear_var.set(str(self.gear))
        self.fuel_var.set(f"{self.fuel:4.1f}%")
        self.temp_var.set(f"{self.engine_temp:3.0f} °C")
        self.distance_var.set(f"{self.distance:7.3f} км")

        if self.engine_state == "off":
            hint = "Space — запустить двигатель"
        elif self.engine_state == "starting":
            hint = "Стартер..."
        else:
            turn, dist = self.upcoming_turn()
            if turn != "ПРЯМО":
                hint = f"{turn} через {dist:.0f} м"
            else:
                hint = f"Предел {self.gear} передачи: ~{self.max_speed_for_current_gear():.0f} км/ч"
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
        elif self.rpm >= self.engine_redline - 150:
            self.status_label.config(text="● КРАСНАЯ ЗОНА", fg=self.RED)
            self.engine_button.config(text="ВЫКЛЮЧИТЬ ДВИГАТЕЛЬ")
        elif self.fuel < 10:
            self.status_label.config(text="● МАЛО ТОПЛИВА", fg=self.YELLOW)
            self.engine_button.config(text="ВЫКЛЮЧИТЬ ДВИГАТЕЛЬ")
        else:
            self.status_label.config(text="● ДВИГАТЕЛЬ РАБОТАЕТ", fg=self.GREEN)
            self.engine_button.config(text="ВЫКЛЮЧИТЬ ДВИГАТЕЛЬ")

    # =====================================================================
    # ОТРЕЗОВКА СЦЕНЫ
    # =====================================================================
    def draw_scene(self):
        c = self.canvas
        w = max(650, c.winfo_width())
        h = max(500, c.winfo_height())
        c.delete("all")

        horizon = int(h * 0.40) + int(self.cam_offset_y)
        center = w * 0.50 + self.cam_offset_x

        # Небо
        sky_colors = ["#030509", "#0a0d18", "#121829", "#1c2438"]
        band_h = horizon / len(sky_colors)
        for i, col in enumerate(sky_colors):
            c.create_rectangle(0, int(i * band_h), w, int((i + 1) * band_h) + 1, fill=col, outline="")

        # Звёзды (мерцание)
        star_rng = random.Random(42)
        for _ in range(70):
            sx = star_rng.uniform(0, w)
            sy = star_rng.uniform(0, horizon * 0.85)
            twinkle = 0.5 + 0.5 * math.sin(self.road_time * star_rng.uniform(1.0, 3.0) + sx)
            size = 1 if twinkle < 0.7 else 2
            col = "#8b949e" if twinkle < 0.7 else "#f0f6fc"
            c.create_oval(sx, sy, sx + size, sy + size, fill=col, outline="")

        # Дрейфующие облака
        cloud_shift = (self.road_time * 4.0) % (w + 300) - 150
        for i, cy_f in enumerate([0.18, 0.28, 0.12]):
            cx0 = (cloud_shift + i * 380) % (w + 300) - 150
            cy0 = horizon * cy_f
            for dx, dy, r in [(0, 0, 26), (28, -6, 20), (-26, -4, 18), (14, 8, 16)]:
                c.create_oval(cx0 + dx - r, cy0 + dy - r * 0.6, cx0 + dx + r, cy0 + dy + r * 0.6,
                              fill="#1c2438", outline="")

        # Солнце и горы
        sun_y = horizon - 15
        c.create_oval(center - 95, sun_y - 95, center + 95, sun_y + 95, fill="#2a0f14", outline="")
        c.create_oval(center - 80, sun_y - 80, center + 80, sun_y + 80, fill="#e63946", outline="")
        c.create_oval(center - 60, sun_y - 60, center + 60, sun_y + 60, fill="#f1faee", outline="")

        mountains = [
            (0, horizon), (w * 0.12, horizon - 30), (w * 0.28, horizon - 75),
            (w * 0.45, horizon - 25), (w * 0.58, horizon - 85), (w * 0.75, horizon - 20),
            (w * 0.88, horizon - 65), (w, horizon)
        ]
        c.create_polygon(mountains, fill="#080b12", outline="#1e293b", width=1)
        c.create_rectangle(0, horizon, w, h, fill="#0a0c10", outline="")

        # --- Перспективная дорога ---
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
            y = top_y + (bottom_y - top_y) * (t ** 1.8)
            half = top_half + (bottom_half - top_half) * (t ** 1.4)
            cx = center + curve_px
            left_edge.append((cx - half, y))
            right_edge.append((cx + half, y))
            road_centers.append((cx, y))

        # Придорожные столбы/деревья (глубина синхронизирована с дорогой)
        pole_spacing = 0.045
        pole_start = math.floor(self.distance / pole_spacing) * pole_spacing
        for k in range(-1, 26):
            pd = pole_start + k * pole_spacing
            depth_km = pd - self.distance
            if depth_km < 0 or depth_km > (0.6 + self.speed * 0.003):
                continue
            t = depth_km / max(0.001, (0.6 + self.speed * 0.003))
            rel = self.route_offset(pd) - current_offset
            curve_px = rel * (w * 0.4)
            y = top_y + (bottom_y - top_y) * (t ** 1.8)
            half = top_half + (bottom_half - top_half) * (t ** 1.4)
            cx = center + curve_px
            side = 1 if int(pd / pole_spacing) % 2 == 0 else -1
            px = cx + side * (half + 14 + 30 * t)
            pole_h = 10 + 55 * t
            is_tree = int(pd / pole_spacing) % 3 == 0
            if is_tree:
                c.create_line(px, y, px, y - pole_h * 0.6, fill="#2b1f14", width=max(1, int(3 * t)))
                r = pole_h * 0.55
                c.create_oval(px - r, y - pole_h * 0.6 - r, px + r, y - pole_h * 0.6 + r * 0.6,
                              fill="#0f2913", outline="#14401a")
            else:
                c.create_line(px, y, px, y - pole_h, fill="#3a4553", width=max(1, int(2 * t)))
                c.create_oval(px - 3 * t - 1, y - pole_h - 3, px + 3 * t + 1, y - pole_h + 3,
                              fill="#f8fafc" if self.engine_state == "running" else "#334155", outline="")

        # Полотно
        road_poly = left_edge + list(reversed(right_edge))
        c.create_polygon([v for pt in road_poly for v in pt], fill="#14171f", outline="")

        # Обочина
        c.create_line([v for pt in left_edge for v in pt], fill="#1AE000", width=2)
        c.create_line([v for pt in right_edge for v in pt], fill="#1AE000", width=2)

        # Разметка
        scroll_phase = (self.road_time * (self.speed / 35.0)) % 1.0 if self.speed > 0.5 else 0.0
        for i in range(14):
            t = (i / 14.0 + scroll_phase * 0.071) % 1.0
            idx = min(samples, int(t * samples))
            cx, y = road_centers[idx]
            dash_len = max(4, 10 + 40 * t)
            width = max(2, int(1 + 6 * t))
            c.create_rectangle(cx - width / 2, y, cx + width / 2, min(bottom_y, y + dash_len), fill="#f8fafc", outline="")

        # Эффекты скорости — линии, радиирующие от точки схода
        if self.speed > 55.0:
            vp_x, vp_y = center, horizon
            n_lines = int(min(26, self.speed / 8.0))
            blur_rng = random.Random(int(self.road_time * 1000))
            for _ in range(n_lines):
                ang = blur_rng.uniform(0, math.pi * 2)
                start_r = blur_rng.uniform(40, 90)
                length = blur_rng.uniform(30, 40) + self.speed * blur_rng.uniform(0.5, 1.3)
                x1 = vp_x + math.cos(ang) * start_r
                y1 = vp_y + math.sin(ang) * start_r * 0.6
                x2 = vp_x + math.cos(ang) * (start_r + length)
                y2 = vp_y + math.sin(ang) * (start_r + length) * 0.6
                if horizon <= y1 <= h or horizon <= y2 <= h:
                    c.create_line(x1, max(horizon, y1), x2, min(h, y2), fill="#ffffff", width=1, stipple="gray25")

        # --- ЧАСТИЦЫ (выхлоп/дым/искры), позади мотоцикла ---
        exhaust_origin_x = center + self.lateral * 30.0 - 90 * math.cos(math.radians(self.roll))
        exhaust_origin_y = h * 0.90
        for p in self.particles:
            fade = max(0.0, 1.0 - p["age"] / p["life"])
            if p["type"] == "smoke":
                col = "#4b5563" if fade > 0.4 else "#6b7280"
                r = p["size"] * (1.4 - fade * 0.6)
                ox, oy = exhaust_origin_x, exhaust_origin_y
                c.create_oval(ox + p["x"] - r, oy + p["y"] - r, ox + p["x"] + r, oy + p["y"] + r,
                              fill=col, outline="", stipple="gray50" if fade < 0.6 else "")
            elif p["type"] == "spark":
                ox, oy = w * 0.5, h * 0.78
                col = "#ffd166" if fade > 0.5 else "#f85149"
                r = p["size"] * fade
                c.create_oval(ox + p["x"] - r, oy + p["y"] - r, ox + p["x"] + r, oy + p["y"] + r,
                              fill=col, outline="")
            else:  # dust
                ox, oy = w * 0.5, h * 0.80
                r = p["size"] * (0.6 + fade * 0.8)
                c.create_oval(ox + p["x"] - r, oy + p["y"] - r, ox + p["x"] + r, oy + p["y"] + r,
                              fill="#9a8a72", outline="", stipple="gray25")

        # --- ОТРЕЗОВКА МОТОЦИКЛА ---
        road_visual_shift = self.lateral * 30.0
        bike_x = center + road_visual_shift + self.wobble * 10.0 + self.slide * 12.0 * math.sin(self.road_time * 12.0)
        bike_y = h * 0.82 + self.cam_shake + self.pitch * 2.0

        scale = (min(w, h) / 600.0)
        self.draw_ninja_first_person(c, bike_x, bike_y, scale, self.roll, self.steer)

        # Подсказка о повороте
        turn, dist = self.upcoming_turn()
        if turn != "ПРЯМО" and self.speed > 15:
            arrow = "◄" if "ЛЕВЫЙ" in turn else "►"
            x = w * 0.5 + (-100 if arrow == "◄" else 100)
            y = h * 0.22
            c.create_text(x, y, text=arrow, fill="#d29922", font=("Segoe UI", 32, "bold"))
            c.create_text(w * 0.5, y, text=f"{turn} [{dist:.0f}м]", fill="#f0f6fc", font=("Segoe UI", 10, "bold"))

        # Трещины на стекле при повреждениях
        if self.damage > 15:
            crack_rng = random.Random(7)
            n_cracks = int(self.damage / 12)
            cx0, cy0 = w * 0.5, h * 0.60
            for i in range(n_cracks):
                ang = crack_rng.uniform(0, math.pi * 2)
                seg = crack_rng.uniform(30, 90)
                x1 = cx0 + crack_rng.uniform(-40, 40)
                y1 = cy0 + crack_rng.uniform(-30, 30)
                x2 = x1 + math.cos(ang) * seg
                y2 = y1 + math.sin(ang) * seg
                c.create_line(x1, y1, x2, y2, fill="#c9d1d9", width=1, stipple="gray50")

        if self.crashed:
            c.create_rectangle(0, h * 0.36, w, h * 0.60, fill="#0d1117", outline="#f85149", width=2)
            c.create_text(w * 0.5, h * 0.43, text="SYSTEM CRASHED", fill="#f85149", font=("Segoe UI", 22, "bold"))
            c.create_text(w * 0.5, h * 0.49, text=f"Повреждения: {self.damage:.0f}%",
                          fill="#f0f6fc", font=("Segoe UI", 11, "bold"))
            c.create_text(w * 0.5, h * 0.545, text="Нажмите 'R' для перезапуска",
                          fill="#8b949e", font=("Segoe UI", 10))

        # Нижняя инфо-строка
        c.create_rectangle(12, h - 36, w - 12, h - 12, fill="#0d1117", outline="#21262d")
        bottom_str = (
            f"  GEAR: {self.gear}  |  THROTTLE: {self.throttle*100:3.0f}%  |  "
            f"BRAKE: {self.brake*100:3.0f}%  |  ROLL: {self.roll:+.1f}°  |  "
            f"WHEELIE: {self.wheelie*100:3.0f}%  |  SLIDE: {self.slide*100:3.0f}%"
        )
        c.create_text(20, h - 24, anchor="w", text=bottom_str, fill="#8b949e", font=("Consolas", 9, "bold"))

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

        # 1. Обтекатель и стекло
        poly([(-120, -100), (0, -180), (120, -100), (180, 20), (140, 80), (-140, 80), (-180, 20)],
             fill=self.COLOR_GREEN, outline=self.COLOR_DARK_GREEN, width=2)
        poly([(-70, -110), (0, -210), (70, -110), (90, -40), (-90, -40)],
             fill=self.COLOR_WINDSHIELD, outline="#1f293d", width=2)

        # 2. Фары
        glow = "#ffffff" if self.engine_state == "running" else "#334155"
        poly([(-110, -30), (-40, -40), (-20, -10), (-90, -5)], fill=self.COLOR_HEADLIGHT, outline=glow, width=2)
        poly([(110, -30), (40, -40), (20, -10), (90, -5)], fill=self.COLOR_HEADLIGHT, outline=glow, width=2)

        # 3. Топливный бак
        poly([(-100, 70), (0, 30), (100, 70), (130, 180), (-130, 180)],
             fill=self.COLOR_GREEN, outline="#15803d")
        poly([(-40, 50), (0, 40), (40, 50), (50, 120), (-50, 120)],
             fill=self.COLOR_BLACK, outline="#262626")

        # 4. ИНТЕРАКТИВНАЯ ПРИБОРНАЯ ПАНЕЛЬ (LCD DISPLAY)
        poly([(-80, -45), (0, -60), (80, -45), (90, 25), (-90, 25)], fill="#0f172a", outline="#334155", width=2)
        poly([(-70, -35), (70, -35), (75, 15), (-75, 15)], fill="#020617")

        if self.engine_state in ("running", "starting"):
            # Тахометр (сегментная шкала RPM с зонами и стрелкой-указателем)
            rpm_pct = min(1.0, self.rpm / self.engine_redline)
            poly([(-60, -28), (60, -28), (60, -20), (-60, -20)], fill="#1e293b")
            zone_bounds = [(0.0, 0.72, self.COLOR_GREEN), (0.72, 0.88, self.YELLOW), (0.88, 1.0, self.RED)]
            for z0, z1, col in zone_bounds:
                if rpm_pct > z0:
                    x0 = -60 + 120 * z0
                    x1 = -60 + 120 * min(rpm_pct, z1)
                    poly([(x0, -28), (x1, -28), (x1, -20), (x0, -20)], fill=col)
            needle_x = -60 + 120 * rpm_pct
            line((needle_x, -32), (needle_x, -18), fill="#f8fafc", width=2)

            # Деления шкалы
            for i in range(13):
                dx = -60 + i * 10
                line((dx, -31), (dx, -29), fill="#64748b", width=1)

            # Спидометр
            text((0, -5), f"{int(self.speed)}", fill="#f8fafc", font=("Consolas", int(18 * scale), "bold"))
            text((25, 0), "km/h", fill="#94a3b8", font=("Consolas", int(7 * scale)))

            # Передача
            gear_str = "N" if (self.speed < 1.0 and self.throttle < 0.05) else str(self.gear)
            poly([(-55, -15), (-35, -15), (-35, 8), (-55, 8)], fill="#1e293b", outline="#475569")
            text((-45, -3), gear_str, fill="#38bdf8", font=("Consolas", int(14 * scale), "bold"))

            # Топливо и температура
            text((-50, 12), "FUEL", fill="#64748b", font=("Consolas", int(5 * scale)))
            fuel_bar_w = 20 * (self.fuel / 100.0)
            poly([(-35, 11), (-35 + fuel_bar_w, 11), (-35 + fuel_bar_w, 13), (-35, 13)], fill="#38d430")

            text((20, 12), f"{int(self.engine_temp)}°C", fill="#64748b", font=("Consolas", int(6 * scale)))

            # Shift Light / Индикатор переключения
            if self.rpm > 9500 or self.shift_flash > 0:
                oval((-10, -52), (10, -42), fill="#ffffff", outline="#f85149")

            # Индикаторы wheelie / занос
            if self.wheelie > 0.35:
                text((0, 20), "WHEELIE", fill="#d29922", font=("Consolas", int(6 * scale), "bold"))
            elif self.slide > 0.4:
                text((0, 20), "TRACTION LOSS", fill="#f85149", font=("Consolas", int(6 * scale), "bold"))

        else:
            text((0, -10), "KAWASAKI", fill="#1e293b", font=("Consolas", int(10 * scale), "bold"))

        # 5. Зеркала
        poly([(-140, -110), (-230, -180), (-190, -190), (-120, -125)], fill=self.COLOR_BLACK)
        poly([(140, -110), (230, -180), (190, -190), (120, -125)], fill=self.COLOR_BLACK)
        poly([(-225, -182), (-195, -187), (-140, -135), (-165, -140)], fill="#1e293b")
        poly([(225, -182), (195, -187), (140, -135), (165, -140)], fill="#1e293b")

        # 6. Руль
        handle_y = 60
        line((-110 + steer_px, handle_y - 10), (-210 + steer_px, handle_y + 15), fill="#1e293b", width=int(14 * scale))
        line((-120 + steer_px, handle_y - 5), (-205 + steer_px, handle_y + 18), fill=self.COLOR_BLACK, width=int(18 * scale))

        line((110 + steer_px, handle_y - 10), (210 + steer_px, handle_y + 15), fill="#1e293b", width=int(14 * scale))
        line((120 + steer_px, handle_y - 5), (205 + steer_px, handle_y + 18), fill=self.COLOR_BLACK, width=int(18 * scale))

        # Нажатие тормоза
        brake_press = self.brake_lever_anim * 12.0
        line((130 + steer_px, handle_y), (220 + steer_px - brake_press, handle_y + 10 - brake_press * 0.5),
             fill=self.COLOR_LIGHT_GRAY, width=int(4 * scale))

        # Бачок и траверса
        oval((140 + steer_px, handle_y - 35), (165 + steer_px, handle_y - 15), fill="#f8fafc", outline="#475569")
        poly([(-40 + steer_px, handle_y - 15), (40 + steer_px, handle_y - 15),
              (30 + steer_px, handle_y + 15), (-30 + steer_px, handle_y + 15)],
             fill=self.COLOR_LIGHT_GRAY, outline="#475569")


if __name__ == "__main__":
    root = tk.Tk()
    app = MotorcycleSimulator(root)
    root.mainloop()