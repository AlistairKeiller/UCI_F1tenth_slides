from dataclasses import dataclass
from typing import Optional, Tuple
from manimlib import *

from manim_slides import Slide


@dataclass
class PID:
    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0
    setpoint: float = 0.0
    out_limits: Tuple[Optional[float], Optional[float]] = (-1.0, 1.0)
    integral: float = 0.0
    previous_error: Optional[float] = None

    def reset(self) -> None:
        self.integral = 0.0
        self.previous_error = None

    def update(self, measurement: float, dt: Optional[float]) -> float:
        error: float = self.setpoint - measurement
        if dt and dt > 0.0:
            self.integral += error * dt
        derivative: float = (
            (error - self.previous_error) / dt
            if dt and dt > 0.0 and self.previous_error is not None
            else 0.0
        )
        u: float = self.kp * error + self.ki * self.integral + self.kd * derivative
        low, high = self.out_limits
        if low is not None and u < low:
            u = low
        if high is not None and u > high:
            u = high
        self.previous_error = error
        return u


class Lab1(Slide):
    def construct(self):
        # title slide
        title = Text("F1tenth Lab 1:", font_size=100).shift(1 * UP)
        title2 = Text("Wall Following")

        self.play(Write(title))
        self.play(Write(title2))
        self.play(FadeOut(title), FadeOut(title2))

        # Outline
        outline_title = Text("Outline:", font_size=100).shift(UP * 2)
        outline = Text(
            "1. What is PID?\n2. Implementing PID\n3. Tuning PID\n4.Geometric analysis of wall following\n5. Wall following!",
            line_spacing_height=1.5,
        ).shift(DOWN)
        self.play(Write(outline_title))
        self.play(Write(outline))
        self.play(FadeOut(outline_title), FadeOut(outline))

        # What is PID?
        what_is_pid_title = Text("What is PID?")
        self.play(Write(what_is_pid_title))

        line_start = [-5, 0, 0]
        line_length = 10
        pid = PID(kp=2.0, ki=0.1, kd=2.0, setpoint=0.0, out_limits=(-2.0, 2.0))
        speed = ValueTracker(0)
        max_speed = 1.5
        acceleration = 2
        heading = ValueTracker(PI / 4)

        line = Line(line_start, line_start + RIGHT * line_length)

        self.play(Transform(what_is_pid_title, line))

        car = (
            ImageMobject("labs/lab1/car_topview.png")
            .scale(0.07)
            .shift(line_start)
            .rotate(heading.get_value())
        )

        self.play(FadeIn(car))

        def follow_path(mob, dt):
            if not dt or dt <= 0:
                return
            x, y, _ = mob.get_center()

            e = y - line_start[1]
            omega = pid.update(e, dt)

            new_theta = heading.get_value() + omega * dt
            mob.rotate(new_theta - heading.get_value())
            heading.set_value(new_theta)

            if x < line_start[0] + line_length:
                speed.set_value(min(speed.get_value() + acceleration * dt, max_speed))
            else:
                speed.set_value(max(speed.get_value() - acceleration * dt, 0))
                if speed.get_value() <= 0:
                    mob.remove_updater(follow_path)
            dx = speed.get_value() * np.cos(new_theta) * dt
            dy = speed.get_value() * np.sin(new_theta) * dt
            mob.move_to([x + dx, y + dy, 0])

        car.add_updater(follow_path)
        self.wait_until(lambda: follow_path not in car.updaters)
        self.play(FadeOut(car), FadeOut(what_is_pid_title))

        # Pid equation
        error_text = Tex(r"\text{Error}").set_color(RED).shift(LEFT * 4)
        pid_box = Rectangle(width=2, height=1).shift(ORIGIN)
        pid_text = Tex(r"\text{PID}").move_to(pid_box.get_center())
        output_text = Tex(r"\text{Action}").set_color(GREEN).shift(RIGHT * 4)

        arrow1 = Arrow(error_text.get_right(), pid_box.get_left(), buff=0.1)
        arrow2 = Arrow(pid_box.get_right(), output_text.get_left(), buff=0.1)

        self.play(Write(error_text))
        self.play(GrowArrow(arrow1))
        self.play(Write(pid_box), Write(pid_text))
        self.play(GrowArrow(arrow2))
        self.play(Write(output_text))

        self.play(
            FadeOut(arrow1),
            FadeOut(pid_box),
            FadeOut(pid_text),
            FadeOut(arrow2),
            FadeOut(output_text),
        )
        error_eq = Tex(
            r"\text{Error}",
            " = ",
            r"\text{Desired State}",
            " - ",
            r"\text{Measured State}",
        ).set_color_by_tex_to_color_map(
            {
                "Error": RED,
                "Desired State": BLUE,
                "Measured State": PURPLE,
            }
        )

        self.play(TransformMatchingTex(error_text, error_eq))
        self.play(FadeOut(error_eq))

        # go back to look at animation with plots for error and steering
        what_is_pid_title = Text("Another look at pid")
        self.play(Write(what_is_pid_title))

        line_start = [-5, -3, 0]
        line_length = 10
        pid = PID(kp=2.0, ki=0.1, kd=2.0, setpoint=0.0, out_limits=(-2.0, 2.0))
        speed = ValueTracker(0)
        max_speed = 1.5
        acceleration = 2
        heading = ValueTracker(PI / 4)
        line = Line(line_start, line_start + RIGHT * line_length)

        self.play(Transform(what_is_pid_title, line))

        axes = Axes(
            x_range=(0, 8),
            y_range=(-2, 2, 0.5),
            height=6,
            width=10,
        ).shift(UP * 0.5)

        axes.add_coordinate_labels(
            font_size=20,
            num_decimal_places=1,
        )

        error_legend = Line([0, 0, 0], [0.5, 0, 0], color=RED, stroke_width=2)
        error_label = Text("Error", font_size=20, color=RED).next_to(
            error_legend, RIGHT, buff=0.1
        )

        steering_legend = Line([0, 0, 0], [0.5, 0, 0], color=BLUE, stroke_width=2)
        steering_label = Text("Steering", font_size=20, color=BLUE).next_to(
            steering_legend, RIGHT, buff=0.1
        )

        legend_group = (
            VGroup(
                VGroup(error_legend, error_label),
                VGroup(steering_legend, steering_label),
            )
            .arrange(DOWN, aligned_edge=LEFT)
            .to_corner(UR, buff=0.5)
        )

        self.play(Write(axes))
        self.play(Write(legend_group))

        error_tracker = ValueTracker(0)
        time_tracker = ValueTracker(0)
        error_points = []
        steering_points = []
        error_segments = []
        steering_segments = []

        car = (
            ImageMobject("labs/lab1/car_topview.png")
            .scale(0.07)
            .shift(line_start)
            .rotate(heading.get_value())
        )

        self.play(FadeIn(car))

        def follow_path(mob, dt):
            if not dt or dt <= 0:
                return
            x, y, _ = mob.get_center()

            e = y - line_start[1]
            omega = pid.update(e, dt)

            error_tracker.set_value(e)
            time_tracker.set_value(time_tracker.get_value() + dt)
            error_points.append([time_tracker.get_value(), e, 0])
            steering_points.append([time_tracker.get_value(), omega, 0])

            if len(error_points) > 1:
                error_segment = Line(
                    axes.coords_to_point(*error_points[-2][:2]),
                    axes.coords_to_point(*error_points[-1][:2]),
                    color=RED,
                    stroke_width=2,
                )
                steering_segment = Line(
                    axes.coords_to_point(*steering_points[-2][:2]),
                    axes.coords_to_point(*steering_points[-1][:2]),
                    color=BLUE,
                    stroke_width=2,
                )
                error_segments.append(error_segment)
                steering_segments.append(steering_segment)
                self.add(error_segment, steering_segment)

            new_theta = heading.get_value() + omega * dt
            mob.rotate(new_theta - heading.get_value())
            heading.set_value(new_theta)

            if x < line_start[0] + line_length:
                speed.set_value(min(speed.get_value() + acceleration * dt, max_speed))
            else:
                speed.set_value(max(speed.get_value() - acceleration * dt, 0))
            if speed.get_value() <= 0:
                mob.remove_updater(follow_path)
            dx = speed.get_value() * np.cos(new_theta) * dt
            dy = speed.get_value() * np.sin(new_theta) * dt
            mob.move_to([x + dx, y + dy, 0])

        car.add_updater(follow_path)
        self.wait_until(lambda: follow_path not in car.updaters)
        self.play(
            FadeOut(car),
            FadeOut(what_is_pid_title),
            FadeOut(axes),
            *[FadeOut(segment) for segment in error_segments],
            *[FadeOut(segment) for segment in steering_segments],
            FadeOut(error_legend),
            FadeOut(error_label),
            FadeOut(steering_legend),
            FadeOut(steering_label),
        )
