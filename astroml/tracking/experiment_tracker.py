from typing import Dict, Any, Optional

class ExperimentTracker:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {}
        
    def log_experiment(self, name: str, result: str) -> None:
        self.data[name] = result
        
    def get_experiment_log(self, name: str) -> Optional[str]:
        return self.data.get(name)
