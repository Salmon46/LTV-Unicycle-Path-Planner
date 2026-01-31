from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.slider import Slider
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.graphics.texture import Texture
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, ListProperty
import math
import numpy as np
from PIL import Image as PILImage
import json
import os

# --- MODERN UI CONFIGURATION ---
Window.size = (1600, 900)

# Color Palette inspired by the user's image
C_BACKGROUND = [24/255, 24/255, 38/255, 1]
C_PANEL = [36/255, 36/255, 58/255, 1]
C_PRIMARY = [128/255, 82/255, 255/255, 1]
C_SECONDARY = [0.2, 0.5, 1, 1]
C_ACCENT_RED = [230/255, 50/255, 75/255, 1]
C_ACCENT_GREEN = [40/255, 180/255, 120/255, 1]
C_TEXT = [230/255, 230/255, 240/255, 1]
C_HINT_TEXT = [0.6, 0.6, 0.65, 1]
C_INPUT_BG = [30/255, 30/255, 45/255, 1]

Window.clearcolor = C_BACKGROUND

# --- CUSTOM WIDGETS FOR MODERN UI ---

class RoundedBoxLayout(BoxLayout):
    bg_color = ListProperty(C_PANEL)
    radius = ListProperty([15, 15, 15, 15])
    
    def __init__(self, **kwargs):
        super(RoundedBoxLayout, self).__init__(**kwargs)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=self.radius)

class ModernButton(Button):
    def __init__(self, **kwargs):
        super(ModernButton, self).__init__(**kwargs)
        self.background_normal = ''
        self.background_color = C_PRIMARY
        self.font_size = '14sp'
        self.bold = True
        self.color = [1, 1, 1, 1]
        
        with self.canvas.before:
            self.bg_color = Color(*C_PRIMARY)
            self.rect = RoundedRectangle(radius=[8])
        self.bind(pos=self.update_shape, size=self.update_shape)
        self.on_state(self, self.state)

    def update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def on_state(self, instance, value):
        if not hasattr(self, 'bg_color'):
            return
        if value == 'down':
            self.bg_color.rgba = [c * 0.8 for c in C_PRIMARY]
        else:
            self.bg_color.rgba = C_PRIMARY

class ModernToggleButton(ToggleButton):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = [0, 0, 0, 0]
        self.font_size = '13sp'
        self.bold = True
        
        with self.canvas.before:
            self.bg_color = Color()
            self.rect = RoundedRectangle(radius=[8])
        self.bind(pos=self.update_shape, size=self.update_shape)
        self.on_state(self, self.state) # Initial color set

    def update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_state(self, instance, value):
        if not hasattr(self, 'bg_color'):
            return
        if value == 'down':
            self.bg_color.rgba = C_PRIMARY
            self.color = [1,1,1,1]
        else:
            self.bg_color.rgba = C_INPUT_BG
            self.color = C_TEXT

class ModernSpinnerOption(SpinnerOption):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = C_INPUT_BG
        self.color = C_TEXT
        self.font_size = '13sp'
        with self.canvas.before:
            self.bg_color_instruction = Color(*C_INPUT_BG)
            self.rect = Rectangle()
        self.bind(pos=self.update_shape, size=self.update_shape)
    
    def on_state(self, instance, value):
        if value == 'down':
            self.bg_color_instruction.rgba = C_PRIMARY
        else:
            self.bg_color_instruction.rgba = C_INPUT_BG

    def update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ModernSpinner(Spinner):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = C_INPUT_BG
        self.color = C_TEXT
        self.option_cls = ModernSpinnerOption # Use custom option class
        with self.canvas.before:
            Color(*self.background_color)
            self.rect = RoundedRectangle(radius=[8])
        self.bind(pos=self.update_shape, size=self.update_shape)

    def update_shape(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

class ModernTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_active = ''
        self.background_color = C_INPUT_BG  # NOT transparent!
        self.foreground_color = C_TEXT
        self.cursor_color = C_PRIMARY
        self.hint_text_color = C_HINT_TEXT
        self.padding = [10, 10, 10, 10]
        
        # Remove the canvas.before block entirely - let background_color handle it
        
        self.bind(focus=self.on_focus)
    
    def on_focus(self, instance, value):
        if value:
            self.background_color = [c * 1.2 for c in C_INPUT_BG[:3]] + [1]
        else:
            self.background_color = C_INPUT_BG

# NEW: Popup for precise coordinate input
class PreciseInputPopup(Popup):
    def __init__(self, path_canvas, point_index, **kwargs):
        super().__init__(**kwargs)
        self.path_canvas = path_canvas
        self.point_index = point_index
        
        # Configure popup
        self.title = f'Edit Coordinates for Point {point_index}'
        self.title_color = C_TEXT
        self.background_color = C_BACKGROUND
        self.separator_color = C_PRIMARY
        self.size_hint = (0.4, 0.4)
        
        # Main content layout
        content_layout = RoundedBoxLayout(orientation='vertical', padding=20, spacing=15)
        
        # Error label
        self.error_label = Label(text='', color=C_ACCENT_RED, size_hint_y=None, height=20)
        
        # Grid for inputs
        grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=100)
        
        # X Input
        grid.add_widget(Label(text="X Coordinate:", color=C_TEXT, bold=True))
        self.x_input = ModernTextInput(multiline=False)
        grid.add_widget(self.x_input)
        
        # Y Input
        grid.add_widget(Label(text="Y Coordinate:", color=C_TEXT, bold=True))
        self.y_input = ModernTextInput(multiline=False)
        grid.add_widget(self.y_input)
        
        # Button layout
        button_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        update_btn = ModernButton(text='Update')
        update_btn.bind(on_press=self.on_update)
        cancel_btn = ModernButton(text='Cancel')
        # Use a more subdued color for cancel
        cancel_btn.bg_color.rgba = [c * 0.8 for c in C_PANEL]
        cancel_btn.bind(on_press=self.dismiss)
        
        button_layout.add_widget(update_btn)
        button_layout.add_widget(cancel_btn)
        
        # Assemble content
        content_layout.add_widget(grid)
        content_layout.add_widget(self.error_label)
        content_layout.add_widget(Widget(size_hint_y=0.1)) # Spacer
        content_layout.add_widget(button_layout)
        
        self.content = content_layout
        
        # Load initial data
        self.load_data()

    def load_data(self):
        try:
            x, y = self.path_canvas.control_points[self.point_index]
            self.x_input.text = f'{x:.3f}'
            self.y_input.text = f'{y:.3f}'
        except Exception as e:
            self.error_label.text = f'Error loading point data: {e}'

    def on_update(self, instance):
        try:
            new_x = float(self.x_input.text)
            new_y = float(self.y_input.text)
            
            # Clamp values to field boundaries
            new_x = np.clip(new_x, self.path_canvas.field_min, self.path_canvas.field_max)
            new_y = np.clip(new_y, self.path_canvas.field_min, self.path_canvas.field_max)
            
            # Update the path canvas
            self.path_canvas.control_points[self.point_index] = [new_x, new_y]
            self.path_canvas.redraw()
            
            # Dismiss popup
            self.dismiss()
            
        except ValueError:
            self.error_label.text = 'Invalid input. Please enter numbers only.'
        except Exception as e:
            self.error_label.text = f'An error occurred: {e}'


class LTVUnicycleController:
    """Linear Time-Varying Unicycle Controller"""
    def __init__(self, kx, ky, ktheta):
        self.kx = kx
        self.ky = ky
        self.ktheta = ktheta
    
    def calculateControl(self, currentPose, referencePose, referenceLinearVelocity, referenceAngularVelocity):
        currentTheta = (currentPose[2] + math.pi) % (2 * math.pi) - math.pi
        referenceTheta = (referencePose[2] + math.pi) % (2 * math.pi) - math.pi
        
        ex = referencePose[0] - currentPose[0]
        ey = referencePose[1] - currentPose[1]
        
        # --- HEADING CHANGE ---
        # The 2D rotation matrix for the error vector (ex, ey) from world-frame to robot-frame
        # has been changed.
        # Standard (0_deg=Right): ex_robot = ex*cos(th) + ey*sin(th)
        # Standard (0_deg=Right): ey_robot = -ex*sin(th) + ey*cos(th)
        # New (0_deg=Up): cos(th_std) = sin(th_nav), sin(th_std) = -cos(th_nav)
        # This transforms the equations to use sin and cos in opposite places,
        # and also flips the sign on the sin(th_std) component.
        #
        # Corrected (0-deg-Up) rotation:
        # ex_robot (forward error) = ex*sin(th) + ey*cos(th)
        # ey_robot (lateral error) = ex*cos(th) - ey*sin(th)
        ex_robot = ex * math.sin(currentTheta) + ey * math.cos(currentTheta)
        ey_robot = ex * math.cos(currentTheta) - ey * math.sin(currentTheta)
        # --- END HEADING CHANGE ---
        
        etheta = (referenceTheta - currentTheta + math.pi) % (2 * math.pi) - math.pi
        
        v = referenceLinearVelocity * math.cos(etheta) + self.kx * ex_robot
        
        if abs(referenceLinearVelocity) > 0.1:
            w = referenceAngularVelocity + referenceLinearVelocity * (self.ky * ey_robot + self.ktheta * math.sin(etheta))
        else:
            w = referenceAngularVelocity + self.ktheta * etheta
        
        return v, w


def cubic_bezier(t, p0, p1, p2, p3):
    """Calculate point on cubic Bezier curve"""
    return (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3


def cubic_bezier_derivative(t, p0, p1, p2, p3):
    """Calculate derivative (tangent) of cubic Bezier curve"""
    return 3*(1-t)**2 * (p1 - p0) + 6*(1-t)*t * (p2 - p1) + 3*t**2 * (p3 - p2)


def trapezoidal_profile(total_time, v_max, accel, decel):
    """Generate time-based trapezoidal velocity profile"""
    t_accel = v_max / accel if accel > 0 else float('inf')
    t_decel = v_max / decel if decel > 0 else float('inf')
    
    if t_accel + t_decel > total_time:
        # Triangle profile
        v_peak = total_time * accel * decel / (accel + decel) if (accel + decel) > 0 else 0
        t_accel = v_peak / accel if accel > 0 else 0
        t_decel = v_peak / decel if decel > 0 else 0
        t_cruise = 0
    else:
        t_cruise = total_time - t_accel - t_decel
        v_peak = v_max
    
    return {
        'v_peak': v_peak,
        't_accel': t_accel,
        't_cruise': t_cruise,
        't_decel': t_decel,
        'total_time': total_time
    }


def scurve_profile(total_time, v_max, accel, decel, jerk):
    """Generate time-based S-curve velocity profile"""
    t_j_accel = min(accel / jerk, total_time / 6) if jerk > 0 else 0
    t_j_decel = min(decel / jerk, total_time / 6) if jerk > 0 else 0
    
    t_accel = (v_max / accel) + t_j_accel if accel > 0 else 0
    t_decel = (v_max / decel) + t_j_decel if decel > 0 else 0
    
    if t_accel + t_decel > total_time:
        v_peak = total_time * accel * decel / (accel + decel) if (accel + decel) > 0 else 0
        t_accel = v_peak / accel if accel > 0 else 0
        t_decel = v_peak / decel if decel > 0 else 0
        t_cruise = 0
    else:
        t_cruise = total_time - t_accel - t_decel
        v_peak = v_max
    
    return {
        'v_peak': v_peak,
        't_j_accel': t_j_accel,
        't_j_decel': t_j_decel,
        't_accel': t_accel,
        't_cruise': t_cruise,
        't_decel': t_decel,
        'total_time': total_time,
        'jerk': jerk
    }


class MotionProfileGraph(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.speed_keyframes = []
        self.max_speed = 60.0
        self.min_speed = 0.0
        self.dragging_keyframe = None
        self.actual_speed_data = []
        self.actual_accel_data = []
        self.actual_jerk_data = []
        
        self.profile_type = 'trapezoidal'
        self.max_acceleration = 100.0
        self.max_deceleration = 100.0
        self.max_jerk = 500.0
        
        self.generated_profile = []
        self.total_time = 10.0
        
        self.show_velocity = True
        self.show_acceleration = False
        self.show_jerk = False
        
        self.bind(pos=self.redraw, size=self.redraw)
        
    def generate_motion_profile(self, path_length):
        """Generate motion profile based on current settings"""
        self.generated_profile = []
        
        if path_length <= 0:
            return
        
        # Store the path length this profile was generated for
        self.path_length_for_profile = path_length
        
        # Better time estimation - use average speed of 50% max speed
        avg_speed = self.max_speed * 0.5 if self.max_speed > 0 else 1
        self.total_time = max(3.0, path_length / avg_speed)
        
        if self.profile_type == 'trapezoidal':
            profile = trapezoidal_profile(self.total_time, self.max_speed, 
                                         self.max_acceleration, self.max_deceleration)
            
            num_points = 200
            for i in range(num_points):
                t = (profile['total_time'] / (num_points - 1)) * i if num_points > 1 else 0
                time_ratio = t / profile['total_time'] if profile['total_time'] > 0 else 0
                
                if t < profile['t_accel']:
                    v = self.max_acceleration * t
                    a = self.max_acceleration
                    j = 0
                elif t < profile['t_accel'] + profile['t_cruise']:
                    v = profile['v_peak']
                    a = 0
                    j = 0
                else:
                    t_decel = t - profile['t_accel'] - profile['t_cruise']
                    v = profile['v_peak'] - self.max_deceleration * t_decel
                    a = -self.max_deceleration
                    j = 0
                
                self.generated_profile.append({
                    'time': t,
                    'time_ratio': time_ratio,
                    'velocity': max(0, v),
                    'acceleration': a,
                    'jerk': j
                })
        
        elif self.profile_type == 's-curve':
            profile = scurve_profile(self.total_time, self.max_speed, 
                                    self.max_acceleration, self.max_deceleration, self.max_jerk)
            
            num_points = 200
            t_j_a = profile['t_j_accel']
            t_a = profile['t_accel']
            t_c = profile['t_cruise']
            t_j_d = profile['t_j_decel']
            t_d = profile['t_decel']
            
            for i in range(num_points):
                t = (profile['total_time'] / (num_points - 1)) * i if num_points > 1 else 0
                time_ratio = t / profile['total_time'] if profile['total_time'] > 0 else 0
                
                # Simplified S-curve implementation
                if t < t_j_a:
                    j = self.max_jerk
                    a = self.max_jerk * t
                    v = 0.5 * self.max_jerk * t**2
                elif t < t_a - t_j_a:
                    j = 0
                    a = self.max_acceleration
                    t_const = t - t_j_a
                    v = 0.5 * self.max_jerk * t_j_a**2 + self.max_acceleration * t_const
                elif t < t_a:
                    t_ramp = t - (t_a - t_j_a)
                    j = -self.max_jerk
                    a = self.max_acceleration - self.max_jerk * t_ramp
                    v = profile['v_peak'] - 0.5 * self.max_jerk * (t_a - t)**2
                elif t < t_a + t_c:
                    j = 0
                    a = 0
                    v = profile['v_peak']
                elif t < t_a + t_c + t_j_d:
                    t_dec = t - t_a - t_c
                    j = -self.max_jerk
                    a = -self.max_jerk * t_dec
                    v = profile['v_peak'] - 0.5 * self.max_jerk * t_dec**2
                elif t < t_a + t_c + t_d - t_j_d:
                    t_dec = t - t_a - t_c
                    t_const = t_dec - t_j_d
                    j = 0
                    a = -self.max_deceleration
                    v = profile['v_peak'] - 0.5 * self.max_jerk * t_j_d**2 - self.max_deceleration * t_const
                else:
                    t_dec = t - t_a - t_c
                    t_ramp = t_dec - (t_d - t_j_d)
                    j = self.max_jerk
                    a = -self.max_deceleration + self.max_jerk * t_ramp
                    v = max(0, self.max_jerk * (t_a + t_c + t_d - t)**2 / 2)
                
                self.generated_profile.append({
                    'time': t,
                    'time_ratio': time_ratio,
                    'velocity': max(0, min(self.max_speed, v)),
                    'acceleration': a,
                    'jerk': j
                })
        
        elif self.profile_type == 'custom' and len(self.speed_keyframes) >= 2:
            sorted_kf = sorted(self.speed_keyframes, key=lambda k: k[0])
            num_points = 200
            
            for i in range(num_points):
                time_ratio = i / (num_points - 1)
                
                # Interpolate between keyframes
                for j in range(len(sorted_kf) - 1):
                    if sorted_kf[j][0] <= time_ratio <= sorted_kf[j+1][0]:
                        t = (time_ratio - sorted_kf[j][0]) / (sorted_kf[j+1][0] - sorted_kf[j][0]) if (sorted_kf[j+1][0] - sorted_kf[j][0]) > 0 else 0
                        v = sorted_kf[j][1] + (sorted_kf[j+1][1] - sorted_kf[j][1]) * t
                        break
                else:
                    v = self.max_speed
                
                # Calculate acceleration numerically
                if i > 0:
                    dt = self.total_time / (num_points - 1)
                    a = (v - self.generated_profile[-1]['velocity']) / dt if dt > 0 else 0
                else:
                    a = 0
                
                # Calculate jerk numerically
                if i > 1:
                    dt = self.total_time / (num_points - 1)
                    j = (a - self.generated_profile[-1]['acceleration']) / dt if dt > 0 else 0
                else:
                    j = 0
                
                self.generated_profile.append({
                    'time': time_ratio * self.total_time,
                    'time_ratio': time_ratio,
                    'velocity': v,
                    'acceleration': a,
                    'jerk': j
                })
        else:
            # Constant velocity fallback
            for i in range(200):
                time_ratio = i / 199
                self.generated_profile.append({
                    'time': time_ratio * self.total_time,
                    'time_ratio': time_ratio,
                    'velocity': self.max_speed,
                    'acceleration': 0,
                    'jerk': 0
                })
    
    def redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            Color(*C_PANEL)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
            
            Color(1,1,1, 0.05)
            for i in range(1, 10):
                y = self.y + (self.height / 10) * i
                Line(points=[self.x, y, self.x + self.width, y], width=1)
            
            for i in range(1, 10):
                x = self.x + (self.width / 10) * i
                Line(points=[x, self.y, x, self.y + self.height], width=1)
            
            # Draw velocity profile
            if self.show_velocity and len(self.generated_profile) >= 2:
                Color(*C_SECONDARY)
                points = []
                for point in self.generated_profile:
                    px = self.x + point['time_ratio'] * self.width
                    py = self.y + (point['velocity'] / self.max_speed if self.max_speed > 0 else 0) * self.height
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=2)
            
            # Draw acceleration profile (normalized to graph height)
            if self.show_acceleration and len(self.generated_profile) >= 2:
                Color(1, 0.6, 0.2, 1)
                points = []
                max_accel = max(self.max_acceleration, self.max_deceleration, 1)
                
                for point in self.generated_profile:
                    # Normalize acceleration: -max_accel to +max_accel maps to 0 to height
                    accel_normalized = (point['acceleration'] / (2 * max_accel)) + 0.5
                    accel_normalized = max(0, min(1, accel_normalized))
                    
                    px = self.x + point['time_ratio'] * self.width
                    py = self.y + accel_normalized * self.height
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=1.5)
            
            # Draw jerk profile (normalized to graph height)
            if self.show_jerk and len(self.generated_profile) >= 2:
                Color(0.9, 0.3, 0.9, 1)
                points = []
                max_jerk_val = self.max_jerk if self.max_jerk > 0 else 1
                
                for point in self.generated_profile:
                    # Normalize jerk: -max_jerk to +max_jerk maps to 0 to height
                    jerk_normalized = (point['jerk'] / (2 * max_jerk_val)) + 0.5
                    jerk_normalized = max(0, min(1, jerk_normalized))
                    
                    px = self.x + point['time_ratio'] * self.width
                    py = self.y + jerk_normalized * self.height
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=1.5)
            
            # Draw actual speed data
            if len(self.actual_speed_data) >= 2:
                Color(*C_ACCENT_RED)
                points = []
                
                for time, speed in self.actual_speed_data:
                    time_ratio = time / self.total_time if self.total_time > 0 else 0
                    px = self.x + time_ratio * self.width
                    py = self.y + (speed / self.max_speed if self.max_speed > 0 else 0) * self.height
                    py = max(self.y, min(self.y + self.height, py))
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=2)
            
            # Draw actual acceleration data
            if self.show_acceleration and len(self.actual_accel_data) >= 2:
                Color(1, 0.4, 0.1, 0.8)
                points = []
                max_accel = max(self.max_acceleration, self.max_deceleration, 1)
                
                for time, accel in self.actual_accel_data:
                    time_ratio = time / self.total_time if self.total_time > 0 else 0
                    accel_normalized = (accel / (2 * max_accel)) + 0.5
                    accel_normalized = max(0, min(1, accel_normalized))
                    
                    px = self.x + time_ratio * self.width
                    py = self.y + accel_normalized * self.height
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=1.5, dash_length=3, dash_offset=2)
            
            # Draw actual jerk data
            if self.show_jerk and len(self.actual_jerk_data) >= 2:
                Color(1, 0.2, 0.8, 0.8)
                points = []
                max_jerk_val = self.max_jerk if self.max_jerk > 0 else 1
                
                for time, jerk in self.actual_jerk_data:
                    time_ratio = time / self.total_time if self.total_time > 0 else 0
                    jerk_normalized = (jerk / (2 * max_jerk_val)) + 0.5
                    jerk_normalized = max(0, min(1, jerk_normalized))
                    
                    px = self.x + time_ratio * self.width
                    py = self.y + jerk_normalized * self.height
                    points.extend([px, py])
                
                if len(points) >= 4:
                    Line(points=points, width=1.5, dash_length=3, dash_offset=2)
            
            # Draw custom keyframes
            if self.profile_type == 'custom':
                for time_ratio, speed in self.speed_keyframes:
                    Color(1, 0.7, 0.2, 1)
                    px = self.x + time_ratio * self.width
                    py = self.y + (speed / self.max_speed if self.max_speed > 0 else 0) * self.height
                    Ellipse(pos=(px - 6, py - 6), size=(12, 12))
            
            # Draw zero line for acceleration/jerk
            if self.show_acceleration or self.show_jerk:
                Color(1,1,1, 0.1)
                center_y = self.y + self.height / 2
                Line(points=[self.x, center_y, self.x + self.width, center_y], width=1)
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.profile_type != 'custom':
            return False
        
        for i, (time_ratio, speed) in enumerate(self.speed_keyframes):
            px = self.x + time_ratio * self.width
            py = self.y + (speed / self.max_speed if self.max_speed > 0 else 0) * self.height
            
            if abs(touch.x - px) < 10 and abs(touch.y - py) < 10:
                self.dragging_keyframe = i
                return True
        
        time_ratio = (touch.x - self.x) / self.width
        speed_ratio = (touch.y - self.y) / self.height
        speed = speed_ratio * self.max_speed
        
        self.speed_keyframes.append((max(0, min(1, time_ratio)), max(0, min(self.max_speed, speed))))
        self.generate_motion_profile(100)
        self.redraw()
        return True
    
    def on_touch_move(self, touch):
        if self.dragging_keyframe is not None and self.collide_point(*touch.pos):
            time_ratio = (touch.x - self.x) / self.width
            speed_ratio = (touch.y - self.y) / self.height
            speed = speed_ratio * self.max_speed
            
            self.speed_keyframes[self.dragging_keyframe] = (
                max(0, min(1, time_ratio)), 
                max(0, min(self.max_speed, speed))
            )
            self.generate_motion_profile(100)
            self.redraw()
            return True
    
    def on_touch_up(self, touch):
        if self.dragging_keyframe is not None:
            if touch.button == 'right' or touch.is_double_tap:
                del self.speed_keyframes[self.dragging_keyframe]
                self.generate_motion_profile(100)
                self.redraw()
            self.dragging_keyframe = None
            return True
    
    def get_velocity_at_distance(self, distance):
        """Get velocity at a given distance along the path"""
        if not self.generated_profile or self.total_time <= 0:
            return 0
        
        # Calculate what percentage of the path we've traveled
        # This is key: we map distance to the motion profile
        if not hasattr(self, 'path_length_for_profile') or self.path_length_for_profile <= 0:
            return self.max_speed
        
        distance_ratio = distance / self.path_length_for_profile
        distance_ratio = max(0, min(1, distance_ratio))
        
        # Find the corresponding time in the profile based on distance ratio
        target_time = distance_ratio * self.total_time
        
        return self.get_velocity_at_time(target_time)
    
    def get_velocity_at_time(self, time):
        """Get velocity at a given time"""
        if not self.generated_profile or time < 0:
            return 0
        
        if time >= self.generated_profile[-1]['time']:
            return 0
        
        # Find closest time points
        for i in range(len(self.generated_profile) - 1):
            if self.generated_profile[i]['time'] <= time <= self.generated_profile[i + 1]['time']:
                # Linear interpolation
                t = (time - self.generated_profile[i]['time']) / (self.generated_profile[i + 1]['time'] - self.generated_profile[i]['time']) if (self.generated_profile[i + 1]['time'] - self.generated_profile[i]['time']) > 0 else 0
                v1 = self.generated_profile[i]['velocity']
                v2 = self.generated_profile[i + 1]['velocity']
                return v1 + (v2 - v1) * t
        
        return 0
    
    def clear(self):
        self.speed_keyframes = []
        self.actual_speed_data = []
        self.actual_accel_data = []
        self.actual_jerk_data = []
        self.generated_profile = []
        self.redraw()
    
    def clear_actual_data(self):
        self.actual_speed_data = []
        self.actual_accel_data = []
        self.actual_jerk_data = []
        self.redraw()
    
    def add_actual_data_point(self, time, speed, accel, jerk):
        """Add actual data points with absolute time values"""
        self.actual_speed_data.append((time, speed))
        self.actual_accel_data.append((time, accel))
        self.actual_jerk_data.append((time, jerk))
        self.redraw()


class PathCanvas(Widget):
    background_texture = ObjectProperty(None)
    
    def __init__(self, motion_graph, **kwargs):
        super().__init__(**kwargs)
        self.motion_graph = motion_graph
        
        self.field_min = -72
        self.field_max = 72
        self.field_size = self.field_max - self.field_min
        
        self.control_points = []
        self.action_points = {} # NEW: Dictionary to store actions
        self.selected_point = None
        self.dragging = False
        
        self.trajectory = []
        self.robotPose = np.array([0.0, 0.0, 0.0])
        self.robotVelocity = 0.0
        self.robotAcceleration = 0.0
        self.robotJerk = 0.0
        self.deltaTime = 0.01
        self.maxVelocity = 60.0
        self.maxAcceleration = 100.0
        self.maxAngularVelocity = 3.0
        self.tracePoints = []
        self.isSimulating = False
        self.robotRadius = 8
        self.controller = None
        self.simulation_event = None
        self.simulation_time = 0.0
        self.prev_velocity = 0.0
        self.prev_acceleration = 0.0
        self.path_length = 0.0
        self.distance_traveled = 0.0
        self.suppress_profile_generation = False
        
        self.bind(pos=self.redraw, size=self.redraw)
        
    def pixel_to_field(self, px, py):
        size = min(self.width, self.height)
        offset_x = (self.width - size) / 2
        offset_y = (self.height - size) / 2
        
        norm_x = (px - self.x - offset_x) / size if size > 0 else 0
        norm_y = (py - self.y - offset_y) / size if size > 0 else 0
        
        field_x = self.field_min + norm_x * self.field_size
        field_y = self.field_min + norm_y * self.field_size
        
        return field_x, field_y
    
    def field_to_pixel(self, fx, fy):
        size = min(self.width, self.height)
        offset_x = (self.width - size) / 2
        offset_y = (self.height - size) / 2
        
        norm_x = (fx - self.field_min) / self.field_size if self.field_size > 0 else 0
        norm_y = (fy - self.field_min) / self.field_size if self.field_size > 0 else 0
        
        px = self.x + offset_x + norm_x * size
        py = self.y + offset_y + norm_y * size
        
        return px, py
    
    def redraw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_PANEL)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[15])
        
        self.canvas.clear()
        self.draw_background()
        self.draw_grid()
        self.draw_bezier_path()
        self.draw_control_points()
        self.draw_trace()
        self.draw_robot()
        
    def load_background_image(self, filepath):
        try:
            img = PILImage.open(filepath)
            img = img.convert('RGBA')
            
            size = min(self.width, self.height)
            img = img.resize((int(size), int(size)), PILImage.LANCZOS)
            
            img_data = img.tobytes()
            self.background_texture = Texture.create(size=img.size, colorfmt='rgba')
            self.background_texture.blit_buffer(img_data, colorfmt='rgba', bufferfmt='ubyte')
            self.background_texture.flip_vertical()
            
            self.redraw()
        except Exception as e:
            print(f"Error loading background image: {e}")
    
    def draw_background(self):
        size = min(self.width, self.height)
        offset_x = (self.width - size) / 2
        offset_y = (self.height - size) / 2
        
        with self.canvas:
            if self.background_texture:
                Color(1, 1, 1, 1)
                Rectangle(texture=self.background_texture, 
                         pos=(self.x + offset_x, self.y + offset_y), 
                         size=(size, size))
            else:
                Color(0,0,0, 0.15)
                Rectangle(pos=(self.x + offset_x, self.y + offset_y), size=(size, size))
    
    def draw_grid(self):
        size = min(self.width, self.height)
        offset_x = (self.width - size) / 2
        offset_y = (self.height - size) / 2
        
        with self.canvas:
            Color(1,1,1, 0.1)
            grid_spacing = 24
            
            for i in range(-3, 4):
                field_coord = i * grid_spacing
                px, _ = self.field_to_pixel(field_coord, self.field_min)
                
                Line(points=[px, self.y + offset_y, px, self.y + offset_y + size], width=1)
                
                px_left, py = self.field_to_pixel(self.field_min, field_coord)
                px_right, _ = self.field_to_pixel(self.field_max, field_coord)
                Line(points=[px_left, py, px_right, py], width=1)
            
            Color(1,1,1, 0.2)
            center_x, _ = self.field_to_pixel(0, 0)
            _, center_y = self.field_to_pixel(0, 0)
            
            Line(points=[center_x, self.y + offset_y, center_x, self.y + offset_y + size], width=1.5)
            Line(points=[self.x + offset_x, center_y, self.x + offset_x + size, center_y], width=1.5)
    
    def draw_bezier_path(self):
        if len(self.control_points) < 2:
            return
        
        with self.canvas:
            for i in range(0, len(self.control_points) - 1, 3):
                if i + 3 < len(self.control_points):
                    p0 = np.array(self.control_points[i])
                    p1 = np.array(self.control_points[i + 1])
                    p2 = np.array(self.control_points[i + 2])
                    p3 = np.array(self.control_points[i + 3])
                    
                    Color(*C_SECONDARY, 0.9)
                    points = []
                    for t in np.linspace(0, 1, 50):
                        pt = cubic_bezier(t, p0, p1, p2, p3)
                        px, py = self.field_to_pixel(pt[0], pt[1])
                        points.extend([px, py])
                    
                    if len(points) >= 4:
                        Line(points=points, width=2.5)
                    
                    Color(1,1,1, 0.1)
                    for j in range(3):
                        px1, py1 = self.field_to_pixel(self.control_points[i+j][0], self.control_points[i+j][1])
                        px2, py2 = self.field_to_pixel(self.control_points[i+j+1][0], self.control_points[i+j+1][1])
                        Line(points=[px1, py1, px2, py2], width=1, dash_length=5, dash_offset=2)
                
                elif i + 1 < len(self.control_points):
                    Color(*C_SECONDARY, 0.9)
                    px1, py1 = self.field_to_pixel(self.control_points[i][0], self.control_points[i][1])
                    px2, py2 = self.field_to_pixel(self.control_points[i+1][0], self.control_points[i+1][1])
                    Line(points=[px1, py1, px2, py2], width=2.5)
    
    def draw_control_points(self):
        with self.canvas:
            for i, (fx, fy) in enumerate(self.control_points):
                px, py = self.field_to_pixel(fx, fy)
                
                if i in self.action_points and self.action_points[i]:
                    Color(1, 0.8, 0, 0.8) # Yellow halo
                    Ellipse(pos=(px - 12, py - 12), size=(24, 24))

                if i % 3 == 0:
                    Color(*C_PRIMARY, 1)
                    Ellipse(pos=(px - 8, py - 8), size=(16, 16))
                else:
                    Color(C_PRIMARY[0]*0.8, C_PRIMARY[1]*0.8, C_PRIMARY[2]*0.8, 1)
                    Ellipse(pos=(px - 5, py - 5), size=(10, 10))
    
    def draw_trace(self):
        if len(self.tracePoints) > 1:
            with self.canvas:
                Color(1, 0.6, 0.2, 0.8)
                points = []
                for point in self.tracePoints:
                    px, py = self.field_to_pixel(point[0], point[1])
                    points.extend([px, py])
                if len(points) >= 4:
                    Line(points=points, width=2)
    
    def draw_robot(self):
        x, y = self.robotPose[0], self.robotPose[1]
        theta = self.robotPose[2] % (2 * math.pi)
        
        px, py = self.field_to_pixel(x, y)
        
        with self.canvas:
            Color(*C_ACCENT_RED, 1)
            Ellipse(pos=(px - self.robotRadius, py - self.robotRadius),
                   size=(self.robotRadius * 2, self.robotRadius * 2))
            
            Color(0.2, 0.9, 0.3, 1)
            arrow_length = 10
            
            # --- HEADING CHANGE ---
            # Standard (0_deg=Right): end_x = x + L*cos(th), end_y = y + L*sin(th)
            # New (0_deg=Up): X component is sin, Y component is cos.
            end_x = x + arrow_length * math.sin(theta)
            end_y = y + arrow_length * math.cos(theta)
            # --- END HEADING CHANGE ---

            end_px, end_py = self.field_to_pixel(end_x, end_y)
            Line(points=[px, py, end_px, end_py], width=3)
    
    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return False
        
        fx, fy = self.pixel_to_field(touch.x, touch.y)
        
        # Check if a point was clicked
        for i, (cpx, cpy) in enumerate(self.control_points):
            px, py = self.field_to_pixel(cpx, cpy)
            if abs(touch.x - px) < 15 and abs(touch.y - py) < 15:
                self.selected_point = i
                self.dragging = True
                App.get_running_app().behavior_planner.update_selected_point(i) # NEW
                return True
        
        # If no point was clicked, deselect and add a new one
        self.selected_point = None
        App.get_running_app().behavior_planner.update_selected_point(None)

        if self.field_min <= fx <= self.field_max and self.field_min <= fy <= self.field_max:
            self.control_points.append([fx, fy])
            App.get_running_app().behavior_planner.update_path_points() # NEW
            self.redraw()
            return True
    
    def on_touch_move(self, touch):
        if self.dragging and self.selected_point is not None:
            fx, fy = self.pixel_to_field(touch.x, touch.y)
            
            if self.field_min <= fx <= self.field_max and self.field_min <= fy <= self.field_max:
                self.control_points[self.selected_point] = [fx, fy]
                self.redraw()
                return True
    
    def on_touch_up(self, touch):
        if touch.button == 'right' and self.selected_point is not None:
            deleted_index = self.selected_point
            del self.control_points[deleted_index]
            
            # NEW: Clean up and re-index actions
            if deleted_index in self.action_points:
                del self.action_points[deleted_index]
            
            new_actions = {}
            for idx, action in self.action_points.items():
                if idx > deleted_index:
                    new_actions[idx - 1] = action
                else:
                    new_actions[idx] = action
            self.action_points = new_actions

            App.get_running_app().behavior_planner.update_path_points()
            self.selected_point = None # Deselect after deletion
            App.get_running_app().behavior_planner.update_selected_point(None)
            self.redraw()
        
        self.dragging = False
        # Do not deselect the point on left-click up, so it stays selected for the behavior planner
    
    def generateTrajectory(self):
        """Generate path waypoints with distance and angle information"""
        self.trajectory = []
        
        if len(self.control_points) < 2:
            return
        
        self.path_length = 0
        cumulative_distance = 0
        
        for i in range(0, len(self.control_points) - 1, 3):
            if i + 3 < len(self.control_points):
                p0 = np.array(self.control_points[i])
                p1 = np.array(self.control_points[i + 1])
                p2 = np.array(self.control_points[i + 2])
                p3 = np.array(self.control_points[i + 3])
                
                prev_pt = p0
                for t in np.linspace(0.025, 1, 40): # 40 points per segment
                    pt = cubic_bezier(t, p0, p1, p2, p3)
                    derivative = cubic_bezier_derivative(t, p0, p1, p2, p3)
                    
                    # --- HEADING CHANGE ---
                    # Standard (0_deg=Right): angle = math.atan2(dy, dx) -> atan2(derivative[1], derivative[0])
                    # New (0_deg=Up): angle = math.atan2(dx, dy) -> atan2(derivative[0], derivative[1])
                    angle = math.atan2(derivative[0], derivative[1])
                    # --- END HEADING CHANGE ---
                    
                    seg_dist = np.linalg.norm(pt - prev_pt)
                    cumulative_distance += seg_dist
                    
                    self.trajectory.append({
                        'x': pt[0], 'y': pt[1], 'theta': angle,
                        'distance': cumulative_distance, 'curvature': 0.0
                    })
                    prev_pt = pt
            
            elif i + 1 < len(self.control_points):
                p0 = np.array(self.control_points[i])
                p1 = np.array(self.control_points[i + 1])
                
                direction = p1 - p0
                
                # --- HEADING CHANGE ---
                # Standard (0_deg=Right): angle = math.atan2(dy, dx) -> atan2(direction[1], direction[0])
                # New (0_deg=Up): angle = math.atan2(dx, dy) -> atan2(direction[0], direction[1])
                angle = math.atan2(direction[0], direction[1]) if np.linalg.norm(direction) > 0 else 0
                # --- END HEADING CHANGE ---
                
                prev_pt = p0
                for t in np.linspace(0.05, 1, 20): # 20 points for straight line
                    pt = p0 + (p1 - p0) * t
                    
                    seg_dist = np.linalg.norm(pt - prev_pt)
                    cumulative_distance += seg_dist
                    
                    self.trajectory.append({
                        'x': pt[0], 'y': pt[1], 'theta': angle,
                        'distance': cumulative_distance, 'curvature': 0.0
                    })
                    prev_pt = pt
        self.path_length = cumulative_distance
        
        # Calculate curvature for each point
        for i in range(1, len(self.trajectory) - 1):
            prev_angle = self.trajectory[i - 1]['theta']
            curr_angle = self.trajectory[i]['theta']
            next_angle = self.trajectory[i + 1]['theta']
            
            # Angular change
            delta_angle = (next_angle - prev_angle + math.pi) % (2 * math.pi) - math.pi
            delta_dist = self.trajectory[i + 1]['distance'] - self.trajectory[i - 1]['distance']
            
            if delta_dist > 0.01:
                self.trajectory[i]['curvature'] = delta_angle / delta_dist
        
        if self.suppress_profile_generation:
            # A profile was loaded from a file, don't generate a new one.
            # Just ensure the path length is correct for distance calculations.
            self.motion_graph.path_length_for_profile = self.path_length
            self.suppress_profile_generation = False # Reset the flag
        else:
            # Generate motion profile based on path length
            self.motion_graph.generate_motion_profile(self.path_length)
        
        # Assign velocities to each trajectory point based on motion profile
        for point in self.trajectory:
            point['velocity'] = self.motion_graph.get_velocity_at_distance(point['distance'])
    
    def start_simulation(self, kx_value, ky_value, ktheta_value, start_angle_deg=0):
        if len(self.control_points) < 2:
            return False
        
        self.generateTrajectory()
        
        if not self.trajectory:
            return False
        
        self.controller = LTVUnicycleController(kx=kx_value, ky=ky_value, ktheta=ktheta_value)
        self.isSimulating = True
        
        # --- HEADING CHANGE ---
        # The user's input 'start_angle_deg' is now in the new (0_deg=Up) system.
        # math.radians() converts it correctly to the new radian system.
        # No change is needed here, as the input now matches the internal convention.
        start_angle_rad = math.radians(start_angle_deg)
        self.robotPose = np.array([self.control_points[0][0], self.control_points[0][1], start_angle_rad])
        # --- END HEADING CHANGE ---
        
        self.robotVelocity = 0.0
        self.robotAcceleration = 0.0
        self.robotJerk = 0.0
        self.prev_velocity = 0.0
        self.prev_acceleration = 0.0
        self.simulation_time = 0.0
        self.distance_traveled = 0.0
        self.tracePoints = []
        
        self.motion_graph.clear_actual_data()
        
        if self.simulation_event:
            self.simulation_event.cancel()
        self.simulation_event = Clock.schedule_interval(self.simulate, self.deltaTime)
        return True
    
    def simulate(self, dt):
        if not self.isSimulating or not self.trajectory:
            return False
        
        try:
            # Get target velocity based on distance traveled along path
            target_velocity = self.motion_graph.get_velocity_at_distance(self.distance_traveled)
            
            # Find closest point on trajectory
            min_dist = float('inf')
            closest_idx = 0
            
            for i in range(len(self.trajectory)):
                dist = math.hypot(
                    self.trajectory[i]['x'] - self.robotPose[0],
                    self.trajectory[i]['y'] - self.robotPose[1]
                )
                if dist < min_dist:
                    min_dist = dist
                    closest_idx = i
            
            # Lookahead for reference point (smaller lookahead for better tracking)
            lookahead_points = max(1, min(5, int(target_velocity * 0.1)))
            target_idx = min(closest_idx + lookahead_points, len(self.trajectory) - 1)
            
            ref_point = self.trajectory[target_idx]
            
            # Calculate angular velocity based on path curvature
            if target_idx < len(self.trajectory) - 1:
                next_point = self.trajectory[min(target_idx + 1, len(self.trajectory) - 1)]
                angle_diff = (next_point['theta'] - ref_point['theta'] + math.pi) % (2 * math.pi) - math.pi
                # Angular velocity proportional to linear velocity and curvature
                referenceW = angle_diff * target_velocity
            else:
                referenceW = 0
            
            referenceW = np.clip(referenceW, -self.maxAngularVelocity, self.maxAngularVelocity)
            
            # Use LTV controller to compute control inputs
            v, w = self.controller.calculateControl(
                self.robotPose,
                [ref_point['x'], ref_point['y'], ref_point['theta']],
                target_velocity,
                referenceW
            )
            
            # Apply velocity constraints with smooth acceleration
            desired_velocity = v
            velocity_error = desired_velocity - self.robotVelocity
            
            # Limit acceleration
            max_accel_step = self.maxAcceleration * self.deltaTime
            if velocity_error > max_accel_step:
                velocity_error = max_accel_step
            elif velocity_error < -max_accel_step:
                velocity_error = -max_accel_step
            
            self.robotVelocity += velocity_error
            self.robotVelocity = np.clip(self.robotVelocity, 0, self.maxVelocity)
            
            # Calculate acceleration and jerk for logging
            new_acceleration = (self.robotVelocity - self.prev_velocity) / dt if dt > 0 else 0
            self.robotJerk = (new_acceleration - self.prev_acceleration) / dt if dt > 0 else 0
            self.robotAcceleration = new_acceleration
            
            self.prev_velocity = self.robotVelocity
            self.prev_acceleration = self.robotAcceleration
            
            # Limit angular velocity
            w = np.clip(w, -self.maxAngularVelocity, self.maxAngularVelocity)
            
            # Calculate distance traveled in this timestep
            distance_delta = self.robotVelocity * self.deltaTime
            self.distance_traveled += distance_delta
            
            # Update robot pose using unicycle kinematics
            # --- HEADING CHANGE ---
            # Standard (0_deg=Right): dX = V*cos(th)*dt, dY = V*sin(th)*dt
            # New (0_deg=Up): X component is sin, Y component is cos.
            deltaX = self.robotVelocity * math.sin(self.robotPose[2]) * self.deltaTime
            deltaY = self.robotVelocity * math.cos(self.robotPose[2]) * self.deltaTime
            # --- END HEADING CHANGE ---
            
            self.robotPose[0] += deltaX
            self.robotPose[1] += deltaY
            self.robotPose[2] = (self.robotPose[2] + (w * self.deltaTime)) % (2 * math.pi)
            
            # Clamp to field boundaries
            self.robotPose[0] = np.clip(self.robotPose[0], self.field_min + self.robotRadius, 
                                       self.field_max - self.robotRadius)
            self.robotPose[1] = np.clip(self.robotPose[1], self.field_min + self.robotRadius, 
                                       self.field_max - self.robotRadius)
            
            # Update simulation time and log actual speed/accel/jerk with time
            self.simulation_time += self.deltaTime
            
            # Add actual data with absolute time values
            self.motion_graph.add_actual_data_point(
                self.simulation_time,
                abs(self.robotVelocity),
                self.robotAcceleration,
                self.robotJerk
            )
            
            # Add trace point
            self.tracePoints.append((self.robotPose[0], self.robotPose[1]))
            self.redraw()
            
            # Check if simulation is complete based on distance traveled
            final_point = self.trajectory[-1]
            distance_to_end = math.hypot(
                final_point['x'] - self.robotPose[0],
                final_point['y'] - self.robotPose[1]
            )
            
            path_completion = self.distance_traveled / self.path_length if self.path_length > 0 else 0
            
            if (path_completion >= 0.95 and distance_to_end < 8.0 and abs(self.robotVelocity) < 2.0) or \
               (self.distance_traveled > self.path_length * 1.1):
                self.isSimulating = False
                if self.simulation_event:
                    self.simulation_event.cancel()
                return False
            
        except Exception as e:
            self.isSimulating = False
            if self.simulation_event:
                self.simulation_event.cancel()
            print(f'Simulation Error: {e}')
            return False
    
    def clear_path(self):
        self.control_points = []
        self.trajectory = []
        self.action_points = {}
        self.robotPose = np.array([0.0, 0.0, 0.0])
        self.robotVelocity = 0.0
        self.robotAcceleration = 0.0
        self.robotJerk = 0.0
        self.simulation_time = 0.0
        self.distance_traveled = 0.0
        self.path_length = 0.0
        self.tracePoints = []
        if self.simulation_event:
            self.simulation_event.cancel()
        self.isSimulating = False
        self.motion_graph.clear_actual_data()
        App.get_running_app().behavior_planner.update_path_points()
        self.redraw()
    
    def save_path_to_file(self, filepath):
        """Save path and motion profile to JSON file for robot use"""
        if len(self.control_points) < 2:
            return False
        
        # Generate trajectory with velocities if not already done
        self.generateTrajectory()

        motion_profile_data = {
            'type': self.motion_graph.profile_type,
            'max_speed': self.motion_graph.max_speed,
            'max_acceleration': self.motion_graph.max_acceleration,
            'max_deceleration': self.motion_graph.max_deceleration,
            'max_jerk': self.motion_graph.max_jerk,
            'profile_points': self.motion_graph.generated_profile
        }
        
        path_data = {
            'metadata': {
                'version': '1.2', # Indicate motion profile support
                'path_length': self.path_length,
                'total_time': self.motion_graph.total_time,
                'max_velocity': self.maxVelocity,
                'max_acceleration': self.maxAcceleration,
                'max_angular_velocity': self.maxAngularVelocity,
                'profile_type': self.motion_graph.profile_type,
            },
            'control_points': [
                {'x': float(cp[0]), 'y': float(cp[1])} 
                for cp in self.control_points
            ],
            'action_points': {str(k): v for k, v in self.action_points.items()},
            'trajectory': [
                {
                    'x': float(point['x']),
                    'y': float(point['y']),
                    'theta': float(point['theta']),
                    'distance': float(point['distance']),
                    'velocity': float(point['velocity']),
                    'curvature': float(point['curvature']),
                }
                for point in self.trajectory
            ],
            'motion_profile': motion_profile_data
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(path_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving path: {e}")
            return False
    
    def load_path_from_file(self, filepath):
        """Load path and motion profile from JSON file"""
        try:
            with open(filepath, 'r') as f:
                path_data = json.load(f)
            
            self.control_points = [
                [cp['x'], cp['y']] 
                for cp in path_data['control_points']
            ]
            self.action_points = {int(k): v for k, v in path_data.get('action_points', {}).items()}
            
            metadata = path_data.get('metadata', {})
            app = App.get_running_app()

            if 'motion_profile' in path_data:
                # New format with full motion profile included
                motion_profile = path_data['motion_profile']
                self.motion_graph.profile_type = motion_profile.get('type', 'trapezoidal')
                self.motion_graph.max_speed = motion_profile.get('max_speed', 60.0)
                self.motion_graph.max_acceleration = motion_profile.get('max_acceleration', 100.0)
                self.motion_graph.max_deceleration = motion_profile.get('max_deceleration', 100.0)
                self.motion_graph.max_jerk = motion_profile.get('max_jerk', 500.0)
                self.motion_graph.generated_profile = motion_profile.get('profile_points', [])
                
                self.maxVelocity = self.motion_graph.max_speed
                self.maxAcceleration = self.motion_graph.max_acceleration
                if self.motion_graph.generated_profile:
                    self.motion_graph.total_time = self.motion_graph.generated_profile[-1].get('time', 10.0)
                
                self.suppress_profile_generation = True
            else:
                # Old format, read from metadata and generate profile
                self.motion_graph.profile_type = metadata.get('profile_type', 'trapezoidal')
                self.maxVelocity = metadata.get('max_velocity', 60.0)
                self.maxAcceleration = metadata.get('max_acceleration', 100.0)
                self.motion_graph.max_speed = self.maxVelocity
                self.motion_graph.max_acceleration = self.maxAcceleration
                self.motion_graph.max_deceleration = app.decel_slider.value
                self.motion_graph.max_jerk = app.jerk_slider.value
                self.motion_graph.generated_profile = []
                self.suppress_profile_generation = False

            self.maxAngularVelocity = metadata.get('max_angular_velocity', 3.0)
            
            # Update UI sliders and profile type buttons to reflect loaded values
            app.vel_slider.value = self.motion_graph.max_speed
            app.accel_slider.value = self.motion_graph.max_acceleration
            app.decel_slider.value = self.motion_graph.max_deceleration
            app.jerk_slider.value = self.motion_graph.max_jerk

            if self.motion_graph.profile_type == 'trapezoidal':
                app.trap_btn.state = 'down'
            elif self.motion_graph.profile_type == 's-curve':
                app.scurve_btn.state = 'down'
            elif self.motion_graph.profile_type == 'custom':
                app.custom_btn.state = 'down'

            self.generateTrajectory()
            app.behavior_planner.update_path_points() # Update behavior planner UI
            
            self.redraw()
            return True
        except Exception as e:
            print(f"Error loading path: {e}")
            return False

# NEW: Behavior Planning Widget
class BehaviorPlanner(RoundedBoxLayout):
    selected_point_index = NumericProperty(-1)
    selected_point_text = StringProperty('No point selected')

    def __init__(self, path_canvas, **kwargs):
        super().__init__(**kwargs)
        self.path_canvas = path_canvas
        self.orientation = 'vertical'
        self.spacing = 15
        self.padding = 20

        self.add_widget(Label(text="Behavior Planning", font_size='22sp', bold=True, color=C_TEXT, size_hint_y=None, height=40))
        
        self.selected_label = Label(text=self.selected_point_text, size_hint_y=None, height=30, color=C_HINT_TEXT)
        self.add_widget(self.selected_label)

        # NEW: Button for precise coordinates
        self.edit_coords_btn = ModernButton(
            text="Edit Coordinates", 
            size_hint_y=None, 
            height=45,
            disabled=True # Disabled by default
        )
        self.edit_coords_btn.bind(on_press=self.open_precise_input_popup)
        self.add_widget(self.edit_coords_btn)

        # Controls for actions
        controls_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=150)
        
        # Intake
        controls_layout.add_widget(Label(text="Intake State:", color=C_TEXT))
        self.intake_spinner = ModernSpinner(text='None', values=['None', 'intakeToBackpack', 'backpackToMiddle', 'backpackToTop', 'backpackToBottom', 'frontForward', 'frontBackward', 'zeroIntake'])
        controls_layout.add_widget(self.intake_spinner)
        
        # Tongue
        controls_layout.add_widget(Label(text="Tongue:", color=C_TEXT))
        self.tongue_spinner = ModernSpinner(text='No Change', values=['No Change', 'On', 'Off'])
        controls_layout.add_widget(self.tongue_spinner)

        # Aligner
        controls_layout.add_widget(Label(text="Aligner:", color=C_TEXT))
        self.aligner_spinner = ModernSpinner(text='No Change', values=['No Change', 'On', 'Off'])
        controls_layout.add_widget(self.aligner_spinner)

        self.add_widget(controls_layout)

        save_btn = ModernButton(text="Save Actions for Point", size_hint_y=None, height=45)
        save_btn.bind(on_press=self.save_actions)
        self.add_widget(save_btn)
        
        # Spacer
        self.add_widget(Widget())

    # NEW: Method to open the precise input popup
    def open_precise_input_popup(self, instance):
        if self.selected_point_index != -1:
            popup = PreciseInputPopup(
                path_canvas=self.path_canvas,
                point_index=self.selected_point_index
            )
            popup.open()

    def update_selected_point(self, index):
        if index is None:
            self.selected_point_index = -1
            self.selected_point_text = 'No point selected'
            self.edit_coords_btn.disabled = True # NEW: Disable button
        else:
            self.selected_point_index = index
            self.selected_point_text = f'Editing Point {index}'
            self.edit_coords_btn.disabled = False # NEW: Enable for any point
            
            if index % 3 == 0:
                self.selected_point_text += f' (Anchor {index // 3})'
            else:
                self.selected_point_text += ' (Handle)'
        
        self.load_actions_for_point() # Load actions regardless (will clear if not anchor)
        self.selected_label.text = self.selected_point_text

    def update_path_points(self):
        # Called when path is cleared or loaded
        self.update_selected_point(None)
        
    def load_actions_for_point(self):
        if self.selected_point_index != -1 and self.selected_point_index % 3 == 0 and self.selected_point_index in self.path_canvas.action_points:
            actions = self.path_canvas.action_points[self.selected_point_index]
            self.intake_spinner.text = actions.get('intake', 'None')
            self.tongue_spinner.text = 'On' if actions.get('tongue') else 'Off' if 'tongue' in actions else 'No Change'
            self.aligner_spinner.text = 'On' if actions.get('aligner') else 'Off' if 'aligner' in actions else 'No Change'
        else:
            self.intake_spinner.text = 'None'
            self.tongue_spinner.text = 'No Change'
            self.aligner_spinner.text = 'No Change'

    def save_actions(self, instance):
        if self.selected_point_index == -1 or self.selected_point_index % 3 != 0:
            popup = App.get_running_app().create_modern_popup('Error', 'Select an anchor point (a large circle) to save actions!')
            popup.open()
            return

        actions = {}
        if self.intake_spinner.text != 'None':
            actions['intake'] = self.intake_spinner.text
        if self.tongue_spinner.text != 'No Change':
            actions['tongue'] = self.tongue_spinner.text == 'On'
        if self.aligner_spinner.text != 'No Change':
            actions['aligner'] = self.aligner_spinner.text == 'On'
        
        if actions:
            self.path_canvas.action_points[self.selected_point_index] = actions
        elif self.selected_point_index in self.path_canvas.action_points:
            del self.path_canvas.action_points[self.selected_point_index]

        self.path_canvas.redraw()
        popup = App.get_running_app().create_modern_popup('Success', f'Actions saved for point {self.selected_point_index // 3}.')
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 1.5)


class PathPlannerApp(App):
    def build(self):
        main_layout = BoxLayout(orientation='horizontal', padding=20, spacing=20)
        
        # --- LEFT COLUMN ---
        left_column = BoxLayout(orientation='vertical', size_hint_x=0.6, spacing=20)
        
        # Path Canvas
        self.motion_graph = MotionProfileGraph() # Needs to be initialized before PathCanvas
        self.path_canvas = PathCanvas(self.motion_graph, size_hint_y=0.7)
        left_column.add_widget(self.path_canvas)

        # Path Controls Panel
        path_controls = RoundedBoxLayout(orientation='vertical', size_hint_y=0.3, spacing=10, padding=20)
        
        title = Label(
            text='Path & Simulation Controls',
            font_size='22sp', bold=True, color=C_TEXT,
            size_hint_y=None, height=40
        )
        path_controls.add_widget(title)
        
        info_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=25, spacing=20)
        self.control_points_label = Label(text='Points: 0', font_size='13sp', color=C_HINT_TEXT)
        self.robot_label = Label(text='Robot: (0, 0, 0°) | V: 0', font_size='13sp', color=C_HINT_TEXT)
        info_box.add_widget(self.control_points_label)
        info_box.add_widget(self.robot_label)
        path_controls.add_widget(info_box)
        
        params_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=65, spacing=15)
        
        # kx input with label
        kx_layout = BoxLayout(orientation='vertical', spacing=5)
        kx_layout.add_widget(Label(text='kx', font_size='12sp', color=C_HINT_TEXT, size_hint_y=None, height=15))
        self.kx_input = ModernTextInput(text='1.5', multiline=False, font_size='13sp')
        kx_layout.add_widget(self.kx_input)
        params_box.add_widget(kx_layout)

        # ky input with label
        ky_layout = BoxLayout(orientation='vertical', spacing=5)
        ky_layout.add_widget(Label(text='ky', font_size='12sp', color=C_HINT_TEXT, size_hint_y=None, height=15))
        self.ky_input = ModernTextInput(text='3.0', multiline=False, font_size='13sp')
        ky_layout.add_widget(self.ky_input)
        params_box.add_widget(ky_layout)

        # ktheta input with label
        ktheta_layout = BoxLayout(orientation='vertical', spacing=5)
        ktheta_layout.add_widget(Label(text='kθ', font_size='12sp', color=C_HINT_TEXT, size_hint_y=None, height=15))
        self.ktheta_input = ModernTextInput(text='2.0', multiline=False, font_size='13sp')
        ktheta_layout.add_widget(self.ktheta_input)
        params_box.add_widget(ktheta_layout)

        # angle input with label
        angle_layout = BoxLayout(orientation='vertical', spacing=5)
        angle_layout.add_widget(Label(text='angle°', font_size='12sp', color=C_HINT_TEXT, size_hint_y=None, height=15))
        self.angle_input = ModernTextInput(text='0', multiline=False, font_size='13sp')
        angle_layout.add_widget(self.angle_input)
        params_box.add_widget(angle_layout)
        
        path_controls.add_widget(params_box)
        
        buttons_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        
        start_btn = ModernButton(text='Start Sim')
        start_btn.bind(on_press=self.start_simulation)
        start_btn.bg_color.rgba = C_ACCENT_GREEN

        clear_btn = ModernButton(text='Clear Path')
        clear_btn.bind(on_press=self.clear_path)
        clear_btn.bg_color.rgba = C_ACCENT_RED
        
        load_bg_btn = ModernButton(text='BG')
        load_bg_btn.bind(on_press=self.show_file_chooser)
        
        save_path_btn = ModernButton(text='Save')
        save_path_btn.bind(on_press=self.save_path)
        
        load_path_btn = ModernButton(text='Load')
        load_path_btn.bind(on_press=self.load_path)
        
        buttons_box.add_widget(start_btn)
        buttons_box.add_widget(clear_btn)
        buttons_box.add_widget(load_bg_btn)
        buttons_box.add_widget(save_path_btn)
        buttons_box.add_widget(load_path_btn)
        path_controls.add_widget(buttons_box)
        
        instructions = Label(
            text='Left-click to add points • Drag to move • Right-click to delete',
            font_size='11sp', color=C_HINT_TEXT,
            size_hint_y=None, height=20
        )
        path_controls.add_widget(instructions)
        
        left_column.add_widget(path_controls)
        main_layout.add_widget(left_column)
        
        # --- RIGHT COLUMN ---
        right_column = BoxLayout(orientation='vertical', size_hint_x=0.4, spacing=20)
        
        motion_profile_section = RoundedBoxLayout(orientation='vertical', size_hint_y=0.6, spacing=10, padding=20)
        
        motion_profile_section.add_widget(Label(
            text='Motion Profile Configuration',
            font_size='22sp', bold=True, color=C_TEXT, size_hint_y=None, height=40))

        # Profile Type
        type_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        type_label = Label(text='Profile Type:', size_hint_x=0.3, font_size='14sp', color=C_TEXT, bold=True)
        type_box.add_widget(type_label)
        self.trap_btn = ModernToggleButton(text='Trapezoidal', group='profile', state='down')
        self.scurve_btn = ModernToggleButton(text='S-Curve', group='profile')
        self.custom_btn = ModernToggleButton(text='Custom', group='profile')
        self.trap_btn.bind(on_press=self.set_trapezoidal)
        self.scurve_btn.bind(on_press=self.set_scurve)
        self.custom_btn.bind(on_press=self.set_custom)
        type_box.add_widget(self.trap_btn)
        type_box.add_widget(self.scurve_btn)
        type_box.add_widget(self.custom_btn)
        motion_profile_section.add_widget(type_box)
        
        # Sliders
        params_section = GridLayout(cols=3, spacing=10, row_default_height=30, row_force_default=True, size_hint_y=None, height=160)

        def create_slider(name, min_val, max_val, default, callback):
            label = Label(text=name, font_size='14sp', color=C_TEXT, bold=True)
            params_section.add_widget(label)
            slider = Slider(min=min_val, max=max_val, value=default, cursor_size=(20, 20), value_track=True, value_track_color=C_PRIMARY)
            value_label = Label(text=f'{default:.1f}', size_hint_x=0.3, font_size='13sp', color=C_TEXT)
            slider.bind(value=lambda instance, value: setattr(value_label, 'text', f'{value:.1f}'))
            slider.bind(value=callback)
            params_section.add_widget(slider)
            params_section.add_widget(value_label)
            return slider, value_label

        self.vel_slider, self.vel_value = create_slider('Max Velocity', 10, 100, 60, self.update_velocity)
        self.accel_slider, self.accel_value = create_slider('Max Accel', 20, 200, 100, self.update_acceleration)
        self.decel_slider, self.decel_value = create_slider('Max Decel', 20, 200, 100, self.update_deceleration)
        self.jerk_slider, self.jerk_value = create_slider('Max Jerk', 100, 1000, 500, self.update_jerk)
        
        motion_profile_section.add_widget(params_section)
        
        # Display Toggles
        display_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=10)
        display_label = Label(text='Display:', size_hint_x=0.3, font_size='14sp', color=C_TEXT, bold=True)
        display_box.add_widget(display_label)
        self.show_vel_btn = ModernToggleButton(text='Velocity', state='down')
        self.show_accel_btn = ModernToggleButton(text='Acceleration')
        self.show_jerk_btn = ModernToggleButton(text='Jerk')
        self.show_vel_btn.bind(on_press=self.toggle_velocity_display)
        self.show_accel_btn.bind(on_press=self.toggle_accel_display)
        self.show_jerk_btn.bind(on_press=self.toggle_jerk_display)
        display_box.add_widget(self.show_vel_btn)
        display_box.add_widget(self.show_accel_btn)
        display_box.add_widget(self.show_jerk_btn)
        motion_profile_section.add_widget(display_box)
        
        # Motion Graph
        motion_profile_section.add_widget(self.motion_graph)
        
        # Generate/Clear Buttons
        graph_controls = BoxLayout(orientation='horizontal', size_hint_y=None, height=45, spacing=10)
        generate_btn = ModernButton(text='Generate Profile')
        generate_btn.bind(on_press=self.generate_profile)
        clear_graph_btn = ModernButton(text='Clear Custom')
        clear_graph_btn.bind(on_press=self.clear_graph)
        graph_controls.add_widget(generate_btn)
        graph_controls.add_widget(clear_graph_btn)
        motion_profile_section.add_widget(graph_controls)
        
        right_column.add_widget(motion_profile_section)
        
        # Behavior Planner
        self.behavior_planner = BehaviorPlanner(self.path_canvas, size_hint_y=0.4)
        right_column.add_widget(self.behavior_planner)

        main_layout.add_widget(right_column)
        
        Clock.schedule_interval(self.update_labels, 0.1)
        
        return main_layout
    
    def set_trapezoidal(self, instance):
        if instance.state == 'down':
            self.motion_graph.profile_type = 'trapezoidal'
            if len(self.path_canvas.control_points) >= 2:
                self.path_canvas.generateTrajectory()
    
    def set_scurve(self, instance):
        if instance.state == 'down':
            self.motion_graph.profile_type = 's-curve'
            if len(self.path_canvas.control_points) >= 2:
                self.path_canvas.generateTrajectory()
    
    def set_custom(self, instance):
        if instance.state == 'down':
            self.motion_graph.profile_type = 'custom'
            if len(self.path_canvas.control_points) >= 2:
                self.path_canvas.generateTrajectory()
    
    def update_velocity(self, instance, value):
        self.motion_graph.max_speed = value
        self.path_canvas.maxVelocity = value
        if len(self.path_canvas.control_points) >= 2:
            self.path_canvas.generateTrajectory()
    
    def update_acceleration(self, instance, value):
        self.motion_graph.max_acceleration = value
        self.path_canvas.maxAcceleration = value
        if len(self.path_canvas.control_points) >= 2:
            self.path_canvas.generateTrajectory()
    
    def update_deceleration(self, instance, value):
        self.motion_graph.max_deceleration = value
        if len(self.path_canvas.control_points) >= 2:
            self.path_canvas.generateTrajectory()
    
    def update_jerk(self, instance, value):
        self.motion_graph.max_jerk = value
        if len(self.path_canvas.control_points) >= 2:
            self.path_canvas.generateTrajectory()
    
    def toggle_velocity_display(self, instance):
        self.motion_graph.show_velocity = instance.state == 'down'
        self.motion_graph.redraw()
    
    def toggle_accel_display(self, instance):
        self.motion_graph.show_acceleration = instance.state == 'down'
        self.motion_graph.redraw()
    
    def toggle_jerk_display(self, instance):
        self.motion_graph.show_jerk = instance.state == 'down'
        self.motion_graph.redraw()
    
    def generate_profile(self, instance):
        if len(self.path_canvas.control_points) >= 2:
            self.path_canvas.generateTrajectory()
            popup = self.create_modern_popup('Success', f'Profile generated!\nPath: {self.path_canvas.path_length:.1f} | Time: {self.motion_graph.total_time:.1f}s')
            Clock.schedule_once(lambda dt: popup.dismiss(), 2.0)
            popup.open()
        else:
            self.create_modern_popup('Warning', 'Please create a path first!').open()
    
    def clear_graph(self, instance):
        self.motion_graph.clear()
    
    def create_modern_popup(self, title, text_content):
        content = RoundedBoxLayout(orientation='vertical', padding=20, spacing=10)
        content.add_widget(Label(text=text_content, color=C_TEXT))
        popup = Popup(title=title, title_color=C_TEXT, content=content, size_hint=(0.4, 0.3),
                      background_color=C_BACKGROUND, separator_color=C_PRIMARY)
        return popup

    def show_file_chooser(self, instance):
        content = RoundedBoxLayout(orientation='vertical', spacing=10, padding=10)
        
        file_chooser = FileChooserListView(
            filters=['*.png', '*.jpg', '*.jpeg', '*.bmp'],
            size_hint_y=0.9
        )
        
        button_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        
        select_btn = ModernButton(text='Select')
        cancel_btn = ModernButton(text='Cancel')
        
        button_layout.add_widget(select_btn)
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(file_chooser)
        content.add_widget(button_layout)
        
        popup = Popup(title='Choose Background Image', content=content, size_hint=(0.9, 0.9),
                      background_color=C_BACKGROUND, title_color=C_TEXT)
        
        def select_file(instance):
            if file_chooser.selection:
                self.path_canvas.load_background_image(file_chooser.selection[0])
                popup.dismiss()
        
        select_btn.bind(on_press=select_file)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def save_path(self, instance):
        """Show file chooser to save path"""
        content = RoundedBoxLayout(orientation='vertical', spacing=10, padding=10)
        
        file_chooser = FileChooserListView(filters=['*.json'], size_hint_y=0.7)
        
        filename_input = ModernTextInput(
            hint_text='Enter filename (e.g., my_path.json)',
            multiline=False, size_hint_y=None, height=40
        )
        
        button_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        save_btn = ModernButton(text='Save')
        cancel_btn = ModernButton(text='Cancel')
        button_layout.add_widget(save_btn)
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(Label(text='Save Path File', size_hint_y=None, height=40, bold=True, font_size='16sp', color=C_TEXT))
        content.add_widget(file_chooser)
        content.add_widget(filename_input)
        content.add_widget(button_layout)
        
        popup = Popup(title='Save Path', content=content, size_hint=(0.9, 0.9),
                      background_color=C_BACKGROUND, title_color=C_TEXT)
        
        def do_save(instance):
            if len(self.path_canvas.control_points) < 2:
                self.create_modern_popup('Error', 'Please create a path first!').open()
                return
            
            filename = filename_input.text.strip()
            if not filename:
                filename = 'path.json'
            elif not filename.endswith('.json'):
                filename += '.json'
            
            directory = file_chooser.path
            filepath = os.path.join(directory, filename)
            
            success = self.path_canvas.save_path_to_file(filepath)
            if success:
                popup.dismiss()
                success_popup = self.create_modern_popup('Success', f'Path saved to:\n{filepath}')
                Clock.schedule_once(lambda dt: success_popup.dismiss(), 2.0)
                success_popup.open()
            else:
                self.create_modern_popup('Error', 'Failed to save path file!').open()
        
        save_btn.bind(on_press=do_save)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def load_path(self, instance):
        """Show file chooser to load path"""
        content = RoundedBoxLayout(orientation='vertical', spacing=10, padding=10)
        
        file_chooser = FileChooserListView(filters=['*.json'], size_hint_y=0.9)
        
        button_layout = BoxLayout(size_hint_y=None, height=45, spacing=10)
        load_btn = ModernButton(text='Load')
        cancel_btn = ModernButton(text='Cancel')
        button_layout.add_widget(load_btn)
        button_layout.add_widget(cancel_btn)
        
        content.add_widget(file_chooser)
        content.add_widget(button_layout)
        
        popup = Popup(title='Load Path File', content=content, size_hint=(0.9, 0.9),
                      background_color=C_BACKGROUND, title_color=C_TEXT)
        
        def do_load(instance):
            if file_chooser.selection:
                filepath = file_chooser.selection[0]
                success = self.path_canvas.load_path_from_file(filepath)
                
                if success:
                    popup.dismiss()
                    success_popup = self.create_modern_popup('Success', f'Path loaded from:\n{filepath}')
                    Clock.schedule_once(lambda dt: success_popup.dismiss(), 2.0)
                    success_popup.open()
                else:
                    self.create_modern_popup('Error', 'Failed to load path file!').open()
        
        load_btn.bind(on_press=do_load)
        cancel_btn.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def update_labels(self, dt):
        canvas = self.path_canvas
        self.control_points_label.text = f'Points: {len(canvas.control_points)}'
        
        # --- HEADING CHANGE ---
        # The robotPose[2] is now already in the (0_deg=Up) system.
        # math.degrees() converts it correctly for display. No change needed.
        angle_deg = math.degrees(canvas.robotPose[2] % (2 * math.pi))
        # --- END HEADING CHANGE ---
        
        self.robot_label.text = f'Robot: ({canvas.robotPose[0]:.1f}, {canvas.robotPose[1]:.1f}, {angle_deg:.1f}°) | V: {canvas.robotVelocity:.1f}'
    
    def start_simulation(self, instance):
        try:
            kx_value = float(self.kx_input.text) if self.kx_input.text else 1.5
            ky_value = float(self.ky_input.text) if self.ky_input.text else 3.0
            ktheta_value = float(self.ktheta_input.text) if self.ktheta_input.text else 2.0
            
            # --- HEADING CHANGE ---
            # The 'angle_value' from the text box is now interpreted
            # as 0_deg=Up, 90_deg=Right, etc.
            angle_value = float(self.angle_input.text) if self.angle_input.text else 0.0
            # --- END HEADING CHANGE ---
            
            success = self.path_canvas.start_simulation(kx_value, ky_value, ktheta_value, angle_value)
            
            if not success:
                self.create_modern_popup('Warning', 'Please create a path first!').open()
        except ValueError:
            self.create_modern_popup('Error', 'Please enter valid numbers for parameters.').open()
    
    def clear_path(self, instance):
        self.path_canvas.clear_path()
        self.motion_graph.clear()
        self.kx_input.text = '1.5'
        self.ky_input.text = '3.0'
        self.ktheta_input.text = '2.0'
        self.angle_input.text = '0'


if __name__ == '__main__':
    PathPlannerApp().run()