import concurrent.futures
import os
from concurrent.futures import ThreadPoolExecutor

from defusedxml import ElementTree

from shrub_archi.identity_resolver import IdentityRepository, Identity


def extract_identities_from_collaboration_folder(archi_repo_folder: str,
                                                 repo: IdentityRepository = None) -> IdentityRepository:
    result = repo if repo else IdentityRepository()
    count = 0
    for dirpath, dir, files in os.walk(archi_repo_folder):
        def read_identity(dirpath, file):
            result = None
            full_filename = os.path.join(dirpath, file)
            # print(f"start reading id from {full_filename}")
            try:
                et = ElementTree.parse(full_filename)
                root = et.getroot()
                identity = Identity(unique_id=root.get("id"), name=root.get("name"),
                                    classification=root.tag)
                if identity.unique_id and identity.name:
                    result = identity
            except Exception as ex:
                print(f"problem with file {full_filename}", ex)
            return result

        with ThreadPoolExecutor(max_workers=128) as exec:
            futures = {exec.submit(read_identity, dirpath, file): file for file in
                       files}
            for future in concurrent.futures.as_completed(futures):
                identity = future.result()
                if identity:
                    result.add(identity)
                count += 1
                print(f"{count}")

    return result
