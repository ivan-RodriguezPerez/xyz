import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3

class CircleDrive(Node):
    def __init__(self, topic_name='/cmd_vel'):
        super().__init__('circle_drive')
        self.publisher_ = self.create_publisher(Twist, topic_name, 10)
        self.get_logger().info('Successfully initialised Commander Node')

    def drive(self, duration, motion):
        # Publish movement
        self.publisher_.publish(motion)
        self.get_logger().info('Moving...')

        # Wait without blocking ros
        end_time = self.get_clock().now() + rclpy.duration.Duration(seconds=duration)
        while rclpy.ok() and self.get_clock().now() < end_time:
            rclpy.spin_once(self, timeout_sec=0.1)

        # Detener robot
        self.publisher_.publish(Twist())
        self.get_logger().info('Stopped.')

def main(args=None):
    rclpy.init(args=args)
    node = CircleDrive()

    motion = Twist()
    motion.linear.x = 0.2
    motion.angular.z = 0.4

    wait = 2 * math.pi / motion.angular.z

    node.drive(wait, motion)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
