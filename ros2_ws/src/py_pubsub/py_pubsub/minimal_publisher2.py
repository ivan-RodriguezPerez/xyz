import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MinimalPublisher(Node):
    def __init__(self):
        super().__init__("minimal_publisher")
        self.number_ = 2
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.5 # seconds
        self.timer_ = self.create_timer(timer_period, self.timer_callback)
        self.i = 0
        self.get_logger().info("minimal_publisher has been started.")

    def publish_number(self):
        msg = String()
        msg.data = f'Hello World {self.i}'
        self.number_publisher_.publish(msg)
        self.get_logger().info(f'Publishing: {msg.data}')
        self.i += 1


def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()
    rclpy.spin(minimal_publisher)
    rclpy.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
    