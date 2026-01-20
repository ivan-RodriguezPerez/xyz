import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.executors import MultiThreadedExecutor

from interfaces_pkg.action import RecordAudio

import requests
from requests.exceptions import Timeout, ConnectionError


class ListenerNode(Node):
    def __init__(self):
        super().__init__('listener_node')

        self.listen_server_ = ActionServer(
            self,
            RecordAudio,
            "listen_audio",
            goal_callback=self.goal_callback,
            execute_callback=self.execute_callback
        )
        
        self.url = 'http://host.docker.internal:5000/listen'
        self.data = {'text': ''}

        self.get_logger().info("Successfully started Listener Node.")


    def goal_callback(self, goal_request: RecordAudio.Goal):

        self.get_logger().info(f"Received goal: {goal_request.goal_record_seconds}")
        self.get_logger().info("Accepting the goal.")
        
        return GoalResponse.ACCEPT

    def execute_callback(self, goal_handle: ServerGoalHandle):
        
        # Hadle action request
        record_seconds = goal_handle.request.goal_record_seconds
        self.data['text'] = str(record_seconds)

        # Execute request
        self.get_logger().info("Executing the goal")

        result = RecordAudio.Result()

        try:
            response = requests.post(self.url, json=self.data, timeout=90)

            response.raise_for_status()

            result.transcription = response.text
        
            goal_handle.succeed()
            self.get_logger().info("Transcription received successfully")

            return result

        except Timeout:
            self.get_logger().error("Timeout waiting for listener server")

            result.transcription = "Timeout"
            goal_handle.abort()
            return result

        except ConnectionError:
            self.get_logger().error("Listener server not available")

            result.transcription = "ServerNotAvailable"
            goal_handle.abort()
            return result


def main(args=None):
    rclpy.init(args=args)
    node = ListenerNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
