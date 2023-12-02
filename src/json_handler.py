import json
import os
from pathlib import Path


class HandlerJsonBase:
    def __init__(self, file_name: str):
        self._json: dict = {}
        self._file_name: str = file_name

        self.__load_json()

    def __load_json(self):
        with open(self._file_name, 'r', encoding='utf-8') as f:
            self._json = json.load(f)

    def dump_json(self):
        print(json.dumps(self._json, indent=4, ensure_ascii=False))

    def get_json(self) -> dict:
        return self._json

    def reload_json(self) -> None:
        self.__load_json()


class HandlerJsonProject(HandlerJsonBase):
    def __init__(self):
        super(HandlerJsonProject, self).__init__(file_name=os.path.join(Path(__file__).parent.parent, 'project.json'))

    def get_min_discount_pct(self) -> float:
        return self._json.get('min_discount_pct', None)


class HandlerJsonRuns(HandlerJsonBase):
    def __init__(self):
        super(HandlerJsonRuns, self).__init__(file_name=os.path.join(Path(__file__).parent.parent, 'runs.json'))

    def reset_runs(self) -> None:
        reset_json = {
            "runs": []
        }
        with open(self._file_name, 'w', encoding='utf-8') as f:
            json.dump(reset_json, f, indent=4, ensure_ascii=False)
        self.__load_json()

    def write_run(self, timestamp: str, total: int, infos: list) -> None:
        list_runs = self._json.get('runs')
        run_dict = {
            'timestamp': timestamp,
            'total': total,
            'games': infos
        }
        list_runs.append(run_dict)
        self._json['runs'] = list_runs
        with open(self._file_name, 'w', encoding='utf-8') as f:
            json.dump(self._json, f, indent=4, ensure_ascii=False)

    def get_last_run(self) -> dict:
        list_runs = self._json.get('runs')
        qtde = len(list_runs)
        if qtde > 0:
            return list_runs[qtde - 1]
