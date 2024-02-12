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

import docker
import docker.errors
from docker.models.containers import Container


class Hunter:
    def __init__(self, version: str):
        self.client = docker.from_env()
        self.version = version
        self.container_name = "hunter_bot_container"
        self.image_name = "vanosten/hunter_container"
        self.container: Container | None = None

        try:
            if self.client.containers.get(self.container_name):
                self.container = self.client.containers.get(self.container_name)
        except docker.errors.NotFound:
            pass

    @property
    def running(self):
        # Technically, this returns True if the container exists, not if its running
        if self.container is None:
            return False

        try:
            self.container.reload()
            return True  # return self.container.status == "running"
        except docker.errors.NotFound:
            pass

        return False

    def pull(self):
        # docker pull vanosten/hunter_container:1.12.0
        self.client.images.pull(self.image_name, tag=self.version)

    def start(self, scenario: str):
        if self.running:
            raise RuntimeError("Container already started")

        self.container = self.client.containers.run(
            self.image_name,
            f"-d /hunter-scenarios -s {scenario} -o 0_0_0_0_0",
            auto_remove=True,
            detach=True,
            name=self.container_name,
            # ports={"5001-5110": "5001-5110/udp"},
            publish_all_ports=True,
            volumes=[f"{os.path.dirname(os.path.dirname(os.path.realpath(__file__)))}/hunter-scenarios:/hunter-scenarios"],
        )

    def stop(self):
        if not self.running:
            raise RuntimeError("Container not started")

        self.container.stop()

    def logs(self):
        if not self.running:
            raise RuntimeError("Container not started")

        return self.container.logs().decode("utf-8")
