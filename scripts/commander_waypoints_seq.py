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


def main():
    # Inicializa el sistema ROS 2
    rclpy.init()

    navigator = BasicNavigator()

    goal_pose = PoseStamped()
    goal_pose.header.frame_id = 'map'
    goal_pose.pose.position.x = 1.0
    goal_pose.pose.position.y = 1.0
    goal_pose.pose.orientation.w = 1.0

    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            print("Distancia restante al objetivo: ", feedback.distance_remaining)
        time.sleep(1)


    result = navigator.getResult()
    if result == TaskResult.SUCCEEDED:
        print("El robot alcanzo el objetivo")
    elif result == TaskResult.CANCELED:
        print("La navegacion fue cancelada.")
    else:
        print("La navegacion fallo.")

    rclpy.shutdown()

if __name__ == '__main__':
    main()
