from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from geometry_msgs.msg import PoseStamped
import rclpy
import time
import yaml


def load_waypoints(filename: str = 'waypoints.yaml') -> dict:
    """
    Load waypoints file containing the points the robot must explore to perform the
    navigation task. Points are composed of x, y and theta coordinates todefine the
    position and orientation the robot must reach durint navigation.

    Args:
        - filename (str): name of the yaml file containing the waypoints.

    Returns:
        dict: navigation points contained in the yaml file.
    """

    with open(filename, 'r') as f:
        loaded_data = yaml.safe_load(f)

    print(f"Data read from {filename}")
    print(loaded_data)

    return loaded_data


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

    for idx, point in waypoints.items():
        x_ = point[0]
        y_ = point[1]
        w_ = point[2]

        result = navigation_simple(navigator, x_, y_, w_)

        results[idx] = result

def main():

    NAVIGATION_TYPE = 'for'
    # Load waypoints
    waypoints = load_waypoints()

    # Init ROS2 nd navigator
    rclpy.init()
    navigator = BasicNavigator()

    if NAVIGATION_TYPE == 'simple':
        x_ = waypoints[0][0]
        y_ = waypoints[0][1]
        w_ = waypoints[0][2]

        result = navigation_simple(navigator, x_, y_, w_)

    elif NAVIGATION_TYPE == 'for':
        result = navigation_for(navigator)

    else:
        result = False

    if result == TaskResult.SUCCEEDED:
        print("El robot alcanzo el objetivo")
    elif result == TaskResult.CANCELED:
        print("La navegacion fue cancelada.")
    else:
        print("La navegacion fallo.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()
