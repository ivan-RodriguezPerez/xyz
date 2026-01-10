import threading

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

from flask import Flask, request, jsonify


# Microservice
app = Flask(__name__)
ros_node = None


@app.route('/')
def index():
    return 'ROS2 Flask Bridge OK'

@app.route('/listen_ros2', methods=['POST'])
def listen_ros2():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    ros_node.publish_text(text)
    return jsonify({'status': 'published'})
    
# ROS2 Node
class ListenerNode(Node):
    def __init__(self):

        super().__init__('listener_node')

        self.publisher = self.create_publisher(
            String,
            'input_request',
            10
        )

    def publish_input_request(self, input_request):
        msg = String()
        msg.data = input_request
        self.publisher.publish(msg)
        self.get_logger().info(f"Published: {input_request}")


def start_flask():
    app.run(
        host='0.0.0.0',
        port=5002,
        debug=False,
        use_reloader=False
    )

def main(args=None):

    global ros_node

    rclpy.init(args=args)
    node = ListenerNode()

    flask_thread = threading.Thread(
        target=start_flask,
        daemon=True
    )
    # Launch both loops
    flask_thread.start()
    rclpy.spin(node)

    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()
