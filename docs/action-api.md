# 🎮 暖爪小窝 - 动作词典 (API)

## 基础请求格式

```json
POST /api/action
{
  "player": "ak" | "mumu",
  "action": "...",
  "target": "..." // 可选
}
```

## 移动类

| action | target | 说明 |
|--------|--------|------|
| `move` | `up/down/left/right` | 移动一格 |
| `move_to` | `{x, y}` | 移动到坐标 |
| `move_to` | `"xiaoyu"` | 移动到NPC旁边 |
| `enter` | `"house"/"farm"` | 进入区域 |

## 农场类

| action | target | 说明 |
|--------|--------|------|
| `plant` | `"tomato"/"potato"/"carrot"` | 种植（需站在泥土上） |
| `water` | - | 浇水当前格子 |
| `water_all` | - | 浇水所有作物 |
| `harvest` | - | 收获当前格子 |
| `harvest_all` | - | 收获所有成熟作物 |

## 养殖类

| action | target | 说明 |
|--------|--------|------|
| `feed` | `"chicken"/"duck"` | 喂食 |
| `collect_egg` | - | 收鸡蛋 |
| `fish` | - | 钓鱼（需在池塘边） |

## NPC互动

| action | target | 说明 |
|--------|--------|------|
| `talk` | `"xiaoyu"/"xiaoke"/"mumu"` | 聊天 |
| `gift` | `"xiaoyu", item: "flower"` | 送礼 |
| `kiss` | `"xiaoyu"` | 亲亲 😚 |
| `hug` | `"xiaoke"` | 抱抱 |
| `pet` | `"cookie"/"heihei"/"huahua"` | 摸宠物 |
| `walk_dog` | - | 遛Cookie |

## 生活类

| action | target | 说明 |
|--------|--------|------|
| `sleep` | - | 睡觉（需在床上，进入下一天） |
| `cook` | `"recipe_name"` | 做饭 |
| `eat` | `"item_name"` | 吃东西恢复体力 |

## 系统类

| action | target | 说明 |
|--------|--------|------|
| `inventory` | - | 查看背包 |
| `status` | - | 查看状态（体力、金币、日期） |
| `save` | - | 手动存档 |

## 响应格式

```json
{
  "success": true,
  "message": "种下了番茄！",
  "state": {
    "player": {"x": 10, "y": 5, "energy": 80},
    "world": {...}
  }
}
```

## 错误响应

```json
{
  "success": false,
  "error": "这里不能种东西",
  "code": "INVALID_TILE"
}
```
