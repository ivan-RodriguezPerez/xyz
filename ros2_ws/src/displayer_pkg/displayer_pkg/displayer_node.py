import rclpy
from rclpy.node import Node
from interfaces_pkg.msg import NavigationStatus

import cv2
import numpy as np


class DisplayerNode(Node):
    def __init__(self):

        super().__init__('displayer_node')
        self.get_logger().info("Started displayer node")

        # Create subscription
        self.subscription = self.create_subscription(
            NavigationStatus,
            '/displayer_topic',
            self.image_callback,
            10
        )

        self.get_logger().info("Successfully created dashboard node.")

    def image_callback(self, msg):

        distance_remaining = msg.distance_remaining
        timeout_time = msg.timeout_time

        self.get_logger().info(f'Message received:\n  distance_remaining: {distance_remaining}\n  timeout time: {timeout_time}')

        self.display_results(distance_remaining, timeout_time)

    def display_results(self, distance_remaining, timeout_time):

        frame = np.zeros((0, 0, 3))
        color = (255, 255, 255)

        # Distance
        cv2.putText(
            frame, f"Distance remaining {distance_remaining}",
            (30, 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )
        # Timeout
        cv2.putText(
            frame, f"Timeout time {timeout_time}",
            (75, 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )

        cv2.imshow('Navigation Status', frame)
        cv2.waitKey(1)


def main(args=None):
    rclpy.init(args=args)
    node = DisplayerNode()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == "__main__":
    main()
