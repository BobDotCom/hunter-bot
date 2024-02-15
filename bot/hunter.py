"""
hunter-bot - A discord bot for hunter written in pycord
Copyright (C) 2024  BobDotCom

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
import re

import docker
import docker.errors
from docker.models.containers import Container


__all__ = "scenario_dir", "available_scenarios", "Hunter", "HunterConfig"

from bot.error import InfoExc, ErrorExc
from bot.persistent_store import PersistentStore

scenario_dir = f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/hunter-scenarios"
available_scenarios = list(
    map(
        lambda scenario: scenario[9:-3],
        filter(lambda scenario: re.fullmatch(r"scenario_\w+\.py", scenario), os.listdir(scenario_dir))
    )
)


class HunterConfigError(InfoExc):
    def __init__(self, message, *args, **kwargs):
        super().__init__("Error when validating hunter configuration: " + message, *args, **kwargs)


class HunterRunningError(ErrorExc):
    pass


class HunterConfig:
    def __init__(
            self,
            scenario: str,
            gci: bool = False,
            hostility: str = "0_0_0_0_0",
            human_defenders: str = ""
    ):
        """
        Configuration for hunter container. It is safe to pass unsanitized input here as it is validated during init.
        See hunter docs for more info:
        https://vanosten.gitlab.io/hunter/installation_server.html#command-line-arguments-for-running-hunter
        """
        self.scenario = scenario
        self.gci = gci
        self.hostility = hostility
        self.human_defenders = human_defenders

        self._validate()

    @staticmethod
    def _validate_callsigns(value: str, variable_name: str = ""):
        variable_name = f"{variable_name} callsign".lstrip().capitalize()
        for i, callsign in enumerate(value.split("#")):
            if not re.fullmatch(r"\w{0,7}", callsign):
                raise HunterConfigError(
                    f"{variable_name} `{callsign}` at index {i} is invalid. (Original: `{value}`)"
                )

    def _validate(self):
        if self.scenario not in available_scenarios:
            raise HunterConfigError(f"Scenario `{self.scenario}` is not available")
        if not isinstance(self.gci, bool):
            raise HunterConfigError(f"GCI is not a boolean: `{self.gci}`")
        if not re.fullmatch(r"(?:\d_){4}\d", self.hostility):
            raise HunterConfigError(f"Hostility `{self.hostility}` is not valid")
        self._validate_callsigns(self.human_defenders, "Human defender")


class Hunter:
    def __init__(self, version: str):
        self.client = docker.from_env()
        self.version = version
        self.container_name = "hunter_bot_container"
        self.image_name = "vanosten/hunter_container"
        self.container: Container | None = None
        self.persistent_store = PersistentStore(os.environ["PERSISTENT_STORE_FILE"], ["config"])
        self._config: HunterConfig | None = self.persistent_store.config

        try:
            if self.client.containers.get(self.container_name):
                self.container = self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    @property
    def config(self) -> HunterConfig:
        return self.persistent_store.config

    @config.setter
    def config(self, conf: HunterConfig):
        self.persistent_store.config = conf

    @property
    def exists(self):
        if self.container is None:
            return False

        try:
            self.container.reload()
            return True
        except docker.errors.NotFound:
            pass

        return False

    @property
    def running(self):
        if not self.exists:
            return False

        return self.container.status == "running"

    def pull(self):
        # docker pull vanosten/hunter_container:1.12.0
        self.client.images.pull(self.image_name, tag=self.version)

    def run(self, config: HunterConfig):
        if self.running:
            raise HunterRunningError("Container already running")

        if self.exists:
            self.container.remove()

        self.container = self.client.containers.run(
            self.image_name,
            " ".join((
                "-i OPFOR",
                # "-c "  # MP Chat controller callsign
                f"-s {config.scenario}",
                "-d /hunter-scenarios",
                "-g" if config.gci else "",
                f"-o {config.hostility}",
                f"-y {config.human_defenders}" if config.human_defenders else ""
            )),
            # auto_remove=True,
            detach=True,
            name=self.container_name,
            # ports={"5001-5110": "5001-5110/udp"},
            publish_all_ports=True,
            volumes=[f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/hunter-scenarios:/hunter-scenarios"],
        )
        self.config = config

    def start(self):
        if self.running:
            raise HunterRunningError("Container already running")

        if not self.exists:
            raise HunterRunningError("Container does not exist yet")

        self.container.start()

    def restart(self):
        if not self.running:
            raise HunterRunningError("Container not running!")

        self.container.restart()

    def stop(self):
        if not self.running:
            raise HunterRunningError("Container not running")

        self.container.stop()

    def logs(self):
        if not self.exists:
            raise HunterRunningError("Container does not exist")

        return self.container.logs().decode("utf-8")
