from __future__ import annotations

import os
import platform
import sys

import psutil


class SysServerService:
    def get_runtime(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "os": platform.platform(),
            "machineName": platform.node(),
            "pythonVersion": sys.version,
            "cpuCount": os.cpu_count(),
            "memoryTotal": mem.total,
            "memoryUsed": mem.used,
            "memoryAvailable": mem.available,
            "processId": os.getpid(),
            "startTime": psutil.Process(os.getpid()).create_time(),
            "threadCount": psutil.Process(os.getpid()).num_threads(),
        }

    def get_hardware(self) -> dict:
        cpu = psutil.cpu_times()
        mem = psutil.virtual_memory()
        disks = []
        for partition in psutil.disk_partitions(all=True):
            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except Exception:
                continue
            if usage.total <= 0:
                continue
            disks.append(
                {
                    "name": partition.mountpoint,
                    "fsType": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                }
            )
        return {
            "cpu": {
                "logicalCount": psutil.cpu_count(logical=True),
                "physicalCount": psutil.cpu_count(logical=False),
                "user": cpu.user,
                "system": cpu.system,
                "idle": cpu.idle,
            },
            "memory": {"total": mem.total, "used": mem.used, "free": mem.free, "percent": mem.percent},
            "disks": disks,
        }

    def get_assemblies(self) -> list[dict]:
        import importlib.metadata as metadata

        distributions = metadata.distributions()
        return [
            {"name": dist.metadata["Name"], "version": dist.version}
            for dist in distributions
            if dist.metadata["Name"]
        ][:200]

    def get_nodes(self) -> list[dict]:
        runtime = self.get_runtime()
        return [
            {
                "instanceId": "local",
                "nodeTag": None,
                "isSelf": True,
                "isAlive": True,
                "startedAt": runtime["startTime"],
                "lastBeat": runtime["startTime"],
                "os": runtime["os"],
                "cpuCount": runtime["cpuCount"],
                "memoryTotal": runtime["memoryTotal"],
            }
        ]
