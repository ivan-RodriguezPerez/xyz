import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle, GoalStatus
from rclpy.executors import MultiThreadedExecutor

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue

from interfaces_pkg.action import RecordAudio

from std_msgs.msg import String

from commander_pkg.utils.scripts import load_waypoints, compose_result_msg, compose_overall_score
from commander_pkg.utils.config import NAVIGATION_TYPE

from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

from geometry_msgs.msg import PoseStamped

import threading
import time
import random
from threading import Event


class OrchestratorNode(Node):
    def __init__(self):
        super().__init__('orchestrator_node')

        self.publisher_speaker = self.create_publisher(
            String,
            'speaker_topic',
            10
        )

        self.record_audio_client_ = ActionClient(
            self,
            RecordAudio,
            "listen_audio"
        )
        self.transcription = ""
        self._result_event = Event()

        self.publisher_llm = self.create_publisher(
            String,
            'input_request',
            10
        )

        # Change Planner client
        self.planner_name = "Navfn"
        self.all_planners = ["GridBased", "Navfn", "Smac2D", ]

        self.cli = self.create_client(SetParameters, '/planner_server/set_parameters')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando a que el servicio de set_parameters este disponible...')

        self.navigator = BasicNavigator()

        waypoints_path = "./src/commander_pkg/commander_pkg/utils/waypoints.yaml"
        self.waypoints = load_waypoints(waypoints_path)

        if NAVIGATION_TYPE == 'random':
            random.shuffle(self.waypoints)

        self.get_logger().info("Successfully created commander node")
        time.sleep(1)

    def speak(self, msg_data, sleep_time=5):
        """
        Function used to compose a message to be published. The function wraps the charcter string
        string into a String interface according to the topic specifications.

        Args:
            msg_data (str): message to be published.

        """

        msg = String()
        msg.data = msg_data
        self.publisher_speaker.publish(msg)
        time.sleep(sleep_time)

    def record_audio(self):
        """
        
        """

        self.record_audio_client_.wait_for_server()
        self._result_event.clear()

        # Compose goal
        goal = RecordAudio.Goal()
        goal.goal_record_seconds = 5

        self.record_audio_client_.send_goal_async(
            goal
        ).add_done_callback(self.goal_response_callback)

        self._result_event.wait()

        return self.transcription
    
    def goal_response_callback(self, future):
        self.goal_handle_: ClientGoalHandle = future.result()

        if self.goal_handle_.accepted:
            self.get_logger().info("Goal got accepted")
            self.goal_handle_.get_result_async().add_done_callback(
                self.goal_result_callback
            )
        else:
            self.get_logger().info("Goal rejected")

    def goal_result_callback(self, future):

        status = future.result().status
        result = future.result().result

        if status == GoalStatus.STATUS_SUCCEEDED:
            self.get_logger().info("Success")
            self.transcription = result.transcription
            self.get_logger().info(f"Transcription received: {self.transcription}")

        elif status == GoalStatus.STATUS_ABORTED:
            self.get_logger().error("Aborted")
            self.transcription = "Aborted"

        elif status == GoalStatus.STATUS_CANCELED:
            self.get_logger().warn("Cancelled")
            self.transcription = "Cancelled"
        else:
            self.transcription = None
        
        self._result_event.set()

    
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

    def think_manual(self, transcription):

        # Actions
        continuar_words = ["continua", "continue", "sigue", "Continúa", "ontin"]
        go_back_words = ["previo", "anterior", "vuelve"]
        stop_words = ["stop", "para", "detén", "deten", "Stop", "Para", "Detén", "Deten"]
        change_planner_words = ["planner", "planer", "cambia", "cambio", "Cambia", "Cambio", "planif"]

        check_action = lambda list_words: any(map(transcription.__contains__, list_words))

        # 1. Continue
        if check_action(continuar_words):
            action = "continuar"
        # 2. Go to previous point
        elif check_action(go_back_words):
            action = "go_back"
        # 3. Stop navigation
        elif check_action(stop_words):
            action = "stop"
        # 4. Change planner
        elif check_action(change_planner_words):
            action = "change planner"
        else:
            action = "continue"

        return action

    def act(self, action, point, prev_point):

        if action == "continuar":
            result = self.navigate_to_point(point)

        elif action == "go_back":
            result = self.navigate_to_point(prev_point)

        elif action == "stop":
            _ = self.stop_navigation()
            result = self.navigate_to_point(point)

        elif action == "change planner":
            _ = self.change_planner()
            result = self.navigate_to_point(point)

        elif action == "change controller":
            _ = self.change_controller()
            result = self.navigate_to_point(point)

        elif action == "turn around":
            turn_point = [prev_point[0], prev_point[1], prev_point[2] - 3.1415]
            self.get_logger().info(f"Turn point: {turn_point}")

            _ = self.change_planner()
            result = self.navigate_to_point(turn_point)

        else:
            result = self.navigate_to_point(point)

        return result

    def navigate_to_point(self, point, timeout_sec=20):
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
        self.speak(f"Moving to point {point_msg}")

        self.navigator.goToPose(goal_pose)

        t0 = time.time()

        while not self.navigator.isTaskComplete():
            feedback = self.navigator.getFeedback()

            dt = time.time() - t0

            if feedback:
                self.get_logger().info(f"Remaining distance: {round(feedback.distance_remaining, 2)} | Timeout: {round(timeout_sec - dt, 2)}")

            time.sleep(1)

            if dt > timeout_sec:
                self.navigator.cancelTask()
                break

        result = self.navigator.getResult()
        self.get_logger().info(f"Navigation result: {result}")

        result_msg = compose_result_msg(result, point_msg)
        self.speak(result_msg)

        return self.navigator.getResult() == TaskResult.SUCCEEDED

    
    def stop_navigation(self):
        self.speak("Stopping navigation")

    def change_planner(self):
        
        prev_planner = self.planner_name
        self.planner_policy()

        self.speak(f"Changing planner from {prev_planner} to {self.planner_name}")

        req = SetParameters.Request()

        # Define new planner parameter
        param = Parameter()
        param.name = "planner_id"
        param.value = ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=self.planner_name)

        # Add parameter to request
        req.parameters = [param]

        # Call service for changing planner
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            self.get_logger().info(f"Planner changed to {self.planner_name}")

        else:
            self.get_logger().error(f"Error changing planner")

    def planner_policy(self):
        """
        Change planner randomly
        """

        new_planner = self.planner_name

        while new_planner == self.planner_name:
            new_planner = random.sample(self.all_planners, 1)[0]
            
        self.planner_name = new_planner

    def change_controller(self):
        self.speak("Changing controller")

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

        self.speak("Starting navigation.")

        prev_point = [0, 0, 0]

        for idx, point in enumerate(waypoints):

            # 1. Contextualiza - Speak
            #x, y, w = point
            self.speak(f"Going to a new scheduled point. Do you want to continue?", 6)

            if False:
                # 2. Receive instructions - Record audio
                transcription = self.record_audio()
                self.speak(transcription)

                # 3. Think
                #self.think(transcription)
                action = self.think_manual(transcription)
            action = "change planner"
            self.speak(f"Acción elegida: {action}")

            # 4. Act
            act_result = self.act(action, point, prev_point)

            # 5. Check success
            if not act_result:
                self.act("turn around", point, prev_point)
                act_result = self.act(action, point, prev_point)

            prev_point = point

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

    executor = MultiThreadedExecutor()
    executor.add_node(node)

    threading.Thread(target=node.run, daemon=True).start()

    executor.spin()

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
