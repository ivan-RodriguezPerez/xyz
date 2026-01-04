from geometry_msgs.msg import PoseStamped
import time
from nav2_simple_commander.robot_navigator import TaskResult

from commander_pkg.utils.scripts import check_result, compose_overall_score


def navigate_to_point(navigator, x, y, w, node):
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
    msg = f"Moving robot to point {point_msgx}"
    node.publisher.publish(msg)

    navigator.goToPose(goal_pose)

    while not navigator.isTaskComplete():
        feedback = navigator.getFeedback()
        if feedback:
            node.get_logger().info(f"Distancia restante al objetivo: {feedback.distance_remaining}")
        time.sleep(1)

    result = navigator.getResult()

    result_msg = compose_result_msg(result, point_msg)
    node.publisher.publish(result_msg)

    return result


def navigation_for(navigator, waypoints, node):
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
    node.publish(msg)

    for idx, point in enumerate(waypoints):
        x_ = point[0]
        y_ = point[1]
        w_ = point[2]

        result = navigate_to_point(navigator, x_, y_, w_, node)

        results[idx] = result

    msg = "La navegación de varios puntos ha finalizado."
    node.publish(msg)

    overall_score = round(100*compose_overall_score(results), 3)
    
    msg = f"Se han alcanzado un {overall_score} % de los puntos definidos."
    node.publish(msg)

    return overall_score
