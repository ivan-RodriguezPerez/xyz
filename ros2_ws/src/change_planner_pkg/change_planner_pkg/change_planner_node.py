import rclpy
from rclpy.node import Node
from rcl_itnerfaces.srv import SetParameters
from rcl_interfaces.msg import Parameter, ParameterType, ParameterValue


class ChangePlanner(Node):

    def __init__(self):

        super().__init__("change_planner_client")
        self.cli = self.create_client(SetParameters, '/planner_server/set_parameters')

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for service set_parameters to be available...")

    def set_planner(self, planner_name):
        req = SetParameters.Request()

        # Define new planner parameter
        param = Parameter()
        param.name = "planner_id"
        param.value = ParameterValue(type=ParameterType.PARAMETER_STRING, string_value=planner_name)

        # Add parameter to request
        req.parameters = [param]

        # Call service for changing planner
        future = self.cli.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            self.get_logger().info(f"Planner changed to {planner_name}")
        else:
            self.get_logger().error(f"Error changing planner")


def main(args=None):

    rclpy.init(args=args)
    change_planneer_client = ChangePlanner()
    change_planneer_client.set_planner("GridBased")
    change_planneer_client.set_planner("SmacPlanner")

    change_planneer_client.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
