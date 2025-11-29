import math
import time
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3

class CircleDrive(Node):
    def __init__(self, topic_name='/cmd_vel'):
        super().__init__('circle_drive')
        self.publisher_ = self.create_publisher(Twist, topic_name, 1)
        time.sleep(2.0)

    def drive(self, wait, motion = Twist()):
        self.publisher_.publish(motion)
        time.sleep(wait)
        self.publisher_.publish(Twist())

def main(args=None):
    rclpy.init(args=args)
    node = CircleDrive()
    motion = Twist(linear=Vector3(x=0.2), angular=Vector3(z=0.4))
    wait = 2 * math.pi / motion.angular.z
    node.drive(wait=wait, motion=motion)
