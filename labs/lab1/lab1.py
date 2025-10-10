from dataclasses import dataclass
from typing import Optional, Tuple, List
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

    def update(
        self, measurement: float, dt: Optional[float]
    ) -> Tuple[float, float, float, float]:
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
        return u, self.kp * error, self.ki * self.integral, self.kd * derivative


def create_legend(legend_data: List[Tuple[str, str]]) -> VGroup:
    """Create a legend with given data: [(text, color), ...]"""
    legend_items = []
    for text, color in legend_data:
        line = Line([0, 0, 0], [0.5, 0, 0], color=color, stroke_width=2)
        text_obj = TexText(
            text, font_size=20, color=color if color != "WHITE" else WHITE
        ).next_to(line, RIGHT, buff=0.1)
        legend_items.append(VGroup(line, text_obj))
    return (
        VGroup(*legend_items).arrange(DOWN, aligned_edge=LEFT).to_corner(UR, buff=0.5)
    )


def create_plotting_updater(
    pid: PID,
    heading: float,
    acceleration: float,
    max_speed: float,
    line_y: float,
    line_end_x: float,
    axes: Optional[Axes] = None,
    segments: Optional[list] = None,
    scene: Optional[Scene] = None,
    plot_data: Optional[dict] = None,
) -> callable:
    """Create car movement updater with plotting"""
    heading: ValueTracker = ValueTracker(heading)
    time_tracker: ValueTracker = ValueTracker(0)
    speed: ValueTracker = ValueTracker(0)
    data = [
        ("error", RED),
        ("steering", ORANGE),
        ("proportional", YELLOW),
        ("integral", BLUE),
        ("derivative", PURPLE),
    ]

    def follow_path_with_plots(mob: Mobject, dt: float) -> None:
        if not dt or dt <= 0:
            return
        x, y, _ = mob.get_center()

        e: float = y - line_y
        omega, p, i, d = pid.update(e, dt)

        current_time = time_tracker.get_value()
        if plot_data is not None and axes is not None and segments is not None:
            for key, color, value in zip(data, [e, omega, p, i, d]):
                if key in plot_data and len(plot_data[key]) > 1:
                    plot_data[key].append([current_time, value, 0])
                    segment = Line(
                        axes.coords_to_point(*plot_data[key][-2][:2]),
                        axes.coords_to_point(*plot_data[key][-1][:2]),
                        color=color,
                        stroke_width=2,
                    )
                    segments.append(segment)
                    scene.add(segment)

        mob.rotate(omega * dt)
        heading.increment_value(omega * dt)
        time_tracker.increment_value(dt)

        current_speed = speed.get_value()
        if current_speed < max_speed and x < line_end_x:
            speed.increment_value(acceleration * dt)
        elif current_speed > 0 and x >= line_end_x:
            speed.increment_value(-acceleration * dt)
        elif current_speed <= 0 and x >= line_end_x:
            speed.set_value(0)
            mob.remove_updater(follow_path_with_plots)

        current_speed = speed.get_value()
        current_heading = heading.get_value()
        dx: float = current_speed * np.cos(current_heading) * dt
        dy: float = current_speed * np.sin(current_heading) * dt
        mob.move_to([x + dx, y + dy, 0])

    return follow_path_with_plots


class Lab1(Slide):
    def construct(self):
        # Title
        title = TexText("F1tenth Lab 1:", font_size=100).shift(1 * UP)
        title2 = TexText("Wall Following")

        self.play(Write(title))
        self.play(Write(title2))
        self.play(FadeOut(title), FadeOut(title2))

        # Outline
        outline_title = TexText("Outline:", font_size=100).shift(UP * 2)
        outline = (
            VGroup(
                TexText("1. What is PID?"),
                TexText("2. Implementing PID"),
                TexText("3. Tuning PID"),
                TexText("4. Geometric analysis of wall following"),
                TexText("5. Wall following!"),
            )
            .arrange(DOWN, aligned_edge=LEFT)
            .shift(DOWN)
        )
        self.play(Write(outline_title))
        self.play(Write(outline))
        self.play(FadeOut(outline_title), FadeOut(outline))

        # What is PID?
        what_is_pid_title = TexText("What is PID?")
        self.play(Write(what_is_pid_title))

        line_y = 0
        line_start_x = -5
        line_end_x = 5
        heading = PI / 4
        line = Line(
            line_y * UP + line_start_x * RIGHT, line_y * UP + line_end_x * RIGHT
        )
        car = (
            ImageMobject("labs/lab1/car_topview.png")
            .scale(0.07)
            .shift(line_y * UP + line_start_x * RIGHT)
            .rotate(heading)
        )

        self.play(Transform(what_is_pid_title, line), FadeIn(car))

        follow_path = create_plotting_updater(
            pid=PID(kp=2.0, ki=0.1, kd=2.0, setpoint=0.0, out_limits=(-2.0, 2.0)),
            heading=heading,
            acceleration=2,
            max_speed=1.5,
            line_y=line_y,
            line_end_x=line_end_x,
        )
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
        what_is_pid_title = TexText("Another look at pid")
        self.play(Write(what_is_pid_title))

        line_y = -3
        line_start_x = -5
        line_end_x = 5
        heading = PI / 4
        line = Line(
            line_start_x * RIGHT + line_y * UP, line_end_x * RIGHT + line_y * UP
        )
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
        legend_group = create_legend([("Error", RED), ("Steering", BLUE)])
        car = (
            ImageMobject("labs/lab1/car_topview.png")
            .scale(0.07)
            .shift(line_start_x * RIGHT + line_y * UP)
            .rotate(heading)
        )
        segments = []

        self.play(Transform(what_is_pid_title, line))
        self.play(Write(axes))
        self.play(Write(legend_group))
        self.play(FadeIn(car))

        follow_path = create_plotting_updater(
            pid=PID(kp=2.0, ki=0.1, kd=2.0, setpoint=0.0, out_limits=(-2.0, 2.0)),
            heading=heading,
            acceleration=2,
            max_speed=1.5,
            line_y=line_y,
            line_end_x=line_end_x,
            axes=axes,
            segments=segments,
            scene=self,
            plot_data={"error": [], "steering": []},
        )
        car.add_updater(follow_path)
        self.wait_until(lambda: follow_path not in car.updaters)
        self.play(
            FadeOut(car),
            FadeOut(what_is_pid_title),
            FadeOut(axes),
            *[FadeOut(segment) for segment in segments],
            FadeOut(legend_group),
        )

        # Implementing PID
        implement_pid_title = TexText("Implementing PID")
        self.play(Write(implement_pid_title))
        self.play(FadeOut(implement_pid_title))

        pid_equation = Tex(
            r"u(t) = K_p e(t) + K_i \int_0^t e(\tau) d\tau + K_d \frac{de(t)}{dt}"
        ).scale(0.8)
        self.play(Write(pid_equation))

        pid_equation_colored = (
            Tex(
                r"u(t) = ",
                r" K_p ",
                r" e(t) ",
                r" + ",
                r" K_i ",
                r" \int_0^t e(\tau) d\tau ",
                r" + ",
                r" K_d ",
                r" \frac{de(t)}{dt}",
            )
            .scale(0.8)
            .set_color_by_tex_to_color_map(
                {
                    r"e(t)": YELLOW,
                    r"\int_0^t e(\tau) d\tau": BLUE,
                    r"\frac{de(t)}{dt}": PURPLE,
                }
            )
        )
        pid_legend_group = create_legend(
            [("Proportional", YELLOW), ("Integral", BLUE), ("Derivative", PURPLE)]
        )

        self.play(
            Write(pid_legend_group),
            TransformMatchingTex(pid_equation, pid_equation_colored),
        )
        self.play(
            FadeOut(pid_legend_group),
            FadeOut(pid_equation_colored),
        )

        # go back to look at animation with plots for PID error and steering
        what_is_pid_title = TexText("Another another look at pid")
        self.play(Write(what_is_pid_title))

        line_y = -3
        line_start_x = -5
        line_end_x = 5
        heading = PI / 4
        line = Line(
            line_start_x * RIGHT + line_y * UP, line_end_x * RIGHT + line_y * UP
        )
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
        legend_group = create_legend(
            [
                ("Error", RED),
                ("Proportional", YELLOW),
                ("Integral", BLUE),
                ("Derivative", PURPLE),
            ]
        )
        car = (
            ImageMobject("labs/lab1/car_topview.png")
            .scale(0.07)
            .shift(line_start_x * RIGHT + line_y * UP)
            .rotate(heading)
        )
        segments = []

        self.play(Transform(what_is_pid_title, line))
        self.play(Write(axes))
        self.play(Write(legend_group))
        self.play(FadeIn(car))

        follow_path = create_plotting_updater(
            pid=PID(kp=2.0, ki=0.1, kd=2.0, setpoint=0.0, out_limits=(-2.0, 2.0)),
            heading=heading,
            acceleration=2,
            max_speed=1.5,
            line_y=line_y,
            line_end_x=line_end_x,
            axes=axes,
            segments=segments,
            scene=self,
            plot_data={
                "error": [[0, 0, 0]],
                "steering": [[0, 0, 0]],
                "proportional": [[0, 0, 0]],
                "integral": [[0, 0, 0]],
                "derivative": [[0, 0, 0]],
            },
        )
        car.add_updater(follow_path)
        self.wait_until(lambda: follow_path not in car.updaters)
        self.play(
            FadeOut(car),
            FadeOut(what_is_pid_title),
            FadeOut(axes),
            *[FadeOut(segment) for segment in segments],
            FadeOut(legend_group),
        )
