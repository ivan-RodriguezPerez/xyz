import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import time

class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        #self.number_ = 0
        self.publisher_ = self.create_publisher(String, 'topic', 10)
        timer_period = 0.05  # seconds
        self.timer_ = self.create_timer(timer_period, self.publish_data)
        self.get_logger().info('minimal_publisher has been started.')

    def publish_data(self):
        msg = String()
        #msg.data = f'Hello World {self.number_}'
        msg.data = f'Hello World {time.time()}'
        self.publisher_.publish(msg)
        self.get_logger().info(f'Publishing: {msg.data}')
        #self.number_ += 1


def main(args=None):
    rclpy.init(args=args)
    node = MinimalPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
