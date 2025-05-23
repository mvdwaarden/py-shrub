import json
import os
import shutil
from typing import Optional, List, Tuple

from shrub_archi.modeling.archi.resolver.entity_resolver import ResolvedEntity
from shrub_util.core import logging as logging


class ResolutionStore:
    def __init__(self, location: str):
        # currently a files based store
        # location is the directory/folder the resolution files are stored
        self.location = location
        self._resolutions: Optional[List[Tuple[str, str, bool]]] = None

    @property
    def resolutions(self):
        return self._resolutions

    @resolutions.setter
    def resolutions(self, resolved_entities: List[ResolvedEntity]):
        self._resolutions = {}
        for resolution in resolved_entities:
            self._resolutions[
                resolution.source.unique_id, resolution.target.unique_id
            ] = resolution.resolver_result.manual_verification

    def _get_resolution_file(self, name) -> str:
        return os.path.join(
            self.location, f"{name if name else 'resolved_entities'}.json"
        )

    def _read_from_string(self, resolutions: str):
        self._resolutions = {}
        for id1, id2, manually_verified in json.loads(resolutions):
            self._resolutions[(id1, id2)] = manually_verified

    def read_from_string(self, resolutions: str):
        if not self._resolutions:
            try:
                self._read_from_string(resolutions)
            except Exception as ex:
                logging.get_logger().error(f"problem reading resolutions", ex=ex)
        return self.resolutions

    def read(self, name: str):
        if not self._resolutions:
            try:
                with open(self._get_resolution_file(name), "r") as ifp:
                    self._read_from_string(ifp.read())
            except Exception as ex:
                logging.get_logger().error(
                    f"problem reading resolution file {self._get_resolution_file(name)}",
                    ex=ex,
                )
                self._resolutions = {}
        return self.resolutions

    def write(self, name: str):
        try:
            tmp = []
            for (id1, id2), value in self.resolutions.items():
                tmp.append((id1, id2, value))
            if os.path.exists(self._get_resolution_file(name)):
                i = 0
                while os.path.exists(f"{self._get_resolution_file(name)}.backup.{i}"):
                    i += 1
                shutil.copyfile(
                    src=self._get_resolution_file(name),
                    dst=f"{self._get_resolution_file(name)}.backup.{i}",
                )
            with open(self._get_resolution_file(name), "w") as ofp:
                json.dump(tmp, ofp)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing resolution file {self._get_resolution_file}", ex=ex
            )

    def resolution(self, id1, id2):
        if self.resolutions and (id1, id2) in self.resolutions:
            return self.resolutions[id1, id2]
        else:
            return None

    def apply_to(self, resolved_ids: List[ResolvedEntity]):
        for (id1, id2), manual_verification in self.resolutions.items():
            for res_id in [
                res_id
                for res_id in resolved_ids
                if res_id.source.unique_id == id1 and res_id.target.unique_id == id2
            ]:
                res_id.resolver_result.manual_verification = manual_verification
                res_id.resolver_result.rule = f"*{res_id.resolver_result.rule}"
                break
