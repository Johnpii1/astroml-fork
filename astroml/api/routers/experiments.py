from typing import Optional
from typing import Dict, Any

class ExperimentsRouter:
    def __init__(self) -> None:
        self.experiments: Dict[str, Any] = {}
        
    def create_experiment(self, name: str) -> None:
        self.experiments[name] = {"status": "running"}
        
    def get_experiment(self, name: str) -> Optional[Dict[str, Any]]:
        return self.experiments.get(name)
