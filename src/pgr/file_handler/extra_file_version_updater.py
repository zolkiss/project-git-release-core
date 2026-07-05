import copy
import json
import re
from pathlib import Path
from re import Pattern
from tempfile import TemporaryDirectory

from jsonpath_ng import parse

from pgr import log
from pgr.config import ReleaseConfig
from pgr.interfaces import NewVersion
from pgr.semver_util import build_version_regex, VersionParts


class ExtraFileVersionUpdater:
    @staticmethod
    def __has_key(key: str, config: dict) -> bool:
        return key in config.keys() and config[key] is not None

    @staticmethod
    def __str_key_not_defined(key: str, config: dict) -> bool:
        return ExtraFileVersionUpdater.__has_key(key, config) and config[key].strip() == ""

    def __init__(self, config: ReleaseConfig, extra_file_config: dict, temp_dir: TemporaryDirectory):
        self.config = config
        self.extra_file_config = extra_file_config
        self.temp_dir = temp_dir

    def update_files(self, current_version: str | None, new_version: NewVersion, text_append_missing: bool):
        if self.__has_key("json", self.extra_file_config):
            self.__update_json_files(self.extra_file_config["json"], new_version)
        if self.__has_key("text", self.extra_file_config):
            self.__update_text_files(self.extra_file_config["text"], new_version, text_append_missing)

    def __update_json_files(self, json_configs: dict, new_version: NewVersion):
        for json_config in json_configs:
            if (self.__str_key_not_defined("repo_path", json_config) or
                    self.__str_key_not_defined("version_path", json_config)):
                log.error(
                    "Invalid configuration. In case of JSON Extra file the non empty repo_path and version_path keys are needed")
                continue

            repo_path = json_config["repo_path"]
            file_path = Path(f"{self.temp_dir.name}/{repo_path}")
            if not file_path.exists():
                log.warn("Cannot find target JSON file from config: %s", repo_path)
                continue

            with open(file_path, "r") as fr:
                json_file: dict = json.load(fr)

            version_path = json_config["version_path"]
            json_path_exp = parse(version_path)

            updated_json_file = copy.deepcopy(json_file)
            json_path_creation_allowed = self.__eval_create_if_not_exists(updated_json_file)
            if json_path_creation_allowed:
                json_path_exp.update_or_create(updated_json_file, new_version.get_full_version())
            else:
                json_path_exp.update(updated_json_file, new_version.get_full_version())

            if updated_json_file == json_file:
                log.warn("Cannot find version path (%s) in the %s file", version_path, repo_path)
            else:
                with open(file_path, "w") as fw:
                    json.dump(updated_json_file, fw, indent=4)

    def __update_text_files(self, text_configs: dict, new_version: NewVersion, text_append_missing: bool):
        for text_file_path in text_configs:
            log.info("Updating version in %s", text_file_path)
            file_path = Path(f"{self.temp_dir.name}/{text_file_path}")
            if not file_path.exists():
                log.warn("Cannot find target text file from config: %s", text_file_path)
                continue

            with open(file_path, "r") as fr:
                text_file = fr.readlines()

            block_pair_indexes: list[tuple[int, int]] = []
            block_inline_indexes: list[int] = []

            for idx, line in enumerate(text_file):
                if self.config.version_config_marker_block_start in line:
                    temp_tuple = None
                    for iidx, iline in enumerate(text_file[idx:]):
                        if self.config.version_config_marker_block_end in iline:
                            temp_tuple = (idx + 1, iidx + idx)
                            break
                    if temp_tuple is not None:
                        block_pair_indexes.append(temp_tuple)
                    else:
                        log.error("Cannot find ending marker for starting marker at line %s", idx + 1)
                elif (self.config.version_config_marker in line and
                      self.config.version_config_marker_block_start not in line and
                      self.config.version_config_marker_block_end not in line):
                    block_inline_indexes.append(idx)

            if len(block_inline_indexes) == 0 and len(block_pair_indexes) == 0:
                log.info("Cannot find version maker in %s", text_file_path)
                continue

            semver_version_patter = build_version_regex(new_version.prefix)
            for idx_pair in block_pair_indexes:
                idx_start = idx_pair[0]
                idx_end = idx_pair[1]
                lines_to_update = text_file[idx_start:idx_end]
                updated_lines = self.__update_block_versions(lines_to_update, semver_version_patter, new_version,
                                                             text_append_missing)
                if updated_lines == lines_to_update:
                    log.warn("No update happened in the marked lines")
                else:
                    text_file[idx_start:idx_end] = updated_lines

            for idx in block_inline_indexes:
                line = text_file[idx]
                updated_line = self.__update_inline_version(line, semver_version_patter, new_version,
                                                            text_append_missing)
                if updated_line == line:
                    log.warn("No update happened in the inline marked line")
                else:
                    text_file[idx] = updated_line

            with open(file_path, "w") as fw:
                fw.write("".join(text_file))

    @staticmethod
    def __eval_create_if_not_exists(json_config):
        return ("create_property" in json_config.keys() and
                json_config["create_property"])

    @staticmethod
    def __update_block_versions(lines_to_update: list[str], pattern: Pattern,
                                new_version: NewVersion, text_append_missing: bool) -> list[str]:
        working_set = []
        for line in lines_to_update:
            matches = pattern.search(line)
            updated_line = line
            if matches is None:
                if text_append_missing:
                    ends_with_newline = line.endswith("\n")
                    updated_line = f"{line.rstrip()} {new_version.get_full_version()}"
                    if ends_with_newline:
                        updated_line += "\n"
                else:
                    log.warn("Cannot find version to update. Appending to end of the line...")
            else:
                old_version = matches.group(VersionParts.FULL_VERSION)
                log.info("Found old version: %s", old_version)
                updated_line = line.replace(old_version, new_version.get_full_version())
            working_set.append(updated_line)
        return working_set

    def __update_inline_version(self, line: str, pattern: Pattern,
                                new_version: NewVersion, text_append_missing: bool) -> str:
        matches = pattern.search(line)
        updated_line = line
        if matches is None:
            if text_append_missing:
                marker_pattern = self.__build_markter_patter(self.config.version_config_marker)
                marker = marker_pattern.search(line)
                if marker is None:
                    log.error("Cannot identify inline marker in line: %s. Skipping", line)
                updated_line = line.replace(marker.group(0), f"{new_version.get_full_version()} {marker.group(0)}")
            else:
                log.warn("Cannot find version to update. Appending to end of the line...")
        else:
            updated_line = line.replace(matches.group(VersionParts.FULL_VERSION), new_version.get_full_version())
        return updated_line

    def __build_markter_patter(self, version_config_marker: str) -> Pattern:
        escaped_marker = re.escape(version_config_marker)
        pattern = rf"[^\w\s]+\s*{escaped_marker}(?:\s*[^\w\s]+)?"
        return re.compile(pattern)
