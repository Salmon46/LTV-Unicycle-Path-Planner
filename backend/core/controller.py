import math

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
        
        # --- HEADING CORRECTION (0-deg=Up) ---
        # ex_robot (forward error) = ex*sin(th) + ey*cos(th)
        # ey_robot (lateral error) = ex*cos(th) - ey*sin(th)
        ex_robot = ex * math.sin(currentTheta) + ey * math.cos(currentTheta)
        ey_robot = ex * math.cos(currentTheta) - ey * math.sin(currentTheta)
        
        etheta = (referenceTheta - currentTheta + math.pi) % (2 * math.pi) - math.pi
        
        v = referenceLinearVelocity * math.cos(etheta) + self.kx * ex_robot
        
        if abs(referenceLinearVelocity) > 0.1:
            w = referenceAngularVelocity + referenceLinearVelocity * (self.ky * ey_robot + self.ktheta * math.sin(etheta))
        else:
            w = referenceAngularVelocity + self.ktheta * etheta
        
        return v, w
