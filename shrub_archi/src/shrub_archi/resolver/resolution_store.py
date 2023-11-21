import json
import os
from typing import Optional, List, Tuple

from shrub_archi.resolver.identity_resolver import ResolvedIdentity
from shrub_util.core import logging as logging


class ResolutionStore:
    def __init__(self, location: str):
        self.location = location
        self._resolutions: Optional[List[Tuple[str, str, bool]]] = None

    @property
    def resolutions(self):
        return self._resolutions

    @resolutions.setter
    def resolutions(self, resolved_identities: List[ResolvedIdentity]):
        self._resolutions = {}
        for res_id in resolved_identities:
            self._resolutions[
                res_id.identity1.unique_id, res_id.identity2.unique_id] = res_id.resolver_result.manual_verification

    def _get_resolution_file(self, name) -> str:
        return os.path.join(self.location,
                            f"{name if name else 'resolved_identities'}.json")

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
                    ex=ex)
                self._resolutions = {}
        return self.resolutions

    def write(self, name: str):
        try:
            tmp = []
            for (id1, id2), value in self.resolutions.items():
                tmp.append((id1, id2, value))
            with open(self._get_resolution_file(name), "w") as ofp:
                json.dump(tmp, ofp)
        except Exception as ex:
            logging.get_logger().error(
                f"problem writing resolution file {self._get_resolution_file}", ex=ex)

    def resolution(self, id1, id2):
        if self.resolutions and (id1, id2) in self.resolutions:
            return self.resolutions[id1, id2]
        else:
            return None

    def is_resolved(self, id2):
        result = False, None
        if self.resolutions:
            for verified in [value for (_, id2_check), value in self.resolutions.items()
                             if id2 == id2_check]:
                result = True, verified
                break
        return result

    def apply_to(self, resolved_ids: List[ResolvedIdentity]):
        for (id1, id2), manual_verification in self.resolutions.items():
            for res_id in [res_id for res_id in resolved_ids if
                           res_id.identity1.unique_id == id1 and res_id.identity2.unique_id == id2]:
                res_id.resolver_result.manual_verification = manual_verification
                res_id.resolver_result.rule = "ID_RESOLUTION_FILE"
                break

    def update_uuids_in_str(self, content: str) -> str:
        for (id1, id2), value in self.resolutions.items():
            if value is True:
                content = content.replace(id2, id1)
        return content
