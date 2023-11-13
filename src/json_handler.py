import json
import os
from pathlib import Path


class HandlerJson:
    def __init__(self, file_name: str = 'project.json'):
        self._file_json: dict = {}
        self._file_name = file_name
        self._file_name_full = f'../{self._file_name}'

        self.__load_json()

    def __load_json(self) -> None:
        with open(self._file_name_full, 'r', encoding='utf-8') as f:
            self._file_json = json.load(f)

    def dump_json(self) -> None:
        print(json.dumps(self._file_json, indent=4, ensure_ascii=False))

    def get_json(self) -> dict:
        return self._file_json

    def reload_json(self) -> None:
        self.__load_json()

    def reset_json(self) -> None:
        aux = {
            "runs": []
        }
        with open(self._file_name_full, 'w', encoding='utf-8') as f:
            json.dump(aux, f, indent=4, ensure_ascii=False)
        self.__load_json()

    def write_run(self, timestamp: str, total: int, infos: list) -> None:
        list_runs = self._file_json['runs']
        aux = {
            'timestamp': timestamp,
            'total': total,
            'games': infos
        }
        list_runs.append(aux)
        self._file_json['runs'] = list_runs
        with open(self._file_name_full, 'w', encoding='utf-8') as f:
            json.dump(self._file_json, f, indent=4, ensure_ascii=False)

    def get_last_run(self) -> dict:
        list_runs = self._file_json['runs']
        qtde = len(list_runs)
        if qtde == 0:
            return None
        else:
            return list_runs[qtde - 1]
