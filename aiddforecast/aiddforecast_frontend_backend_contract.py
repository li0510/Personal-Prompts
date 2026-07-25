# aiddforecast_frontend_backend_contract.py
"""
AIDDForecast 框架 — 前后端交互契约（指导级）。

本文件定义框架前端（WEB 端 / 命令行工具）与框架后端
（引擎 / 调度器 / 管道链）之间的完整交互逻辑。

任何 AI Agent 或开发者阅读本文件后，应能完整理解：
    - 用户如何通过不同途径上传主数据
    - 每种途径支持哪些读取形式
    - 后端六种运行模式及其对应的前端调用方式
    - 多项目模式下用户如何指定每个项目的具体文件

结构：
    1. 前后端职责划分
    2. 用户上传主数据途径
    3. 后端六种运行模式 × 前端调用矩阵
    4. 多项目文件映射语法

遵循：
    - P40（全局一致性）：前后端接口统一
    - P50（技术可解释性）：每种场景对应明确的业务操作
    - 哲学二（从数据开始，由判断结束）：框架是参谋，用户是指挥官
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════
# 1. 前后端职责划分
# ═══════════════════════════════════════════════════════════════════

FRONTEND_BACKEND_ROLES: str = """
前后端职责划分。

前端（WEB 端 + 命令行工具 aidctl）：
    人类用户与框架后端的交互窗口。
    职责：传递信息与数据，展示后端返回的实际成果。
    不处理数据，不做业务决策。

后端（引擎 / 调度器 / 管道链 / 中间件 / 工具集）：
    框架核心模块。
    职责：加载数据、处理数据、生产数据、返回数据。
    所有业务决策由调度器和管道链完成。
"""

# ═══════════════════════════════════════════════════════════════════
# 2. 用户上传主数据途径
# ═══════════════════════════════════════════════════════════════════

DATA_UPLOAD_PATHWAYS: str = """
用户上传主数据途径。

用户可通过三种途径将主数据传递给框架后端：
    1. WEB 端 — 在可视化控制台上传文件或配置路径
    2. 命令行工具（aidctl）— 通过 -f / -p 参数指定文件或项目
    3. 配置文件（config.yaml）— 在 data.source 中配置路径

每种途径支持两种方式：
    方式一：显式上传
        - WEB 端：用户上传文件 → 保存到临时路径 → 将路径传给后端
        - 命令行：用户通过 -f 或 -p 参数指定文件路径 → 直接传给后端
        - 适用场景：单次运行。用户每次手动指定文件。

    方式二：配置文件配置
        - WEB 端：用户在项目配置中填写 data.source
        - 命令行：用户通过 aidctl startproject 生成 config.yaml，
          在 data.source 中填写路径
        - 适用场景：重复运行。如某单项目多文件异步并行场景需要
          每周运行，配置好文件存放路径后，框架后端自行扫描加载。

每种方式支持两种读取形式：
    形式一：具体文件路径 — 精确指定到某个文件
        - 示例：-f ./data/sales_2024.csv
        - 示例：data.source: ./data/sales_2024.csv

    形式二：目录 / 项目路径扫描 — 指定到目录或项目名，框架自行扫描
        - 示例：-f ./data/（扫描该目录下所有 CSV）
        - 示例：data.source: ./data/（扫描该目录下所有 CSV）
        - 多项目：-p proj1（扫描 projects/proj1/data/ 下所有 CSV）
"""

# ═══════════════════════════════════════════════════════════════════
# 3. 后端六种运行模式 × 前端调用矩阵
# ═══════════════════════════════════════════════════════════════════

RUN_MODE_MATRIX: str = """
后端六种运行模式 × 前端调用矩阵。

以下矩阵覆盖单项目 / 多项目下所有组合。
每种模式 × 每种方式 × 每种形式均有明确的用户操作和引擎入口。

─── 模式一：单项目 · 单文件运行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────
显式上传 │ 具体文件 │ aidctl run my_project -f a.csv       │ execute(file_paths=["a.csv"])
显式上传 │ 目录扫描 │ aidctl run my_project -f ./d/        │ execute(file_paths=["./d/"])
         │          │   --mode single                      │ （引擎扫描取第一个）
配置文件 │ 具体文件 │ config.yaml:                         │ execute()
         │          │   data.source: ./data/a.csv           │ （引擎读配置加载）
配置文件 │ 目录扫描 │ config.yaml:                         │ execute()
         │          │   data.source: ./data/               │ （引擎扫描取第一个）
默认     │ —        │ aidctl run my_project                │ execute()
         │          │ （自动扫描项目数据目录）             │ （引擎扫描取第一个）

─── 模式二：单项目 · 多文件合并成单文件运行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────────────
显式上传 │ 具体文件 │ aidctl run my_project -f a.csv b.csv │ execute(file_paths=["a.csv","b.csv"],
         │          │   --mode merge                       │          mode="merge")
显式上传 │ 目录扫描 │ aidctl run my_project -f ./d/        │ execute(file_paths=["./d/"],
         │          │   --mode merge                       │          mode="merge")
配置文件 │ 具体文件 │ config.yaml:                         │ execute(mode="merge")
         │          │   data.source:                       │ （引擎读配置合并）
         │          │     - ./data/a.csv                   │
         │          │     - ./data/b.csv                   │
配置文件 │ 目录扫描 │ config.yaml:                         │ execute(mode="merge")
         │          │   data.source: ./data/               │ （引擎扫描合并）

─── 模式三：单项目 · 多文件不合并异步并行运行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────────────
显式上传 │ 具体文件 │ aidctl run my_project -f a.csv b.csv │ execute(file_paths=["a.csv","b.csv"],
         │          │   --mode parallel                    │          mode="parallel")
显式上传 │ 目录扫描 │ aidctl run my_project -f ./d/        │ execute(file_paths=["./d/"],
         │          │   --mode parallel                    │          mode="parallel")
配置文件 │ 具体文件 │ config.yaml:                         │ execute(mode="parallel")
         │          │   data.source:                       │ （引擎读配置各文件独立运行）
         │          │     - ./data/a.csv                   │
         │          │     - ./data/b.csv                   │
配置文件 │ 目录扫描 │ config.yaml:                         │ execute(mode="parallel")
         │          │   data.source: ./data/               │ （引擎扫描各文件独立运行）

─── 模式四：多项目 · 各项目单文件 · 项目异步并行运行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────────────
显式上传 │ 默认扫描 │ aidctl run -p proj1 proj2            │ execute(project_file_map=
         │          │   --mode single                      │   {"proj1":None,"proj2":None},
         │          │ （各项目扫描目录取第一个文件）       │   mode="single")
显式上传 │ 用户指定 │ aidctl run -p proj1:data/a.csv       │ execute(project_file_map=
         │          │   proj2:data/b.csv --mode single      │   {"proj1":["data/a.csv"],
         │          │                                      │    "proj2":["data/b.csv"]},
         │          │                                      │   mode="single")
配置文件 │ 具体文件 │ 各项目 config.yaml:                  │ execute(project_file_map=
         │          │   data.source: ./data/xxx.csv        │   {"proj1":None,"proj2":None},
         │          │   + aidctl run -p proj1 proj2        │   mode="single")
         │          │   --mode single                      │ （引擎内部各读各自配置）
配置文件 │ 目录扫描 │ 同上                                │ 同上

─── 模式五：多项目 · 各项目多文件合并 · 项目异步并行运行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────────────
显式上传 │ 用户指定 │ aidctl run -p proj1:a.csv,b.csv      │ execute(project_file_map=
         │          │   proj2 --mode merge                 │   {"proj1":["a.csv","b.csv"],
         │          │ （proj1 指定文件合并，               │    "proj2":None},
         │          │  proj2 扫描合并）                    │   mode="merge")
配置文件 │ 具体文件 │ 各项目 config.yaml 中                │ execute(project_file_map=
         │          │   data.source 为文件列表             │   {"proj1":None,"proj2":None},
         │          │   + aidctl run -p proj1 proj2        │   mode="merge")
         │          │   --mode merge                       │
配置文件 │ 目录扫描 │ 同上                                │ 同上

─── 模式六：多项目 · 各项目多文件异步并行 · 项目间同步串行 ───

前端方式 │ 读取形式 │ 用户操作                             │ 引擎入口
─────────┼──────────┼──────────────────────────────────────┼──────────────────────────────────────
显式上传 │ 用户指定 │ aidctl run -p proj1:a.csv,b.csv      │ execute(project_file_map=
         │          │   proj2 --mode parallel              │   {"proj1":["a.csv","b.csv"],
         │          │ （proj1 指定文件异步并行，           │    "proj2":None},
         │          │  proj2 扫描异步并行）                │   mode="parallel")
配置文件 │ 具体文件 │ 各项目 config.yaml 中                │ execute(project_file_map=
         │          │   data.source 为文件列表             │   {"proj1":None,"proj2":None},
         │          │   + aidctl run -p proj1 proj2        │   mode="parallel")
         │          │   --mode parallel                    │
配置文件 │ 目录扫描 │ 同上                                │ 同上
"""

# ═══════════════════════════════════════════════════════════════════
# 4. 多项目文件映射语法
# ═══════════════════════════════════════════════════════════════════

PROJECT_FILE_MAP_SYNTAX: str = """
多项目文件映射语法。

当用户需要为多项目模式下的每个项目指定不同的文件时，
使用以下语法：

    -p 项目名:文件1,文件2 项目名:文件1,文件2 ...

    示例：
        aidctl run -p proj1:data/a.csv,data/b.csv proj2:data/c.csv --mode merge
        含义：proj1 的 a.csv 和 b.csv 合并后执行预测，
              proj2 的 c.csv 单独执行预测。

    解析规则：
        1. 如果参数包含 ':' → ':' 前是项目名，后是文件路径（逗号分隔）。
        2. 如果参数不包含 ':' → 参数整体是项目名，文件由框架扫描项目目录。
        3. 文件路径相对于项目根目录（projects/项目名/）。

    引擎接口：
        execute(
            project_file_map={
                "proj1": ["data/a.csv", "data/b.csv"],
                "proj2": None,  # None 表示框架扫描
            },
            mode="merge",
        )
"""

# ═══════════════════════════════════════════════════════════════════
# 文件元信息
# ═══════════════════════════════════════════════════════════════════

__all__: list[str] = [
    "FRONTEND_BACKEND_ROLES",
    "DATA_UPLOAD_PATHWAYS",
    "RUN_MODE_MATRIX",
    "PROJECT_FILE_MAP_SYNTAX",
]

__version__: str = "0.2.5"
__framework__: str = "AIDDForecast"
__description__: str = (
    "AIDDForecast 框架前后端交互契约文件。"
    "定义前端（WEB 端 / CLI）与后端（引擎 / 调度器）之间的"
    "完整交互逻辑，包括数据上传途径、六种运行模式矩阵和"
    "多项目文件映射语法。"
)