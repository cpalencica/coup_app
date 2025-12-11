from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any
import uuid

from ..game.engine import GameEngine
from ..game.actions import Action

router = APIRouter()

# Simple in-memory store of games for development/demo
GAMES: Dict[str, GameEngine] = {}


def get_engine(game_id: str) -> GameEngine:
    engine = GAMES.get(game_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return engine


@router.post("/", summary="Create a new game")
async def create_game() -> Dict[str, str]:
    game_id = str(uuid.uuid4())
    GAMES[game_id] = GameEngine()
    return {"game_id": game_id}


@router.post("/{game_id}/players", summary="Add player to game")
async def add_player(game_id: str, payload: Dict[str, str]):
    engine = get_engine(game_id)
    player_id = payload.get("player_id")
    name = payload.get("name")
    if not player_id or not name:
        raise HTTPException(status_code=400, detail="player_id and name required")
    try:
        engine.add_player(player_id, name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


@router.post("/{game_id}/start", summary="Start game (deal cards)")
async def start_game(game_id: str):
    engine = get_engine(game_id)
    try:
        engine.start()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"ok": True}


def _serialize_state(engine: GameEngine) -> Dict[str, Any]:
    s = engine.state
    return {
        "players": [
            {
                "id": p.id,
                "name": p.name,
                "coins": p.coins,
                "cards": [c.value for c in p.cards],
                "influence": p.influence,
            }
            for p in s.players
        ],
        "deck_count": len(s.deck),
        "discard_count": len(s.discard),
        "current_player_idx": s.current_player_idx,
        "pending_action": s.pending_action.value if s.pending_action else None,
        "awaiting_challenge": s.awaiting_challenge,
        "awaiting_block": s.awaiting_block,
        "block_type": s.block_type,
    }


@router.get("/{game_id}/state", summary="Get game state (debug view)")
async def get_state(game_id: str):
    engine = get_engine(game_id)
    return _serialize_state(engine)


@router.post("/{game_id}/declare", summary="Declare an action")
async def declare_action(game_id: str, payload: Dict[str, str]):
    engine = get_engine(game_id)
    player_id = payload.get("player_id")
    action_str = payload.get("action")
    target_id = payload.get("target_id")
    if not player_id or not action_str:
        raise HTTPException(status_code=400, detail="player_id and action required")
    try:
        action = Action(action_str)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid action")
    try:
        msg = engine.declare_action(player_id, action, target_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": msg}


@router.post("/{game_id}/challenge", summary="Challenge the pending action/block")
async def challenge(game_id: str, payload: Dict[str, str]):
    engine = get_engine(game_id)
    challenger_id = payload.get("challenger_id")
    if not challenger_id:
        raise HTTPException(status_code=400, detail="challenger_id required")
    try:
        msg = engine.challenge(challenger_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": msg}


@router.post("/{game_id}/block", summary="Declare a block")
async def block(game_id: str, payload: Dict[str, str]):
    engine = get_engine(game_id)
    blocker_id = payload.get("blocker_id")
    block_type = payload.get("block_type")
    if not blocker_id or not block_type:
        raise HTTPException(status_code=400, detail="blocker_id and block_type required")
    try:
        msg = engine.block(blocker_id, block_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": msg}


@router.post("/{game_id}/resolve", summary="Resolve the pending action")
async def resolve(game_id: str):
    engine = get_engine(game_id)
    try:
        msg = engine.resolve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"message": msg}


# Minimal websocket endpoint — a separate connection manager broadcasts simple json messages
from ..websocket.manager import ConnectionManager

manager = ConnectionManager()


@router.websocket("/ws/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await manager.connect(websocket, game_id)
    try:
        while True:
            data = await websocket.receive_text()
            # For now echo back and broadcast to all clients in the same game room
            await manager.broadcast(f"[{game_id}] {data}", game_id)
    except WebSocketDisconnect:
        manager.disconnect(websocket, game_id)
