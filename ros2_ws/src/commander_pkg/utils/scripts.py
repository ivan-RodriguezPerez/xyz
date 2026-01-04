import yaml
from nav2_simple_commander.robot_navigator import TaskResult


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


def compose_result_msg(result, point_msg):
    """
    Convert the result of a specific navigation order into a usser message.

    Args:
        result (enum.EnumMeta): whether the navigation action was successful or not.

    Returns:
        msg (str): usser message.

    """

    if result == TaskResult.SUCCEEDED:
        msg = f"El robot alcanzo el objetivo {point_msg}"
    elif result == TaskResult.CANCELED:
        msg = f"La navegacion fue cancelada. El robot no pudo alcanzar el objetivo {point_msg}"
    else:
        msg = f"La navegacion fallo. El robot no pudo alcanzar el objetivo {point_msg}"

    return msg


def compose_overall_score(results):
    """
    Function used to compute an score showing the success rate of navigation. For that
    the ratio between reached points over all initially defined points is computed.

    Args:
        results (list): results from all navigation orders.
    
    Returns:
        overall_score (float): success ratio of navigation plan.

    """

    total_points = len(results)
    succeded_points = len([r for r in results.values if r == TaskResult.SUCCEEDED])

    overall_score = succeded_points / total_points

    return overall_score