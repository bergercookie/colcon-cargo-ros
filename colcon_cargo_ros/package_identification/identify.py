from collections.abc import MutableMapping
from typing import Optional, List, Any, Dict
from pathlib import Path

from colcon_core.logging import colcon_logger
from colcon_core.package_identification import PackageIdentificationExtensionPoint
from colcon_core.plugin_system import satisfies_version, SkipExtensionException
import toml

logger = colcon_logger.getChild(__name__)


class CargoRosPackageIdentification(PackageIdentificationExtensionPoint):
    """Identify Cargo packages with `Cargo.toml` files."""

    # the priority needs to be higher than the extensions identifying either pure rust packages
    # or non-rust CMake ROS2 packages
    PRIORITY = 160

    def __init__(self):
        super().__init__()
        satisfies_version(PackageIdentificationExtensionPoint.EXTENSION_POINT_VERSION, "^1.0")

        self.name = "cargo_ros"

    def identify(self, metadata):
        if metadata.type is not None and metadata.type != self.name:
            return

        # skip package if it contains a CMakeLists.txt file
        cmake_txt = metadata.path / "CMakeLists.txt"
        if cmake_txt.is_file():
            return

        # for it to be an ROS 2 rust package, there needs to be both a Cargo.toml and a
        # package.xml file
        cargo_toml = metadata.path / "Cargo.toml"
        if not cargo_toml.is_file():
            return
        package_xml = metadata.path / "package.xml"
        if not package_xml.is_file():
            return

        data = extract_data(cargo_toml)
        if not data:
            raise SkipExtensionException(
                'Failed to extract Rust package information from "%s"' % cargo_toml.absolute()
            )

        metadata.type = "cargo_ros"
        if metadata.name is None:
            metadata.name = data["name"]
        metadata.dependencies["build"] |= data["depends"]
        metadata.dependencies["run"] |= data["depends"]


def extract_data(cargo_toml: Path) -> Optional[Dict[str, Any]]:
    """
    Extract the project name and dependencies from a Cargo.toml file.

    :param cargo_toml: The path of the Cargo.toml file
    """
    content = {}
    try:
        content = toml.load(str(cargo_toml))
    except toml.TomlDecodeError:
        logger.error('Decoding error when processing "%s"' % cargo_toml.absolute())
        return

    # set the project name - fall back to use the directory name
    data = {}
    toml_name_attr = extract_project_name(content)
    data["name"] = toml_name_attr if toml_name_attr is not None else cargo_toml.parent.name

    depends = extract_dependencies(content)
    # exclude self references
    if depends:
        data["depends"] = set(depends) - {data["name"]}
    else:
        data["depends"] = set()

    return data


def extract_project_name(content: MutableMapping) -> Optional[str]:
    """
    Extract the Cargo project name from the Cargo.toml file.

    :param content: The Cargo.toml parsed dictionnary
    :returns: The project name, otherwise None
    """
    try:
        return content["package"]["name"]
    except KeyError:
        return None


def extract_dependencies(content: MutableMapping) -> Optional[List[str]]:
    """
    Extract the dependencies from the Cargo.toml file.

    :param content: The Cargo.toml parsed dictionnary
    :returns: Packages listed in the dependencies section
    """
    try:
        list(content["dependencies"].keys())
    except KeyError:
        return []
