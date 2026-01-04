import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import random

from commander_pkg.utils.scripts import load_waypoints, compose_result_msg, compose_overall_score
from commander_pkg.utils.config import NAVIGATION_TYPE

from nav2_simple_commander.robot_navigator import BasicNavigator

from geometry_msgs.msg import PoseStamped
import time


class CommanderNode(Node):
    def __init__(self):
        super().__init__('commander_node')

        self.publisher = self.create_publisher(
            String,
            'speaker_topic',
            10
        )

        self.navigator = BasicNavigator()

        waypoints_path = "./src/commander_pkg/commander_pkg/utils/waypoints.yaml"
        self.waypoints = load_waypoints(waypoints_path)

        if NAVIGATION_TYPE == 'random':
            random.shuffle(self.waypoints)
        self.get_logger().info("Successfully created commander node")
        time.sleep(3)

    def publish_message(self, msg_data):
        """
        """

        msg = String()
        msg.data = msg_data
        self.publisher.publish(msg)

    def navigate_to_point(self, x, y, w):
        """
        Function used to send a command to the robot using a set of coordinates and orientation.

        Args:
            navigator ():
            x (float): X coordinate of the goal point.
            y (float): Y coordinate of the goal point.
            w (float): orientation of the robot at the goal point.

        Reurns:
            result (enum.EnumMeta): whether the navigation action was successful or not.

        """

        goal_pose = PoseStamped()
        goal_pose.header.frame_id = 'map'
        goal_pose.pose.position.x = x
        goal_pose.pose.position.y = y
        goal_pose.pose.orientation.w = w

        # Notify message
        point_msg = f"x: {x}, y: {y}, w: {w}"
        msg = f"Moving robot to point {point_msg}"
        self.publish_message(msg)

        self.navigator.goToPose(goal_pose)

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()
            if feedback:
                self.get_logger().info(f"Distancia restante al objetivo: {feedback.distance_remaining}")
            time.sleep(1)

        result = self.navigator.getResult()

        result_msg = compose_result_msg(result, point_msg)
        self.publish_message(result_msg)

        return result

    def navigation_for(self, navigator, waypoints, node):
        """
        Execute navigation towards a sequence of points.

        Args:
            navigator
            waypoints

        Returns:
            overall_score

        """

        results = {}

        msg = "Iniciando una navegación de varios puntos."
        self.publish_message(msg)

        for idx, point in enumerate(waypoints):
            x_ = point[0]
            y_ = point[1]
            w_ = point[2]

            result = self.navigate_to_point(navigator, x_, y_, w_, node)

            results[idx] = result

        msg = "La navegación de varios puntos ha finalizado."
        self.publish_message(msg)

        overall_score = round(100*compose_overall_score(results), 3)
        
        msg = f"Se han alcanzado un {overall_score} % de los puntos definidos."
        self.publish_message(msg)

        return overall_score

    def run(self):

        if NAVIGATION_TYPE == 'simple':
            self.get_logger().info("NAVIGATION SINGLE POINT")
            x_, y_, w_ = self.waypoints[0]

            result = self.navigation_simple(self.navigator, x_, y_, w_, self)
            print(f"Navigation result: {result}")

        elif NAVIGATION_TYPE == 'for':
            self.get_logger().info("NAVIGATION SINGLE POINT")
            score = self.navigation_for(self.navigator, self.waypoints, self)
            print(f"Navigation succeed in {score}")

        elif NAVIGATION_TYPE == 'interactive':
            pass

        else:
            pass


def main(args=None):

    rclpy.init(args=args)

    node = CommanderNode()

    result = node.run()

    node.get_logger().info(f"Navigation finished with result: {result}")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
