import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import ollama


class OllamaChat(Node):

    def __init__(self):
        super().__init__('ollama_chat')

        self.request_sub = self.create_subscription(
            String,
            'input_request',
            self.request_callback,
            10
        )

        self.response_pub = self.create_publisher(
            String,
            'speaker_topic',
            10
        )

        self.get_logger().info(f"Ollama chat node is running!")

    def request_callback(self, msg):

        self.get_logger().info(f"Received request: {msg.data}")

        response = ollama.chat(
            model='llama3.2',
            messages=[{
                'role': 'user',
                'content': msg.data,
            }]
        )

        self.get_logger().info(f"LLM answers:\n  {response}")

        output = String()
        output.data = response['message']['content']

        self.response_pub.publish(output)


def main(args=None):

    rclpy.init(args=args)
    node = OllamaChat()
    rclpy.spin(node)

if __name__ == '__main__':
    main()
