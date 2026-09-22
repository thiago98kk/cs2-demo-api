import os
import tempfile
import requests

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from demoparser2 import DemoParser


app = FastAPI(title="CS2 Demo Parser API")


class ParseRequest(BaseModel):
    demo_id: str
    project_id: str | None = None
    file_url: str
    team_name: str | None = None
    map: str | None = None


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "cs2-demo-parser"
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/parse-demo")
def parse_demo(request: ParseRequest):
    temp_path = None

    try:
        # 1. Baixar a demo
        response = requests.get(
            request.file_url,
            stream=True,
            timeout=120
        )

        response.raise_for_status()

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=".dem"
        ) as temp_file:

            temp_path = temp_file.name

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):
                if chunk:
                    temp_file.write(chunk)

        # 2. Abrir demo
        parser = DemoParser(temp_path)

        # 3. Extrair eventos
        deaths = parser.parse_event(
            "player_death",
            player=["X", "Y", "Z"]
        )

        grenades = parser.parse_events([
            "smokegrenade_detonate",
            "flashbang_detonate",
            "hegrenade_detonate",
            "inferno_startburn",
            "bomb_planted",
            "bomb_defused"
        ])

        # 4. Extrair posições
        positions = parser.parse_ticks([
            "X",
            "Y",
            "Z",
            "health",
            "armor_value",
            "team_num",
            "name",
            "steamid",
            "active_weapon_name"
        ])

        # Transformar DataFrames em JSON
        death_records = deaths.to_dicts()

        position_records = positions.to_dicts()

        event_records = []

        for event_name, dataframe in grenades.items():
            if dataframe is None:
                continue

            for row in dataframe.to_dicts():
                row["event_type"] = event_name
                event_records.append(row)

        return {
            "success": True,

            "demo_id": request.demo_id,

            "project_id": request.project_id,

            "match": {
                "map": request.map,
                "team_analyzed": request.team_name
            },

            "rounds": [],

            "events": death_records + event_records,

            "players": [],

            "positions": position_records,

            "features": []
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
