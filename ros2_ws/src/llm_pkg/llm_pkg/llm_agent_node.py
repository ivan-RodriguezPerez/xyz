import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import ollama
from llm_pkg.tools.tools_script import *


class OllamaAgent(Node):
    """
    ros2 topic pub /speaker_topic std_msgs/String "data: Hello LLM. we are going to work together!" --once
    """

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
            }],
            tools=tools,
        )

        res = ""

        print("response: ", response)

        if ('message' in response and
            'tool_calls' in response['message'] and
            len(response['message']['tool_calls']) > 0 and
            'function' in response['message']['tool_calls'][0] and
            'name' in response['message']['tool_calls'][0]['function'] and
            'arguments' in response['message']['tool_calls'][0]['function']):
            
            # Parse tool name and arguments
            tools_calls = response['message']['tool_calls']
            tool_name = tools_calls[0]['function']['name']
            arguments = tools_calls[0]['function']['arguments']
            
                
            if( tool_name == "get_current_weather"):
                temperature = get_current_weather(arguments["city"])
                res = "The temperature in " + arguments["city"] + " is about " + temperature
            elif( tool_name == "do_math"):
                result = do_math( int(arguments['x']), arguments['op'], int(arguments['y']) )
                res = "The result of the requested operation is: " + result

        else:
            res = generic_chat()

        output = String()
        output.data = res

        self.response_pub.publish(output)

        self.get_logger().info(f"LLM answers:\n  {response}")
    

def main(args=None):

    rclpy.init(args=args)
    node = OllamaAgent()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
