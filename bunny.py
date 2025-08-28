from datetime import datetime, timezone
from typing import Dict, Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Virtual Bunny Care")

# Allow local dev frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Action(BaseModel):
    kind: Literal["carrot", "pellet", "pat", "toy"] | None = None


def clamp(v: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, v))


class Bunny:
    def __init__(self):
        now = datetime.now(timezone.utc).timestamp()
        self.state: Dict[str, float] = {
            "hunger": 40.0,  # 0 = full, 100 = starving
            "happiness": 70.0,  # 0 = sad, 100 = delighted
            "cleanliness": 80.0,  # 0 = messy, 100 = sparkling
            "energy": 70.0,  # optional stat
        }
        self.last_update = now

    def _decay(self):
        """Apply time-based changes since last_update."""
        now = datetime.now(timezone.utc).timestamp()
        elapsed_min = (now - self.last_update) / 60.0
        if elapsed_min <= 0:
            return

        # Tunable decay rates per minute
        hunger_rate = 1.2  # hunger increases over time
        happy_decay = 0.4
        clean_decay = 0.3
        energy_recover = 0.3  # slow idle recovery

        self.state["hunger"] = clamp(self.state["hunger"] + hunger_rate * elapsed_min)
        self.state["happiness"] = clamp(self.state["happiness"] - happy_decay * elapsed_min)
        self.state["cleanliness"] = clamp(self.state["cleanliness"] - clean_decay * elapsed_min)
        self.state["energy"] = clamp(self.state["energy"] + energy_recover * elapsed_min)

        self.last_update = now

    def status(self):
        self._decay()
        health = (
            clamp(100 - self.state["hunger"]) * 0.4
            + self.state["happiness"] * 0.3
            + self.state["cleanliness"] * 0.2
            + self.state["energy"] * 0.1
        )
        return {**self.state, "overallHealth": round(health, 1)}

    def feed(self, kind: Literal["carrot", "pellet"]):
        self._decay()
        if kind == "carrot":
            self.state["hunger"] = clamp(self.state["hunger"] - 18)
            self.state["happiness"] = clamp(self.state["happiness"] + 6)
        elif kind == "pellet":
            self.state["hunger"] = clamp(self.state["hunger"] - 28)
            self.state["cleanliness"] = clamp(self.state["cleanliness"] - 4)  # crumbs!
        self.state["energy"] = clamp(self.state["energy"] + 5)
        return self.status()

    def play(self, kind: Literal["pat", "toy"]):
        self._decay()
        if kind == "pat":
            self.state["happiness"] = clamp(self.state["happiness"] + 10)
            self.state["energy"] = clamp(self.state["energy"] + 3)
        elif kind == "toy":
            self.state["happiness"] = clamp(self.state["happiness"] + 16)
            self.state["energy"] = clamp(self.state["energy"] - 8)
            self.state["cleanliness"] = clamp(self.state["cleanliness"] - 2)  # messy play
        return self.status()

    def clean(self):
        self._decay()
        self.state["cleanliness"] = clamp(self.state["cleanliness"] + 25)
        self.state["happiness"] = clamp(self.state["happiness"] + 4)
        return self.status()

    def reset(self):
        self.__init__()
        return self.status()


bunny = Bunny()


@app.get("/api/status")
def get_status():
    return bunny.status()


@app.post("/api/feed")
def feed(action: Action):
    if action.kind not in ("carrot", "pellet"):
        return {"error": "Invalid feed kind. Use 'carrot' or 'pellet'."}
    return bunny.feed(action.kind)  # type: ignore


@app.post("/api/play")
def play(action: Action):
    if action.kind not in ("pat", "toy"):
        return {"error": "Invalid play kind. Use 'pat' or 'toy'."}
    return bunny.play(action.kind)  # type: ignore


@app.post("/api/clean")
def clean():
    return bunny.clean()


@app.post("/api/reset")
def reset():
    return bunny.reset()
