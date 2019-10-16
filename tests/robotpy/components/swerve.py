from ctre import WPI_TalonSRX
import math
import numpy as np

from pyswervedrive import Chassis, Controller

from collections import namedtuple
SwerveConfig = namedtuple("SwerveConfig", ["alpha", "l", "r"])


class SwerveModule:
    drive_motor: WPI_TalonSRX
    steer_motor: WPI_TalonSRX
    config: SwerveConfig

    def __init__(self):
        self.speed = 0.0
        self.angle = 0.0

    def setup(self):
        self.kTimeoutMs = 10
        self.kSlotIdx = 0
        self.kPIDLoopIdx = 0

        self.steer_motor.configSelectedFeedbackSensor(
            WPI_TalonSRX.FeedbackDevice.CTRE_MagEncoder_Relative,
            self.kPIDLoopIdx,
            self.kTimeoutMs
        )

        # choose to ensure sensor is positive when output is positive
        self.steer_motor.setSensorPhase(True)

        # choose based on what direction you want forward/positive to be.
        # This does not affect sensor phase.
        self.steer_motor.setInverted(False)

        # Set the allowable closed-loop error, Closed-Loop output will be
        # neutral within this range. See Table in Section 17.2.1 for native
        # units per rotation.
        self.steer_motor.configAllowableClosedloopError(0, self.kPIDLoopIdx, self.kTimeoutMs)

        # set closed loop gains in slot0, typically kF stays zero - see documentation */
        self.steer_motor.selectProfileSlot(self.kSlotIdx, self.kPIDLoopIdx)
        self.steer_motor.config_kF(0, 0, self.kTimeoutMs)
        self.steer_motor.config_kP(0, 5, self.kTimeoutMs)
        self.steer_motor.config_kI(0, 0, self.kTimeoutMs)
        self.steer_motor.config_kD(0, 0, self.kTimeoutMs)

        # zero the sensor
        self.steer_motor.setSelectedSensorPosition(0, self.kPIDLoopIdx, self.kTimeoutMs)

    def drive(self, speed, angle):
        self.speed = speed
        self.angle = angle

    def bound(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def execute(self):
        talon_speed = self.speed / 3.0
        # 4096 counts per revolution
        current_counts = self.steer_motor.getQuadraturePosition()
        current_angle = current_counts / 4096.0 * 2.0 * math.pi
        delta = self.bound(self.angle - current_angle)
        delta_flipped = self.bound(self.angle - current_angle + math.pi)
        if abs(delta) < abs(delta_flipped):
            chosen = delta
        else:
            chosen = delta_flipped
        counts = current_counts + int(chosen / (2.0*math.pi) * 4096)
        mod_counts = counts % 4096
        mod_angle = mod_counts / 4096.0 * 2.0 * math.pi
        if abs(self.bound(mod_angle - self.angle)) > 0.1:
            talon_speed = -talon_speed
        self.drive_motor.set(talon_speed)
        self.steer_motor.set(WPI_TalonSRX.ControlMode.Position, counts)

class SwerveChassis:
    lr_swerve: SwerveModule
    rr_swerve: SwerveModule
    lf_swerve: SwerveModule
    rf_swerve: SwerveModule

    def __init__(self):
        self.vx = None
        self.vy = None
        self.vz = None

    def setup(self):
        self.modules = [self.lr_swerve, self.rr_swerve, self.lf_swerve, self.rf_swerve]
        alpha = np.array([module.config.alpha for module in self.modules])
        l = np.array([module.config.l for module in self.modules])
        r = np.array([module.config.r for module in self.modules])
        self.icr_chassis = Chassis(alpha, l, r)
        self.controller = Controller(self.icr_chassis)


    def drive(self, vx, vy, vz):
        for module in self.modules:
            x = vx + vz * -math.sin(module.config.alpha) * module.config.l
            y = vy + vz * math.cos(module.config.alpha) * module.config.l
            speed = math.hypot(x, y)
            direction = math.atan2(y, x)
            module.drive(speed, direction)

    def icr_drive(self, vx, vy, vz):
        self.vx = vx
        self.vy = vy
        self.vz = vz

    def execute(self):
        if self.vx is not None:
            # We're using the ICR controller
            beta = np.array([(module.steer_motor.getQuadraturePosition()+1024)/4096*2*math.pi+module.config.alpha
                for module in self.modules])
            phi_dot = np.array([module.drive_motor.get() for module in self.modules])
            self.controller.updateStates(beta, phi_dot)
            controls = self.controller.controlStep(self.vx, self.vy, self.vz)
            for c, m in zip(controls, self.modules):
                m.drive(c[1], c[0])
