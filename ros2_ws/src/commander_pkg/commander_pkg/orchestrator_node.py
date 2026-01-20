import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle, GoalStatus
from rclpy.executors import MultiThreadedExecutor

from rcl_interfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue

from interfaces_pkg.action import RecordAudio
from interfaces_pkg.msg import NavigationStatus

from std_msgs.msg import String


from commander_pkg.utils.scripts import load_waypoints, compose_result_msg, compose_overall_score, get_navigation_result
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

        self.publisher_status = self.create_publisher(
            NavigationStatus,
            'displayer_topic',
            10,
        )

        # Change Planner client
        self.planner_name = "Navfn"
        self.all_planners = ["GridBased", "Navfn", "Smac2D", ]

        self.planner_cli = self.create_client(SetParameters, '/planner_server/set_parameters')
        while not self.planner_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando a que el servicio de planner_server/set_parameters este disponible...')

        # Change Controller client
        self.controller_name = "FollowPath"
        self.all_controllers = ["FollowPath", "MPPIController", "RPPC"]  # ["DWB", "TEB", "RPP"]

        self.controller_cli = self.create_client(SetParameters, '/controller_server/set_parameters')
        while not self.controller_cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Esperando a que el servicio de controller_server/set_parameters este disponible...')

        self.navigator = BasicNavigator()

        waypoints_path = "./src/commander_pkg/commander_pkg/utils/waypoints.yaml"
        self.waypoints = load_waypoints(waypoints_path)

        if NAVIGATION_TYPE == 'random':
            random.shuffle(self.waypoints)

        self.timeout_nav = 90  # [s]
        self.static_strategy = "CONTROLLER"

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
        "continue", "go back", "stop", "change planner", "change controller", or "turn around".

        """

        llm_msg = String()
        llm_msg.data = llm_prompt
        self.publisher_llm.publish(llm_msg)

        time.sleep(20)

    def think_manual(self, transcription):

        # Actions
        continue_words = ["continua", "continue", "sigue", "Continúa", "ontin"]
        go_back_words = ["previo", "anterior", "vuelve"]
        stop_words = ["stop", "para", "detén", "deten", "Stop", "Para", "Detén", "Deten"]
        change_planner_words = ["planner", "planer", "planif"]
        change_controller_words = ["control", "controlador", "controller", "contro"]

        check_action = lambda list_words: any(map(transcription.__contains__, list_words))

        # 1. Continue
        if check_action(continue_words):
            action = "continue"
        # 2. Go to previous point
        elif check_action(go_back_words):
            action = "go back"
        # 3. Stop navigation
        elif check_action(stop_words):
            action = "stop"
        # 4. Change planner
        elif check_action(change_planner_words):
            action = "change planner"
        # 5. Change controller
        elif check_action(change_controller_words):
            action = "change controller"
        else:
            action = "continue"

        return action

    def act(self, action, point, prev_point, planner=None, controller=None):

        if action == "continue":
            result = self.navigate_to_point(point)

        elif action == "go back":
            result = self.navigate_to_point(prev_point)

        elif action == "stop":
            self.speak("Stopping navigation")
            result = "STOP"

        elif action == "change planner":
            _ = self.change_planner(planner)
            result = self.navigate_to_point(point)

        elif action == "change controller":
            _ = self.change_controller(controller)
            result = self.navigate_to_point(point)

        elif action == "turn around":
            # Turn around in the same x and y coordinates
            turn_point = [prev_point[0], prev_point[1], float(round(prev_point[2] - 3.1415, 2))]
            self.get_logger().info(f"Turn point: {turn_point}")
            _ = self.navigate_to_point(turn_point)

            # Try again
            _ = self.change_planner()
            self.get_logger().info(f"Navigating again to: {point}")
            result = self.navigate_to_point(point)

        else:
            result = self.navigate_to_point(point)

        return result

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

        point_msg = f"x: {x}, y: {y}, w: {w}"
        self.speak(f"Moving to point {point_msg}")

        self.navigator.goToPose(goal_pose)

        timeout_state = False

        initial_distance = 0.0
        feedback = False

        t0 = time.time()
        elapsed_dt = 5.0

        while not self.navigator.isTaskComplete():

            try:
                feedback = self.navigator.getFeedback()
                distance_remaining = feedback.distance_remaining
            except:
                distance_remaining = initial_distance

            dt = time.time() - t0

            # Update initial distance
            if (initial_distance == 0.0) and (dt > elapsed_dt):
                initial_distance = distance_remaining

            # Timeout
            if dt > self.timeout_nav:
                self.navigator.cancelTask()
                timeout_state = True
                break

            timeout_time_ = max(round(self.timeout_nav - dt, 2), 0.0)

            msg_status = NavigationStatus()
            if feedback:
                msg_status.distance_remaining = round(distance_remaining, 2)
                msg_status.timeout_time = timeout_time_
            else:
                msg_status.distance_remaining = -99.99
                msg_status.timeout_time = -99.99

            self.publisher_status.publish(msg_status)

            time.sleep(1)

        final_distance = feedback.distance_remaining if feedback else initial_distance

        # Static
        min_distance = 0.3
        static_state = abs(final_distance - initial_distance) <= min_distance

        result = get_navigation_result(self.navigator.getResult(), static_state, timeout_state)

        self.get_logger().info(f"Navigation result: {result}")

        result_msg = compose_result_msg(result, point_msg)
        self.speak(result_msg)

        return result

    def change_planner(self, planner=None):

        prev_planner = self.planner_name

        if planner:
            new_planner = planner
        else:
            self.planner_policy()
            new_planner = self.planner_name

        if new_planner != prev_planner:
            self.speak(f"Changing planner from {prev_planner} to {self.planner_name}")

            req = SetParameters.Request()

            # Define new planner parameter
            param = Parameter()
            param.name = "planner_id"
            param.value = ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=self.planner_name)

            # Add parameter to request
            req.parameters = [param]

            # Call service for changing planner
            future = self.planner_cli.call_async(req)
            rclpy.spin_until_future_complete(self, future)

            if future.result() is not None:
                self.get_logger().info(f"Planner changed to {self.planner_name}")

            else:
                self.get_logger().error(f"Error changing planner")

    def change_controller(self, controller=None):

        prev_controller = self.controller_name

        if controller:
            new_controller = controller
        else:
            self.controller_policy()
            new_controller = self.controller_name

        if new_controller != prev_controller:
            self.speak(f"Changing controller from {prev_controller} to {self.controller_name}")

            req = SetParameters.Request()

            # Define new planner parameter
            param = Parameter()
            param.name = "controller_id"
            param.value = ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=self.controller_name)

            # Add parameter to request
            req.parameters = [param]

            # Call service for changing planner
            future = self.controller_cli.call_async(req)
            rclpy.spin_until_future_complete(self, future)

            if future.result() is not None:
                self.get_logger().info(f"Controller changed to {self.controller_name}")

            else:
                self.get_logger().error(f"Error changing controller")

    def planner_policy(self):
        """
        Change planner randomly
        """

        new_planner = self.planner_name

        while new_planner == self.planner_name:
            new_planner = random.sample(self.all_planners, 1)[0]

        self.planner_name = new_planner

    def controller_policy(self):
        """
        Change controller randomly
        """

        new_controller = self.controller_name

        while new_controller == self.controller_name:
            new_controller = random.sample(self.all_controllers, 1)[0]

        self.controller_name = new_controller

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
        
        prev_point = [-1.0, -0.45, -3.72]

        for idx, point in enumerate(waypoints):

            # 1. Contextualiza - Speak
            self.speak(f"Going to a new scheduled point. Do you want to continue?", 6)

            # 2. Receive instructions - Record audio
            transcription = self.record_audio()
            self.speak(transcription)

            # 3. Think
            #self.think(transcription)
            action = self.think_manual(transcription)
            self.speak(f"Acción elegida: {action}")

            # 4. Act
            result = self.act(action, point, prev_point)

            # 5. Check action result
            if result == "STOP":
                break

            elif result == "STATIC":
                if self.static_strategy == "PLANNER":
                    result = self.act("turn around", point, prev_point, planner="Navfn")
                elif self.static_strategy == "CONTROLLER":
                    result = self.act("change controller", point, prev_point, controller="MPPIController")
                else:
                    result = self.act("turn around", point, prev_point, planner="Navfn")
                    result = self.act("change controller", point, prev_point, controller="MPPIController")


            elif result == "TIMEOUT":
                msg = String()
                msg.data = "The navigation failed by timeout. Trying again."
                self.publisher_speaker.publish(msg)

                self.timeout_nav = min(self.timeout_nav + 15, 120)
                result = self.act("continue", point, prev_point)
                

            prev_point = point

            results[idx] = result

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
