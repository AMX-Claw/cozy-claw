# Cozy Claw - Tiled 地图项目 🎮

## 打开方式
用 Tiled.app 打开 `cozy-claw.tmx`

## 地图信息
- **尺寸：** 60×69 格（= 游戏世界 960×1104 像素，每格16px，游戏里3倍放大）
- **Tile大小：** 16×16 像素
- **游戏画布：** 800×600（相机跟随玩家）

## 图层说明
| 图层 | 用途 |
|------|------|
| **Ground** | 草地、水、泥土等地面 |
| **Terrain** | 路径、农田、高低差 |
| **Buildings** | 房子墙壁、屋顶、栅栏 |
| **Decorations** | 树、花、家具、装饰物 |
| **Above Player** | 树冠等需要遮住角色的部分 |
| **Markers** | 对象层，标记角色出生点等（不渲染） |

## 角色们（不用画在地图里，代码控制）
- 🦊 **小玉** — 狐狸，玩家控制
- 🐙 **阿克** — 章鱼，NPC跟随小玉
- 🪵 **木木** — 蓝色方块，NPC闲逛
- 🐕 **Cookie** — 约克夏，NPC
- 🐱 **黑黑** — 黑猫，NPC
- 🐱 **花花** — 虎斑猫，NPC
- 🐣 **小鸡们** — 农场小鸡

## 已加载的Tileset（20个）
你可以在Tiled里随时添加更多！所有素材都在 `tilesets/` 文件夹里（共46个png）。

### 地面类
- Grass (基础草地)、Grass V2 (进阶草地)、Water、Hills、Tilled Dirt

### 建筑类  
- Walls、Roof、Doors、Fences、Paths、Stone Path、Furniture

### 装饰类
- Grass Things、Trees Bushes、Flowers Stones、Farming Plants
- Cherry Blossom、Outdoor Decor、Signs、Spring Crops

### 还没加载但可以用的（tilesets/文件夹里）
- `cherry_tree_big.png` — 大樱花树
- `pink_house.png` — 粉色小别墅（你选的那个！）
- `small_house.png` / `brick_house.png` / `huts.png` — 村庄房子
- `boats.png` — 小船
- `water_well.png` — 水井
- `picnic_basket.png` / `picnic_blanket.png` — 野餐
- `wooden_furniture_v2.png` — 更多家具
- `modern_furniture.png` — 现代家具（从HA项目搬过来的）
- `trees_bushes_v2.png` — 更多树和灌木
- `oak_tree.png` — 橡树
- 还有更多...

## 画完之后
告诉阿克，他会写一个转换脚本把tmx导出成游戏用的map.json 🐙
