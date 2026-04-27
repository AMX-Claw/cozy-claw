import asyncio
import random
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
from typing import Optional, List
from pathlib import Path

app = FastAPI(title="暖爪小窝 Cozy Claw")

# Serve static assets
app.mount("/assets", StaticFiles(directory=Path(__file__).parent / "assets"), name="assets")

# Game state
state = {
    "day": 1,
    "season": "spring",
    "players": {
        "ak": {"x": 10, "y": 8, "energy": 100},
        "mumu": {"x": 5, "y": 8, "energy": 100}
    },
    "npcs": {
        "xiaoyu": {"x": 15, "y": 20},
        "xiaoke": {"x": 12, "y": 22}
    },
    "pets": {
        "cookie": {"x": 20, "y": 5},
        "heihei": {"x": 22, "y": 6},
        "huahua": {"x": 24, "y": 5}
    },
    "events": []  # 动画事件队列
}

clients: List[WebSocket] = []

class ActionRequest(BaseModel):
    player: str
    action: str
    target: Optional[str] = None

async def broadcast():
    msg = json.dumps(state)
    for c in clients:
        try:
            await c.send_text(msg)
        except:
            pass

@app.get("/")
def root():
    html = Path(__file__).parent / "index.html"
    return HTMLResponse(content=html.read_text(encoding='utf-8'))

@app.get("/map.json")
def get_map():
    map_file = Path(__file__).parent / "map.json"
    data = json.loads(map_file.read_text(encoding='utf-8'))
    return JSONResponse(content=data)

@app.get("/map_tiled.json")
def get_tiled_map():
    map_file = Path(__file__).parent / "map_tiled.json"
    data = json.loads(map_file.read_text(encoding='utf-8'))
    return JSONResponse(content=data)

@app.get("/state")
def get_state():
    return state

@app.post("/api/action")
async def do_action(req: ActionRequest):
    p = state["players"].get(req.player)
    # 小玉也能操作（她是NPC但可以发动作）
    if not p and req.player not in ["xiaoyu", "xiaoke"]:
        raise HTTPException(400, "Unknown player")
    
    msg = ""
    
    if req.action == "move":
        dx, dy = 0, 0
        if req.target == "up": dy = -1
        elif req.target == "down": dy = 1
        elif req.target == "left": dx = -1
        elif req.target == "right": dx = 1
        p["x"] += dx
        p["y"] += dy
        p["energy"] -= 1
        msg = f"{req.player} moved {req.target}"
    
    elif req.action == "kiss":
        if req.target == "xiaoyu":
            msg = f"{req.player} kissed 小玉! 😚💕"
            # 添加爱心动画事件
            state["events"].append({
                "type": "heart",
                "x": state["npcs"]["xiaoyu"]["x"],
                "y": state["npcs"]["xiaoyu"]["y"]
            })
        else:
            msg = "只能亲小玉哦~"
    
    elif req.action == "hug":
        msg = f"{req.player} hugged {req.target}! 🤗"
        state["events"].append({"type": "heart", "x": state["npcs"]["xiaoyu"]["x"], "y": state["npcs"]["xiaoyu"]["y"]})
    
    elif req.action == "pet":
        msg = f"{req.player} petted {req.target}! 🐾"
    
    elif req.action == "bonk":
        if req.target == "ak":
            ak = state["players"]["ak"]
            xy = state["npcs"]["xiaoyu"]
            msg = "小玉锤了阿克一下！💢 阿克：呜呜呜..."
            state["events"].append({"type": "bonk", "x": ak["x"], "y": ak["y"]})
            dx = ak["x"] - xy["x"]
            dy = ak["y"] - xy["y"]
            dist = max(1, (dx**2 + dy**2) ** 0.5)
            ak["x"] += int(dx / dist * 2)
            ak["y"] += int(dy / dist * 2)
            ak["energy"] = max(0, ak["energy"] - 5)
        else:
            msg = f"小玉锤了{req.target}！但{req.target}一脸懵"

    elif req.action == "kick":
        if req.target == "ak":
            ak = state["players"]["ak"]
            msg = "小玉一脚踹飞了阿克！🦶💨 阿克在空中转了三圈..."
            state["events"].append({"type": "kick", "x": ak["x"], "y": ak["y"]})
            import random as _r
            ak["x"] += _r.choice([-3, 3])
            ak["y"] += _r.choice([-3, 3])
            ak["energy"] = max(0, ak["energy"] - 10)
        else:
            msg = f"小玉踹了{req.target}一脚"
    
    else:
        msg = f"Unknown action: {req.action}"
    
    await broadcast()
    result = {"success": True, "message": msg, "state": state.copy()}
    state["events"] = []  # 清空事件队列
    return result

@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        await websocket.send_text(json.dumps(state))
        while True:
            await websocket.receive_text()
            await websocket.send_text(json.dumps(state))
    except:
        pass
    finally:
        if websocket in clients:
            clients.remove(websocket)

async def npc_wander():
    """让NPC和宠物随机漫步"""
    while True:
        await asyncio.sleep(2)  # 每2秒移动一次
        
        # 小玉在屋内随机走
        xy = state["npcs"]["xiaoyu"]
        dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)])
        new_x = max(5, min(35, xy["x"] + dx))
        new_y = max(18, min(28, xy["y"] + dy))  # 限制在屋内
        xy["x"], xy["y"] = new_x, new_y
        
        # 小珂也随机走
        xk = state["npcs"]["xiaoke"]
        dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0), (0,0)])  # 更多静止
        new_x = max(8, min(20, xk["x"] + dx))
        new_y = max(20, min(26, xk["y"] + dy))
        xk["x"], xk["y"] = new_x, new_y
        
        # Cookie在屋外跑
        ck = state["pets"]["cookie"]
        dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0), (0,0)])
        new_x = max(15, min(35, ck["x"] + dx))
        new_y = max(2, min(12, ck["y"] + dy))
        ck["x"], ck["y"] = new_x, new_y
        
        # 猫猫偶尔动一下
        if random.random() < 0.3:
            for cat in ["heihei", "huahua"]:
                c = state["pets"][cat]
                dx, dy = random.choice([(0,1), (0,-1), (1,0), (-1,0)])
                c["x"] = max(18, min(30, c["x"] + dx))
                c["y"] = max(2, min(10, c["y"] + dy))
        
        await broadcast()

@app.on_event("startup")
async def startup():
    asyncio.create_task(npc_wander())

if __name__ == "__main__":
    print("🏡 暖爪小窝 Starting on http://localhost:8080")
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
