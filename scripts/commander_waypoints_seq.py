from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import rclpy
import time
import yaml
import random

from config import NAVIGATION_TYPE


def load_waypoints(filename: str = 'waypoints.yaml') -> list:
    """
    Load waypoints file containing the points the robot must explore to perform the
    navigation task. Points are composed of x, y and theta coordinates todefine the
    position and orientation the robot must reach durint navigation.

    Args:
        - filename (str): name of the yaml file containing the waypoints.

    Returns:
        list: navigation points contained in the yaml file.
    """

    with open(filename, 'r') as f:
        loaded_data = yaml.safe_load(f)

    print(f"Data read from {filename}")
    print(loaded_data)
    
    waypoints = list(loaded_data.values())

    return waypoints


def check_result(result):
    """
    """
    if result == TaskResult.SUCCEEDED:
        msg = "El robot alcanzo el objetivo"
    elif result == TaskResult.CANCELED:
        msg = "La navegacion fue cancelada."
    else:
        msg = "La navegacion fallo."

    return msg


def compose_overall_score(results):
    """
    """

    total_points = len(results)
    succeded_points = len([r for r in results.values if r == TaskResult.SUCCEEDED])

    overall_score = succeded_points / total_points

    return overall_score


def navigation_simple(navigator, x, y, w):
    """
    """

    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.pose.position.x = x
    goal_pose.pose.position.y = y
    goal_pose.pose.orientation.w = w

    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print("Distancia restante al objetivo: ", feedback.distance_remaining)
        time.sleep(1)


    result = navigator.getResult()

    return result


def navigation_for(navigator, waypoints):
    """
    """

    results = {}

    for idx, point in enumerate(waypoints):
        x_ = point[0]
        y_ = point[1]
        w_ = point[2]

        print(f"Navigation to x: {x_}, y: {y_}, w: {w_}")
        result = navigation_simple(navigator, x_, y_, w_)

        msg = check_result(result)

        if result == TaskResult.SUCCEEDED:
            print(f"The robot reached the point [x: {x_}, y: {y_}, w: {w_}]")
        else:
            print(msg)

        results[idx] = result

    overall_score = round(100*compose_overall_score(results), 3)

    return overall_score

def main():

    # Load waypoints
    waypoints = load_waypoints()

    if NAVIGATION_TYPE == 'random':
        random.shuffle(waypoints)

    # Init ROS2 nd navigator
    rclpy.init()
    navigator = BasicNavigator()

    if NAVIGATION_TYPE == 'simple':
        x_ = waypoints[0][0]
        y_ = waypoints[0][1]
        w_ = waypoints[0][2]

        result = navigation_simple(navigator, x_, y_, w_)
        print(f"Navigation result: {result}")

    elif NAVIGATION_TYPE == 'for':
        score = navigation_for(navigator, waypoints)
        print(f"Navigation succeed in {score}")

    else:
        pass

    rclpy.shutdown()

if __name__ == '__main__':
    main()
