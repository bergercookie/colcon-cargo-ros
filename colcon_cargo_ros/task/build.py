import os
from pathlib import Path

from colcon_cargo.task.cargo import CARGO_EXECUTABLE
from colcon_cargo.task.cargo.build import CargoBuildTask
from colcon_core.environment import create_environment_scripts
from colcon_core.logging import colcon_logger
from colcon_core.plugin_system import satisfies_version
from colcon_core.shell import create_environment_hook, get_command_environment
from colcon_core.task import run

logger = colcon_logger.getChild(__name__)


class CargoRosBuildTask(CargoBuildTask):
    """Build ROS2 Cargo packages."""

    def __init__(self):
        super().__init__()

    def add_arguments(self, *, parser):
        pass

    async def _build(self, args, env):
        # TODO Let the user specify which libs to link against
        extra_flags = [
            f"-Lnative={Path.home()}/ros2_rust_ws/install/builtin_interfaces/lib",
            "-Lnative=/opt/ros/foxy/lib",
            f"-Lnative={Path.home()}/ros2_rust_ws/install/std_msgs/lib",
        ]

        deps = {
            "rclrs": {
                "path": f"{Path.home()}/ros_ws/install/rclrs/share/rclrs/rust",
            },
            "rclrs_common": {
                "path": f"{Path.home()}/ros_ws/install/rclrs_common/share/rclrs_common/rust",
            },
            "std_msgs": {
                "path": f"{Path.home()}/ros_ws/install/std_msgs/share/std_msgs/rust",
            },
        }

        return await super()._build(args, env, *extra_flags, deps=deps)
