import numpy as np

def cubic_bezier(t, p0, p1, p2, p3):
    """Calculate point on cubic Bezier curve"""
    return (1-t)**3 * p0 + 3*(1-t)**2*t * p1 + 3*(1-t)*t**2 * p2 + t**3 * p3

def cubic_bezier_derivative(t, p0, p1, p2, p3):
    """Calculate derivative (tangent) of cubic Bezier curve"""
    return 3*(1-t)**2 * (p1 - p0) + 6*(1-t)*t * (p2 - p1) + 3*t**2 * (p3 - p2)
