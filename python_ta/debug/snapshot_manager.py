from __future__ import annotations

import inspect
import os
import re
import sys
import types
from typing import Any, Iterable, Optional

from python_ta.debug.snapshot import snapshot


class SnapshotManager:
    """
    Class used to manage the snapshots taken during the execution of a program.

    Instance attributes:
        memory_viz_args: The arguments to pass to the MemoryViz CLI
        memory_viz_version: The version of MemoryViz to use
        include: A collection of function names, either as strings or regular expressions, whose variables will be captured
        output_directory: The path to save the snapshots
    """

    memory_viz_args: Optional[list[str]]
    memory_viz_version: str
    _snapshot_counts: int
    include: Optional[Iterable[str | re.Pattern]]
    output_directory: Optional[str]

    def __init__(
        self,
        memory_viz_args: Optional[list[str]] = None,
        memory_viz_version: str = "latest",
        include: Optional[Iterable[str | re.Pattern]] = None,
        output_directory: Optional[str] = None,
    ) -> None:
        """Initialize a SnapshotManager context manager for snapshot-based debugging.

        Args:
            memory_viz_args: The arguments to pass to the memory visualizer.
            memory_viz_version: The version of the memory visualizer to use
            include: A collection of function names, either as strings or regular expressions, whose variables will be captured
            output_directory: The path to save the snapshots. Use this argument instead of the `--output` flag to specify the output directory.
                Defaults to the current directory.
        """
        if sys.version_info < (3, 10, 0):
            logging.warning("You need Python 3.10 or later to use SnapshotManager.")
        if memory_viz_args is None:
            memory_viz_args = ["--roughjs-config", "seed=12345"]
        self.memory_viz_version = memory_viz_version
        self.memory_viz_args = memory_viz_args
        self._snapshot_counts = 0
        self.include = include

        if any("--output" in arg for arg in memory_viz_args):
            raise ValueError(
                "Use the output_directory argument to specify a different output path."
            )

        self.output_directory = output_directory if output_directory else "."

    def _trace_func(self, frame: types.FrameType, event: str, _arg: Any) -> None:
        """Trace function to take snapshots at each line of code."""
        if event == "line" and frame.f_locals:
            memory_viz_args_copy = self.memory_viz_args.copy()
            memory_viz_args_copy.extend(
                [
                    "--output",
                    os.path.join(
                        os.path.abspath(self.output_directory),
                        f"snapshot-{self._snapshot_counts}.svg",
                    ),
                ]
            )
            snapshot(
                include=self.include,
                save=True,
                memory_viz_args=memory_viz_args_copy,
                memory_viz_version=self.memory_viz_version,
            )
            self._snapshot_counts += 1

    def __enter__(self):
        """Set up the trace function to take snapshots at each line of code."""
        func_frame = inspect.getouterframes(inspect.currentframe())[1].frame
        func_frame.f_trace = self._trace_func
        sys.settrace(lambda *_args: None)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Remove the trace function."""
        sys.settrace(None)
        inspect.getouterframes(inspect.currentframe())[1].frame.f_trace = None
