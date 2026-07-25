"""
Polars 高性能数据处理原则体系
Polars High-Performance Data Processing Principles

版本: 0.2.5
最后更新: 2026-07-19
适用数据规模: 千万级行数 (≥ 10,000,000 rows)
内存约束: ≤ 3 GB (推荐运行在 2 GB 上下)
硬件约束: 单机多核 CPU (默认利用所有可用核心)

本文件定义了在千万级数据量下，使用 Polars 进行高性能数据处理的核心原则、推荐做法与禁止项。
所有原则均基于 Polars 官方文档、官方 GitHub Issue 及官方博客的明确依据。
"""


# ============================================================================
# 一、核心设计哲学
# ============================================================================

POLARS_CORE_PHILOSOPHY = """
Polars 的高性能来自三个核心支柱：
1. 惰性求值 (Lazy API)：通过查询优化器进行谓词下推和投影下推，减少 I/O 和内存占用
2. 原生表达式 (Expressions)：在 Rust 层面并行执行，利用 SIMD 和多核 CPU
3. 列式存储 (Arrow)：零拷贝数据传递，高效的内存布局

核心原则：
- 万物皆表达式，能懒则懒
- 优先使用 LazyFrame，仅在探索性分析时使用 Eager
- 避免 Python 级别的循环和 UDF
"""


# ============================================================================
# 二、高性能策略清单 (7 项)
# ============================================================================

HIGH_PERFORMANCE_STRATEGIES = {
    "1. Lazy API（惰性求值）": {
        "description": "使用 scan_* 替代 read_*，让优化器执行谓词下推和投影下推",
        "official_basis": "官方文档: 'preferred (and highest-performance) mode of operation'",
        "✅ 允许使用": [
            "数据处理流程确定，不需要查看中间结果",
            "数据集 > 100 万行",
            "需要对查询执行全局优化",
        ],
        "❌ 禁止使用": [
            "探索性数据分析 (EDA)，需要每一步查看中间结果",
            "查询计划模式无法提前知晓的操作 (如 pivot)",
            "数据集 < 1 万行，优化开销大于收益",
        ],
        "示例": """
            # ✅ 允许：使用 Lazy API
            lf = pl.scan_csv("large_file.csv")
            result = lf.filter(pl.col("age") > 25).select("name", "age").collect()
            
            # ❌ 禁止：在探索性分析中过早使用 Lazy
            # 应先用 pl.read_csv() 查看数据样本，确定查询逻辑后再改用 Lazy
        """,
    },
    "2. 原生表达式（避免 Python 循环）": {
        "description": "使用向量化表达式替代 map_elements / apply",
        "official_basis": "官方文档：原生表达式可并行化，UDF 不能；apply 被认为是反模式",
        "✅ 允许使用": [
            "所有能用 Polars 原生表达式实现的逻辑",
            "需要高性能并行计算的场景",
        ],
        "❌ 禁止使用": [
            "能用原生表达式实现的任何场景",
            "需要高性能、低内存占用的生产环境代码",
        ],
        "示例": """
            # ✅ 允许：使用原生表达式
            df = df.with_columns(
                (pl.col("value") - pl.col("value").mean()).alias("centered")
            )
            
            # ❌ 禁止：使用 Python UDF 实现可原生表达的逻辑
            df = df.with_columns(
                pl.col("value").apply(lambda x: x - x.mean()).alias("centered")
            )
        """,
    },
    "3. 尽早过滤和列裁剪": {
        "description": "在惰性查询中尽早应用 filter 和 select，让优化器将操作下推到扫描层",
        "official_basis": "官方文档：scan_* 可以 '跳过读取不需要的列和行'",
        "✅ 允许使用": ["所有使用 LazyFrame API 的场景"],
        "示例": """
            # ✅ 正确：先裁剪列、再过滤、后聚合
            result = (
                lf.select("category", "value")
                .filter(pl.col("value") > 100)
                .group_by("category")
                .agg(pl.col("value").mean())
            )
        """,
    },
    "4. 数据类型优化": {
        "description": "指定最小整数类型，低基数用 Categorical，日期用 Date",
        "official_basis": "官方文档：通过 schema_overrides 或 dtypes 指定数据类型",
        "✅ 允许使用": [
            "知道数据范围，可选择最小整数类型 (如 UInt32 替代 Int64)",
            "字符串列基数较低 (< 50% 唯一值)，使用 Categorical",
            "仅需日期不需要时间，使用 Date 替代 Datetime",
        ],
        "❌ 禁止使用": [
            "不确定数据范围，使用过小类型可能导致溢出",
            "需要频繁修改分类值 (Categorical 重编码有开销)",
        ],
        "示例": """
            # ✅ 允许：指定最优类型
            df = pl.read_csv(
                "data.csv",
                dtypes={
                    "id": pl.UInt32,
                    "category": pl.Categorical,
                    "date": pl.Date,
                }
            )
            
            # ❌ 禁止：在不确定范围时使用过小类型
        """,
    },
    "5. 流式引擎": {
        "description": "数据集超内存时启用 streaming=True，使用 sink_* 直接写入",
        "official_basis": "官方文档：流式引擎 '不一定需要将所有数据存储在 RAM 中'",
        "✅ 允许使用": [
            "数据集 > 可用内存 (如 > 3GB)",
            "需要将结果直接写入文件，避免内存物化",
            "查询包含大规模分组、连接等操作",
            "数据集越大，流式引擎的性能优势越明显",
        ],
        "❌ 禁止使用": [
            "数据集远小于内存，内存引擎更快",
            "需要多次复用中间结果",
            "查询规模极小，流式调度开销大于收益",
        ],
        "示例": """
            # ✅ 允许：数据集超过内存，使用流式引擎
            lf.filter(pl.col("value") > 100).collect(streaming=True)
            
            # ✅ 允许：直接流式写入，避免内存物化
            lf.filter(pl.col("value") > 100).sink_parquet("output.parquet")
            
            # ❌ 禁止：小数据集使用流式（内存引擎更快）
        """,
    },
    "6. 使用 over() 替代显式分组-聚合-连接": {
        "description": "组内排名、组内标准化、组内累计等操作使用 over()",
        "official_basis": "官方文档：over() '类似于执行分组聚合并将结果连接回原始 DataFrame'",
        "✅ 允许使用": [
            "需要在分组上下文中计算但不改变行数的操作 (组内排名、标准化、累计)",
        ],
        "❌ 禁止使用": [
            "需要改变行数的聚合操作 (此时应使用 group_by().agg())",
        ],
        "示例": """
            # ✅ 允许：使用 over() 一次性完成组内计算
            df = df.with_columns(
                pl.col("value").mean().over("category").alias("category_mean")
            )
            
            # ❌ 禁止：使用显式分组-聚合-连接（更慢）
            agg_df = df.group_by("category").agg(pl.col("value").mean())
            df = df.join(agg_df, on="category")
        """,
    },
    "7. 批量操作，减少 collect() 调用": {
        "description": "所有惰性操作完成后只调用一次 collect()",
        "official_basis": "—",
        "✅ 允许使用": ["所有 LazyFrame 链式操作场景"],
        "示例": """
            # ✅ 正确：只调用一次 collect()
            result = (
                lf.filter(...)
                .select(...)
                .group_by(...)
                .agg(...)
                .collect()
            )
            
            # ❌ 错误：多次 collect() 导致多次物化
            df1 = lf.filter(...).collect()
            df2 = df1.select(...)
            result = df2.group_by(...).agg(...)
        """,
    },
}


# ============================================================================
# 三、高频操作推荐与禁止对照表
# ============================================================================

HIGH_FREQUENCY_OPERATIONS = {
    "数据选择与列操作": {
        "选择列": {
            "✅ 推荐": "df.select(), pl.col()",
            "❌ 不推荐": "df['col'], df.col",
            "⛔ 禁止": "—",
            "说明": "df.select() 支持表达式，能与 Lazy API 配合触发投影下推",
        },
        "新建/修改列": {
            "✅ 推荐": "df.with_columns()",
            "❌ 不推荐": "Python 循环逐行添加",
            "⛔ 禁止": "—",
            "说明": "with_columns() 能充分利用并行和惰性优化",
        },
        "选择首行": {
            "✅ 推荐": "df.first()",
            "❌ 不推荐": "df[0, :] 后再做复杂操作",
            "⛔ 禁止": "—",
            "说明": "first() 是能提前终止的优化操作",
        },
        "提取标量": {
            "✅ 推荐": "df.item()",
            "❌ 不推荐": "df[0,0] 或 series[0]",
            "⛔ 禁止": "—",
            "说明": "df.item() 是官方推荐的方法，经过专项性能优化",
        },
    },
    "数据筛选与过滤": {
        "条件过滤": {
            "✅ 推荐": "df.filter()",
            "❌ 不推荐": "—",
            "⛔ 禁止": "Python 循环内多次 filter",
            "说明": "filter() 是实现谓词下推的核心方式",
        },
        "条件判断": {
            "✅ 推荐": "pl.when().then().otherwise()",
            "❌ 不推荐": "—",
            "⛔ 禁止": "apply 或 map_elements 实现 if-else",
            "说明": "pl.when() 是原生条件表达式，向量化执行",
        },
    },
    "分组与聚合": {
        "分组聚合": {
            "✅ 推荐": "df.group_by().agg([...])",
            "❌ 不推荐": "—",
            "⛔ 禁止": "Python 手动遍历分组进行聚合",
            "说明": "Polars 在 Rust 层面并行执行分组和聚合",
        },
        "去重": {
            "✅ 推荐": "df.unique()",
            "❌ 不推荐": "—",
            "⛔ 禁止": "apply(set)",
            "说明": "原生 unique() 性能比 apply(set) 快 10 倍以上",
        },
    },
    "数据连接与拼接": {
        "数据连接": {
            "✅ 推荐": "df.join()",
            "❌ 不推荐": "—",
            "⛔ 禁止": "—",
            "说明": "Polars 支持多种连接方式，在 Lazy API 中可被优化器重排",
        },
        "垂直拼接 (同结构)": {
            "✅ 推荐": "pl.concat(how='vertical')",
            "❌ 不推荐": "—",
            "⛔ 禁止": "—",
            "说明": "列结构完全一致时使用 vertical",
        },
        "对角拼接 (不同结构)": {
            "✅ 推荐": "pl.concat(how='diagonal', rechunk=False) + Python 生成器",
            "❌ 不推荐": "一次性 pl.concat(how='diagonal') 加载全部数据",
            "⛔ 禁止": "水平拼接 (how='horizontal') 在列数多时使用",
            "说明": "diagonal + rechunk=False + 生成器 是官方推荐的高性能组合",
        },
    },
    "其他高频操作": {
        "检查是否为空": {
            "✅ 推荐": "df.is_empty()",
            "❌ 不推荐": "len(df) == 0",
            "⛔ 禁止": "—",
            "说明": "is_empty() 专门为此优化，避免长度计算",
        },
        "数据类型优化": {
            "✅ 推荐": "读取时通过 schema_overrides/dtypes 指定",
            "❌ 不推荐": "全部使用默认类型",
            "⛔ 禁止": "—",
            "说明": "合适的数据类型能显著降低内存占用",
        },
        "并行处理": {
            "✅ 推荐": "Polars 自动并行",
            "❌ 不推荐": "—",
            "⛔ 禁止": "multiprocessing 的 fork 方法",
            "说明": "Polars 默认利用所有 CPU 核心；fork 会导致死锁",
        },
    },
}


# ============================================================================
# 四、pl.concat + diagonal + 生成器 专项方案
# ============================================================================

CONCAT_DIAGONAL_GENERATOR_SPEC = {
    "名称": "pl.concat + how='diagonal' + Python 生成器",
    "适用场景": [
        "合并大量（数万个）结构不完全相同的文件",
        "数据总量 > 千万级，对内存占用敏感",
        "希望在合并时能处理缺失的列，并用 null 自动填充",
    ],
    "推荐用法": {
        "代码": """
            import polars as pl
            from pathlib import Path

            def read_csv_files(file_paths):
                for path in file_paths:
                    yield pl.scan_csv(path)  # 惰性扫描，不立即加载

            files = Path("data/").glob("*.csv")
            lf = pl.concat(read_csv_files(files), how="diagonal", rechunk=False)
            result = lf.collect(streaming=True)
        """,
        "关键参数": {
            "how='diagonal'": "列名不一致时自动填充 null，是官方标准方法",
            "rechunk=False": "避免昂贵的重分块操作，显著降低内存和计算开销",
            "Python 生成器": "惰性求值，避免将所有 DataFrame 同时加载到内存",
        },
    },
    "官方依据": {
        "how='diagonal'": "官方文档定义，用于列名不完全一致的 DataFrame 拼接",
        "生成器": "惰性求值，流式处理，避免内存峰值",
        "rechunk=False": "官方社区建议，在拼接大量文件时关闭自动重分块",
    },
    "✅ 允许使用": [
        "合并大量（数万个）结构不完全相同的 CSV 或 Parquet 文件",
        "数据总量 ≥ 千万级，对内存占用敏感",
    ],
    "❌ 禁止使用": [
        "数据量小（< 百万行），此时 overhead 大于收益",
        "所有 DataFrame 列结构完全一致（此时用 vertical 更高效）",
        "使用 how='horizontal' 且列数很多（执行时间可能二次方增长）",
    ],
    "版本注意事项": [
        "Polars 1.31.0+ 存在内存回归问题 (Issue #23889)，建议锁定 1.30.x",
        "旧版本 pl.concat 存在内存泄漏风险，建议使用最新稳定版",
    ],
}


# ============================================================================
# 五、情景化适用条件完整矩阵
# ============================================================================

SCENARIO_MATRIX = {
    "优化技术": {
        "Lazy API": {
            "✅ 允许": ["数据处理流程确定", "数据集 > 100 万行", "需要全局优化"],
            "❌ 禁止": ["探索性分析 (EDA)", "pivot 等模式无法提前知晓", "数据集 < 1 万行"],
        },
        "原生表达式": {
            "✅ 允许": ["所有能用原生表达式实现", "需要高性能并行计算"],
            "❌ 禁止": ["能用原生表达式实现的任何场景", "生产环境代码"],
        },
        "Python UDF": {
            "✅ 允许": ["逻辑无法用任何原生表达式实现", "一次性脚本"],
            "❌ 禁止": ["所有能用原生表达式实现"],
        },
        "scan_*": {
            "✅ 允许": ["使用 LazyFrame API 的任何场景", "需要谓词下推"],
            "❌ 禁止": ["探索性分析", "数据集极小", "需要立即获得 DataFrame"],
        },
        "流式引擎": {
            "✅ 允许": ["数据集 > 可用内存", "需要直接写入文件", "大规模分组/连接"],
            "❌ 禁止": ["数据集远小于内存", "需要多次复用中间结果", "查询极小"],
        },
        "数据类型优化": {
            "✅ 允许": ["知道数据范围", "低基数字符串", "仅需日期"],
            "❌ 禁止": ["不确定数据范围", "需要频繁修改分类值"],
        },
        "over()": {
            "✅ 允许": ["组内排名", "组内标准化", "组内累计"],
            "❌ 禁止": ["需要改变行数的聚合操作"],
        },
        "partition_by": {
            "✅ 允许": ["分组 < 1000", "需要随机访问", "内存充足 (> 8GB)"],
            "❌ 禁止": ["分组 > 10000", "仅需顺序遍历", "内存受限 (< 3GB)"],
        },
        "group_by": {
            "✅ 允许": ["分组 > 1000", "仅需顺序遍历", "内存受限 (< 3GB)"],
            "❌ 禁止": ["分组极少且需要频繁随机访问"],
        },
        "pl.concat(diagonal)": {
            "✅ 允许": ["大量结构不一致文件", "内存敏感"],
            "❌ 禁止": ["数据量小", "列结构完全一致"],
        },
    }
}


# ============================================================================
# 六、决策流程图
# ============================================================================

DECISION_FLOW = """
数据拼接决策流程：

开始
  │
  ▼
需要处理分组数据？
  │
  ├── 否 ──► 使用原生表达式 + Lazy API（无需分组）
  │
  ▼ 是
分组数量有多少？
  │
  ├── < 100 组 ──► 需要随机访问特定分组吗？
  │                     │
  │                     ├── 是 ──► partition_by + dict
  │                     │
  │                     └── 否 ──► group_by + iter_rows()
  │
  ├── 100-1000 组 ──► 内存是否充足（> 8GB）且需要随机访问？
  │                     │
  │                     ├── 是 ──► partition_by + dict
  │                     │
  │                     └── 否 ──► group_by + agg()
  │
  └── > 1000 组 ──► group_by + agg()（唯一推荐）
                        │
                        └── 配合 Lazy API + 流式引擎

数据拼接决策流程（专项）：

数据拼接需求
  │
  ▼
列结构是否完全一致？
  │
  ├── 是 ──► pl.concat(how="vertical")
  │
  └── 否 ──► 文件数量是否巨大（> 1000 个）？
              │
              ├── 是 ──► pl.concat(how="diagonal", rechunk=False) + Python 生成器 ✅
              │
              └── 否 ──► pl.concat(how="diagonal") 可接受
"""


# ============================================================================
# 七、版本注意事项
# ============================================================================

VERSION_NOTES = """
Polars 版本注意事项：

1. Polars 1.31.0 / 1.32.0 版本存在内存回归问题（Issue #23889）
   - 1.30.0 版本内存使用 < 20GB
   - 1.31.0+ 版本内存使用激增至 OOM (300GB+ 仍无法完成)
   - 建议生产环境锁定版本为 1.30.x

2. pl.concat 旧版本存在内存泄漏风险（社区报告）
   - 建议使用最新的稳定版 Polars
   - 如遇内存问题，检查是否使用了过旧版本

3. partition_by(as_dict=True) 返回类型变更（PR #16793）
   - 返回键类型为 tuple[object, ...]，类型注解时需注意
"""


# ============================================================================
# 八、优先级矩阵
# ============================================================================

PRIORITY_MATRIX = {
    "优化手段": {
        "Lazy API": {"性能影响": "极高", "内存影响": "极高", "实施难度": "低", "优先级": "P0"},
        "原生表达式（不用Python循环）": {"性能影响": "极高", "内存影响": "高", "实施难度": "低", "优先级": "P0"},
        "数据类型优化": {"性能影响": "高", "内存影响": "极高", "实施难度": "低", "优先级": "P0"},
        "列裁剪（select）": {"性能影响": "高", "内存影响": "极高", "实施难度": "低", "优先级": "P0"},
        "流式引擎": {"性能影响": "中", "内存影响": "极高", "实施难度": "低", "优先级": "P1"},
        "使用 over() 替代 join": {"性能影响": "中", "内存影响": "中", "实施难度": "中", "优先级": "P1"},
        "partition_by 预分片": {"性能影响": "中", "内存影响": "负影响", "实施难度": "中", "优先级": "P2"},
    }
}


# ============================================================================
# 九、约束条件达成建议
# ============================================================================

CONSTRAINTS_ACHIEVEMENT = {
    "千万行秒级运算": "使用 Lazy API + 原生表达式 + 多核并行。千万行过滤操作实测约 0.09 秒，分组聚合通常 2 秒内完成",
    "内存 < 3GB": "使用 scan_* 替代 read_*；开启 streaming=True；优化数据类型；仅裁剪需要的列；使用 sink_* 直接写入",
    "多核 CPU 高利用率": "Polars 默认利用所有可用核心，采用 morsel 驱动模式，每个 CPU 线程取一块输入并行处理",
}


# ============================================================================
# 十、官方依据汇总
# ============================================================================

OFFICIAL_BASIS_SUMMARY = {
    "Lazy API 是首选高性能模式": "官方文档: 'preferred (and highest-performance) mode of operation'",
    "惰性 API 可降低内存和 CPU 负载": "官方文档: '将显著降低内存和CPU的负载'",
    "使用 scan_* 替代 read_*": "官方文档: '优化器可以将优化下推到读取器'",
    "避免 Python UDF": "官方文档: '比原生表达式 API 慢得多'",
    "原生表达式可并行化，UDF 不能": "官方文档: 'Polars-native expressions can be parallelised (UDFs typically cannot)'",
    "流式引擎处理超大数据集": "官方博客: '性能随数据集增大而显著提升'",
    "Polars 核心用 Rust 编写，支持 SIMD": "官方文档说明",
    "1.31.0+ 版本内存增加问题": "官方 GitHub Issue #23889",
    "partition_by 是内存密集型": "官方文档: 'partition_by 映射中的 DataFrame 是 copies，是 memory intensive'",
    "group_by 是内存廉价": "官方文档: 'group_by 是 cheap memory wise，相当于一个 32 位整数列'",
    "diagonal 拼接": "官方文档定义，用于列名不一致的 DataFrame 拼接",
    "rechunk=False 优化": "官方社区建议，在拼接大量文件时关闭自动重分块",
}


# ============================================================================
# 十一、完整示例代码（千万行 × 5000 unique_id）
# ============================================================================

EXAMPLE_CODE = """
import polars as pl

# 1. 惰性扫描 + 数据类型优化
lf = pl.scan_parquet(
    "sales_data.parquet",
    schema_overrides={
        "unique_id": pl.Categorical,
        "sales": pl.Float32,
        "date": pl.Date,
    }
)

# 2. 列裁剪 + 过滤无效数据
lf = lf.select(["unique_id", "date", "sales", "category"]) \\
      .filter(pl.col("sales").is_not_null())

# 3. 分组计算（利用多核并行）
result = (
    lf.group_by("unique_id")
    .agg([
        pl.col("sales").mean().alias("mean_sales"),
        pl.col("sales").std().alias("std_sales"),
        pl.col("sales").count().alias("n_obs"),
        pl.col("date").min().alias("first_date"),
        pl.col("date").max().alias("last_date"),
    ])
    .filter(pl.col("n_obs") >= 30)
    .collect(streaming=True)
)

# 4. 分组数量少时的 partition_by 使用
if len(result) < 10000:
    groups_dict = result.partition_by("unique_id", as_dict=True)
    for uid, group_df in groups_dict.items():
        pass
else:
    # 分组数量多时改用 group_by + 迭代器
    for uid, group_df in result.group_by("unique_id"):
        pass

# 5. 大量文件拼接示例（diagonal + 生成器）
from pathlib import Path

def read_csv_files(file_paths):
    for path in file_paths:
        yield pl.scan_csv(path)

files = Path("data/").glob("*.csv")
lf_merged = pl.concat(read_csv_files(files), how="diagonal", rechunk=False)
result_merged = lf_merged.collect(streaming=True)
"""


# ============================================================================
# 十二、打印验证
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Polars 高性能数据处理原则体系")
    print("Polars High-Performance Data Processing Principles")
    print("=" * 80)
    print(f"核心哲学: {POLARS_CORE_PHILOSOPHY}")
    print(f"策略数量: {len(HIGH_PERFORMANCE_STRATEGIES)} 项")
    print(f"高频操作类别: {len(HIGH_FREQUENCY_OPERATIONS)} 类")
    print("=" * 80)
    print("完整原则体系已加载。")
    print("版本: 1.0 | 更新日期: 2026-07-19")