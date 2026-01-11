import rclpy
from rclpy import Node
from std_msgs.msg import String
import requests


class ListenerNode(Node):
    def __init__(self):
        super().__init__('listener_node')

        self.subscription = self.create_subscription(
            String,
            'listener_topic',
            self.listen_callback,
            10
        )

        self.publisher = self.create_publisher(
            String,
            'audio_input',
            10
        )

        self.url = 'http://host.docker.internal:5000/listen'

        self.data = {'text': ''}

        self.get_logger().info('Started listener node')

    def listen_callback(self, msg):
        text = msg.data
        self.get_logger().info(f'Listening to a new instruction...')
        self.data = text

        # Building transcription message
        response = requests.post(self.url, json=self.data)
        msg = String()
        msg.data = response
        self.publisher.publish(msg)

        self.get_logger().info(f'Published in listener topic:\n  {response}')


def main(args=None):
    rclpy.init(args=args)
    node = ListenerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
