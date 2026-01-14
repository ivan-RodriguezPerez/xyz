import rclpy
from rclpy.node import Node
from interfaces_pkg.srv import RecordAudio
from rclpy.executors import MultiThreadedExecutor

import requests


class ListenerNode(Node):
    def __init__(self):
        super().__init__('listener_node')

        self.listen_server_ = self.create_service(
            RecordAudio,
            "listen_audio",
            self.callback_record_audio
        )
        
        self.url = 'http://host.docker.internal:5000/listen'
        self.data = {'text': ''}

        self.get_logger().info("Successfully started Listener Node.")
    
    def callback_record_audio(
        self,
        request: RecordAudio.Request,
        response: RecordAudio.Response
    ):
        """
        Service callback that triggers audio recording on the host machine and
        returns the speech transcription.

        This callback sends a request to an external HTTP server running on the
        host system (Windows). The server records audio from the laptop microphone
        for the requested duration, performs speech-to-text transcription, and
        returns the resulting text to the ROS 2 client via this service response.

        Args:
            request (RecordAudio.Request):
                Service request containing the desired audio recording duration
                in seconds.
            response (RecordAudio.Response):
                Service response populated with the transcribed text obtained
                from the external recording server.

        Returns:
            RecordAudio.Response:
                The service response containing the speech transcription.
        """

        # Handle request
        record_seconds = request.record_seconds
        self.data["text"] = str(record_seconds)

        # Execute request
        self.get_logger().info("Sending request...")
        request_response = requests.post(self.url, json=self.data)
        self.get_logger().info("Response received from server")

        # Compose result
        response.transcription = request_response.text

        return response

def main(args=None):
    rclpy.init(args=args)
    node = ListenerNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    executor.spin()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
