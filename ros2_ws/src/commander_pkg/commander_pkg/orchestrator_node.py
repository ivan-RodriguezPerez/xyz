import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import random

from commander_pkg.utils.scripts import load_waypoints, compose_result_msg, compose_overall_score
from commander_pkg.utils.config import NAVIGATION_TYPE

from nav2_simple_commander.robot_navigator import BasicNavigator

from geometry_msgs.msg import PoseStamped
import time


class OrchestratorNode(Node):
    def __init__(self):
        super().__init__('orchestrator_node')

        self.publisher_speaker = self.create_publisher(
            String,
            'speaker_topic',
            10
        )

        self.publisher_listener = self.create_publisher(
            String,
            'listener_topic',
            10
        )

        self.publisher_llm = self.create_publisher(
            String,
            'input_request',
            10
        )

        self.subscription_audio = self.create_subscription(
            String,
            'audio_input',
            self.audio_callback,
            10
        )
        self.most_recent_instruction = None

        self.navigator = BasicNavigator()

        waypoints_path = "./src/commander_pkg/commander_pkg/utils/waypoints.yaml"
        self.waypoints = load_waypoints(waypoints_path)

        if NAVIGATION_TYPE == 'random':
            random.shuffle(self.waypoints)

        self.get_logger().info("Successfully created commander node")
        time.sleep(1)

    def audio_callback(self, msg):
        """
        """

        text = msg.data
        self.get_logger().info(f'Audio message received: {text}')

        self.most_recent_instruction = text

    def speak(self, msg_data):
        """
        Function used to compose a message to be published. The function wraps the charcter string
        string into a String interface according to the topic specifications.

        Args:
            msg_data (str): message to be published.

        """

        msg = String()
        msg.data = msg_data
        self.publisher_speaker.publish(msg)

    def record_audio(self):
        """
        
        """
        transcription = "Continua navegando"

        self.speak(transcription)

        return transcription
    
    def think(self, transcription):
        """
        """
        llm_prompt = f"""
        You are a robot assistant. You are working in a robotic environment and your mission is to determine
        to correct tool to continue or stop a navigation simulation accross points. You are receiving a specific
        transcription from the user and you must convert the user message into an action using the tools you have
        been provided. The message from user is: {transcription}. According to this user input you must answer
        "continue" or "stop".
        """

        llm_msg = String()
        llm_msg.data = llm_prompt
        self.publisher_llm.publish(llm_msg)

        time.sleep(20)

    def navigate_to_point(self, point):
        """
        Function used to send a command to the robot using a set of coordinates and orientation.

        Args:
            point (list): cartersian coordiantes of the goal point and orientation of the robot
                at the final position in format [X, Y, W]

        Reurns:
            result (enum.EnumMeta): whether the navigation action was successful or not.

        """

        x, y, w = point

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = w

        # Notify message
        point_msg = f"x: {x}, y: {y}, w: {w}"
        self.speak(f"Moving robot to point {point_msg}")

        self.navigator.goToPose(goal_pose)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f"Distancia restante al objetivo: {feedback.distance_remaining}")
            time.sleep(1)

        result = self.navigator.getResult()

        result_msg = compose_result_msg(result, point_msg)
        self.speak(result_msg)

        return result

    def navigation_for(self, waypoints):
        """
        Execute navigation towards a sequence of points.

        Args:
            navigator
            waypoints

        Returns:
            overall_score

        """

        results = {}

        self.speak("Iniciando una navegación de varios puntos.")

        for idx, point in enumerate(waypoints):

            # 1. Contextualiza - Speak
            x, y, w = point
            self.speak(f"The robot is going to navigate to point x: {x}, y: {y}, w: {w}. Do you want to continue?")

            # 2. Receive instructions - Record audio
            transcription = self.record_audio()

            # 3. Think
            #self.think(transcription)
            
            # 4. Act
            result = self.navigate_to_point(point)

            # Cambiar de planificador local
            # Si resultoado is not SUCCEDED -> Change scheduler
            # Otherwise use default planner
            if idx > 2:
                pass


        msg = String()
        msg.data = "The navigation through all waypoints has finished."
        self.publisher_speaker.publish(msg)

        overall_score = round(100*compose_overall_score(results), 3)
        
        msg = String()
        msg.data = f"The robot reached {overall_score}% of the defined waypoints."
        self.publisher_speaker.publish(msg)

        return overall_score

    def run(self):

        if NAVIGATION_TYPE == 'simple':
            self.get_logger().info("NAVIGATION SINGLE POINT")
            point = self.waypoints[0]
            result = self.navigate_to_point(point)
            print(f"Navigation result: {result}")

        elif NAVIGATION_TYPE == 'seq':
            self.get_logger().info("NAVIGATION SINGLE POINT")
            score = self.navigation_for(self.waypoints)
            print(f"Navigation succeed in {score}")

        elif NAVIGATION_TYPE == 'interactive':
            pass

        else:
            pass


def main(args=None):

    rclpy.init(args=args)

    node = OrchestratorNode()

    result = node.run()

    node.get_logger().info("Navigation finished.\n")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
