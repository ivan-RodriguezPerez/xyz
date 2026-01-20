import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import requests
from requests.exceptions import Timeout, ConnectionError, HTTPError


class SpeakerNode(Node):
    def __init__(self):
        super().__init__('speaker_node')

        self.subscription = self.create_subscription(
            String,
            'speaker_topic',
            self.speak_callback,
            10
        )

        self.url = 'http://host.docker.internal:5000/speak'

        self.data = {'text': ''}

        self.get_logger().info('Started speaker node')

    def speak_callback(self, msg):
        text = msg.data
        self.get_logger().info(f'Message received: {text}')
        self.data = text

        try:
            response = requests.post(self.url, json=self.data)
            self.get_logger().info("Message delivered to speakers.")

        except HTTPError as e:
            self.get_logger().error("Message could not be delivered to speakers.")

        except Timeout:
            self.get_logger().error("Timeout waiting for speaker server")

        except ConnectionError:
            self.get_logger().error("Speaker server not available")


def main(args=None):
    rclpy.init(args=args)
    node = SpeakerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
