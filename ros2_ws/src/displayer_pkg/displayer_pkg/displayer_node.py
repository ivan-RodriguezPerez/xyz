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

        self.display_results(-99.99, -99.99)

        self.get_logger().info("Successfully created dashboard node.")

    def image_callback(self, msg):

        distance_remaining = msg.distance_remaining
        timeout_time = msg.timeout_time

        self.get_logger().info(f'Message received: distance_remaining: {distance_remaining} m,  timeout time: {timeout_time} s')

        self.display_results(distance_remaining, timeout_time)

    def display_results(self, distance_remaining, timeout_time):

        frame = np.zeros((200, 800, 3))
        color = (255, 255, 255)
        font_scale = 1.5
        thickness = 2

        # Distance
        cv2.putText(
            frame, f"Distance remaining {distance_remaining} m",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color, thickness
        )
        # Timeout
        cv2.putText(
            frame, f"Timeout time {timeout_time} s",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color, thickness
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
