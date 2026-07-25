"""
Polars 企业级应用契约
Polars Enterprise-Grade Application Contract

版本: 0.2.5
最后更新: 2026-07-22
适用数据规模: 千万级行数 (≥ 10,000,000 rows)
内存约束: ≤ 3 GB (推荐运行在 2 GB 上下)
硬件约束: 单机多核 CPU (默认利用所有可用核心)
验证基准: 10,000 SKU × 260 周 = 2,600,000 行周度数据

本文件是供应链智能分析平台（sci）项目在开发过程中，
基于 Polars 1.40+ 的实践经验总结提炼出的企业级应用契约。
它既包含 Polars 官方的通用高性能原则，也包含本项目在千万级
数据量下遭遇并修复的所有性能陷阱和 API 使用错误的解决方案。
任何使用 Polars 进行企业级数据处理的开发者，在阅读本文件后，
应能避免上述已发生的错误，并遵循本文件的约束条件进行开发。

契约定义：
    违反本文件中任何标记为 "⛔ 禁止" 的条款，将导致运行时错误
    或严重性能退化（已在 sci 项目中通过 19+ 个测试用例验证）。

本文件结构：
    一、核心设计哲学
    二、高性能策略清单 (7 项)
    三、高频操作推荐与禁止对照表（含 sci 项目补充的 6 条新原则）
    四、pl.concat + diagonal + 生成器 专项方案
    五、情景化适用条件完整矩阵
    六、决策流程图
    七、版本注意事项
    八、优先级矩阵
    九、约束条件达成建议
    十、官方依据汇总
    十一、完整示例代码
    十二、打印验证
    十三、CSV 编码自动检测专项方案 [NEW]
    十四、企业级 ERP 导出文件解析专项方案 [NEW]
    十五、企业级数据量压力测试基准 [NEW]
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
        "description": "使用向量化表达式替代 map_elements / apply。"
                       "所有自定义函数必须包含防御性列存在检查和数据完备性验证。",
        "official_basis": "官方文档：原生表达式可并行化，UDF 不能；apply 被认为是反模式",
        "✅ 允许使用": [
            "所有能用 Polars 原生表达式实现的逻辑",
            "需要高性能并行计算的场景",
            "对预分组的 DataFrame 进行逐物料计算时，必须先从 dict 取值，不得对全表执行 filter",
        ],
        "❌ 禁止使用": [
            "能用原生表达式实现的任何场景",
            "需要高性能、低内存占用的生产环境代码",
            "对大规模 DataFrame 逐物料执行 filter 操作（O(n²) 性能陷阱）",
        ],
        "示例": """
            # ✅ 允许：使用原生表达式
            df = df.with_columns(
                (pl.col("value") - pl.col("value").mean()).alias("centered")
            )
            
            # ✅ 允许：预分组后从 dict 取值
            groups = df.partition_by("material_code", as_dict=True)
            for code, group_df in groups.items():
                if "target_col" not in group_df.columns:
                    continue  # 防御性列存在检查
                result = group_df["target_col"].mean()
            
            # ❌ 禁止：使用 Python UDF 实现可原生表达的逻辑
            df = df.with_columns(
                pl.col("value").apply(lambda x: x - x.mean()).alias("centered")
            )
            
            # ❌ 禁止：逐物料 filter 全表（O(n²) 性能陷阱）
            for code in codes:
                group = df.filter(pl.col("material_code") == code)  # 每次扫描全表
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
        "description": "数据集超内存时启用 engine='streaming'，使用 sink_* 直接写入。"
                       "Polars 1.25.0+ 中 streaming=True 已弃用，必须使用 engine='streaming'。",
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
            "使用 streaming=True 参数（Polars 1.25.0+ 已弃用）",
        ],
        "示例": """
            # ✅ 允许：数据集超过内存，使用流式引擎
            lf.filter(pl.col("value") > 100).collect(engine="streaming")
            
            # ✅ 允许：直接流式写入，避免内存物化
            lf.filter(pl.col("value") > 100).sink_parquet("output.parquet")
            
            # ❌ 禁止：小数据集使用流式（内存引擎更快）
            
            # ❌ 禁止：使用 streaming=True（Polars 1.25.0+ 已弃用）
            # lf.collect(streaming=True)
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
        "description": "所有惰性操作完成后只调用一次 collect()。"
                       "多指标聚合使用一次 select 并行计算所有标量，避免多次全表扫描。",
        "official_basis": "—",
        "✅ 允许使用": [
            "所有 LazyFrame 链式操作场景",
            "多指标聚合使用 DataFrame.select([Expr1, Expr2, ...]).item() 模式一次扫描完成",
        ],
        "❌ 禁止使用": [
            "多次 collect() 导致多次物化",
            "对同一 DataFrame 分离调用 .sum()、.mean()、.n_unique() 等造成多次全表扫描",
        ],
        "示例": """
            # ✅ 正确：只调用一次 collect()
            result = (
                lf.filter(...)
                .select(...)
                .group_by(...)
                .agg(...)
                .collect()
            )
            
            # ✅ 正确：一次 select 并行计算所有标量
            stats = df.select([
                pl.col("sales").sum().alias("total"),
                pl.col("sales").mean().alias("avg"),
                pl.col("id").n_unique().alias("count"),
            ])
            total = stats["total"].item()
            avg = stats["avg"].item()
            count = stats["count"].item()
            
            # ❌ 错误：多次 collect() 导致多次物化
            df1 = lf.filter(...).collect()
            df2 = df1.select(...)
            result = df2.group_by(...).agg(...)
            
            # ❌ 错误：分离调用导致多次全表扫描
            total = df["sales"].sum()
            avg = df["sales"].mean()
            count = df["id"].n_unique()
        """,
    },
}


# ============================================================================
# 三、高频操作推荐与禁止对照表（含 sci 项目补充）
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
        "重命名列": {
            "✅ 推荐": "df.rename(dict(zip(old_names, new_names))) — 使用字符串映射",
            "❌ 不推荐": "—",
            "⛔ 禁止": "df.rename(dict(enumerate(new_names))) — 使用整数索引作为键",
            "说明": "Polars 1.40+ 要求 rename 的映射键必须是字符串，使用 enumerate 产生整数键将导致 TypeError",
        },
        "选择首行": {
            "✅ 推荐": "df.first()",
            "❌ 不推荐": "df[0, :] 后再做复杂操作",
            "⛔ 禁止": "—",
            "说明": "first() 是能提前终止的优化操作",
        },
        "提取标量": {
            "✅ 推荐": "df.item() 或 series.item()",
            "❌ 不推荐": "df[0,0] 或 series[0]",
            "⛔ 禁止": "—",
            "说明": "Polars 1.40+ 中 .mean()/.sum() 等聚合函数返回 DataFrame，必须使用 .item() 转换为 Python 标量",
        },
        "DataFrame vs Series API 区分": {
            "✅ 推荐": "DataFrame.height, Series.len()",
            "❌ 不推荐": "—",
            "⛔ 禁止": "Series.height（Series 没有 height 属性）",
            "说明": "DataFrame 使用 .height 获取行数，Series 使用 .len() 或 len(series) 获取长度",
        },
    },
    "数据筛选与过滤": {
        "条件过滤": {
            "✅ 推荐": "df.filter() — DataFrame 级别过滤",
            "❌ 不推荐": "—",
            "⛔ 禁止": [
                "Python 循环内多次 filter",
                "series.filter(pl.col(...) > ...) — Series.filter() 不接受表达式参数（Polars 1.40+）",
            ],
            "说明": "DataFrame.filter() 接受表达式参数，是实现谓词下推的核心方式。"
                     "Series.filter() 只接受布尔 Series 或布尔列表。",
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
        "分组预提取": {
            "✅ 推荐": "df.partition_by('col', as_dict=True) — 适用于需要随机访问特定分组且分组数 ≤ 10,000",
            "❌ 不推荐": "逐物料 df.filter(pl.col('code') == x) — O(n²) 性能陷阱",
            "⛔ 禁止": "先 group_by().agg() 提取 key，再逐物料 filter 全表",
            "说明": "partition_by 内部基于 Arrow 零拷贝分区，一次遍历完成全部分组。"
                     "返回 dict 后直接从 dict 取值，无需再次扫描全表。",
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
            "✅ 推荐": "df.join() — 确保 join 键类型一致（如统一转为 pl.Utf8）",
            "❌ 不推荐": "—",
            "⛔ 禁止": "跨类型 join（如 Categorical vs str）— Polars 1.40+ 不允许",
            "说明": "Polars 支持多种连接方式，在 Lazy API 中可被优化器重排。"
                     "join 前必须确保键的类型完全一致。",
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
        "防御性列存在检查": {
            "✅ 推荐": "在任何可能接收空 DataFrame 或异构 Schema 的函数开头检查列存在性",
            "❌ 不推荐": "假设传入的 DataFrame 始终包含所需的列",
            "⛔ 禁止": "不检查列存在性就直接访问 df['col_name']",
            "说明": "当使用 partition_by + dict 模式时，某些 key 可能对应空 DataFrame。"
                     "必须在访问列前检查 'col_name' in df.columns",
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
            from itertools import chain
            from typing import Iterable, Literal

            def concat_dataframes_stream(
                dfs: Iterable[pl.DataFrame],
                how: Literal["diagonal"] = "diagonal",
                rechunk: bool = False,
            ) -> pl.DataFrame | None:
                '''
                流式拼接 DataFrame 序列，避免内存峰值。
                使用 next() + itertools.chain 模式，逐个消费 DataFrame 传入 pl.concat。
                '''
                stream = (df for df in dfs if df is not None)
                try:
                    first_df = next(stream)
                except StopIteration:
                    return None
                return pl.concat(chain([first_df], stream), how=how, rechunk=rechunk)
        """,
        "关键参数": {
            "how='diagonal'": "列名不一致时自动填充 null，是官方标准方法",
            "rechunk=False": "避免昂贵的重分块操作，显著降低内存和计算开销",
            "next() + itertools.chain": "标准范式：先取出第一个元素，再用 chain 拼接剩余生成器",
        },
    },
    "官方依据": {
        "how='diagonal'": "官方文档定义，用于列名不完全一致的 DataFrame 拼接",
        "生成器": "惰性求值，流式处理，避免内存峰值",
        "rechunk=False": "官方社区建议，在拼接大量文件时关闭自动重分块",
        "next() + chain": "sci 项目实践验证，避免将全部 DataFrame 同时加载到内存",
    },
    "✅ 允许使用": [
        "合并大量（数万个）结构不完全相同的 CSV 或 Parquet 文件",
        "数据总量 ≥ 千万级，对内存占用敏感",
    ],
    "❌ 禁止使用": [
        "数据量小（< 百万行），此时 overhead 大于收益",
        "所有 DataFrame 列结构完全一致（此时用 vertical 更高效）",
        "使用 how='horizontal' 且列数很多（执行时间可能二次方增长）",
        "使用 list.append() 收集所有 DataFrame 后再传入 pl.concat()（内存峰值）",
    ],
    "版本注意事项": [
        "推荐使用 Polars 1.40+，已验证 concat_dataframes_stream 稳定运行",
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
            "✅ 允许": ["分组 ≤ 10,000", "需要随机访问", "内存充足 (> 8GB)"],
            "❌ 禁止": ["分组 > 10,000", "仅需顺序遍历", "内存受限 (< 3GB)"],
        },
        "group_by": {
            "✅ 允许": ["分组 > 10,000", "仅需顺序遍历", "内存受限 (< 3GB)"],
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
  ├── 100-10,000 组 ──► 内存是否充足（> 8GB）且需要随机访问？
  │                     │
  │                     ├── 是 ──► partition_by + dict
  │                     │
  │                     └── 否 ──► group_by + agg()
  │
  └── > 10,000 组 ──► group_by + agg()（唯一推荐）
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
              ├── 是 ──► concat_dataframes_stream + diagonal + rechunk=False ✅
              │
              └── 否 ──► pl.concat(how="diagonal") 可接受
"""


# ============================================================================
# 七、版本注意事项
# ============================================================================

VERSION_NOTES = """
Polars 版本注意事项（基于 Polars 1.40.1 实践验证）：

1. Polars 1.25.0+ 弃用 streaming=True 参数
   - 必须使用 engine="streaming" 替代
   - 使用 streaming=True 将触发 DeprecationWarning

2. Polars 1.40+ API 重大变更（sci 项目实战验证）：
   - rename 映射键必须是字符串，使用整数索引将导致 TypeError
   - .mean()/.sum() 等聚合函数返回 DataFrame，需使用 .item() 提取标量
   - Series.filter() 不接受表达式参数，只接受布尔 Series/列表
   - DataFrame.filter() 接受表达式参数，保持不变
   - join 键类型必须完全一致（Categorical vs str 不允许）
   - partition_by(as_dict=True) 返回 dict[tuple, DataFrame]，键为 tuple 类型
   - scan_csv encoding 参数仅接受 'utf8'/'utf8-lossy'，不接受 'utf-8'（带连字符）

3. 推荐生产环境使用 Polars 1.40+ 稳定版
   - 已验证 19+ 个测试用例在 1.40.1 下全部通过
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
        "一次 select 多指标并行计算": {"性能影响": "高", "内存影响": "中", "实施难度": "低", "优先级": "P1"},
        "concat_dataframes_stream 流式拼接": {"性能影响": "高", "内存影响": "极高", "实施难度": "低", "优先级": "P0"},
    }
}


# ============================================================================
# 九、约束条件达成建议
# ============================================================================

CONSTRAINTS_ACHIEVEMENT = {
    "千万行秒级运算": "使用 Lazy API + 原生表达式 + 多核并行。千万行过滤操作实测约 0.09 秒，分组聚合通常 2 秒内完成",
    "内存 < 3GB": "使用 scan_* 替代 read_*；开启 engine='streaming'；优化数据类型；仅裁剪需要的列；使用 sink_* 直接写入",
    "多核 CPU 高利用率": "Polars 默认利用所有可用核心，采用 morsel 驱动模式，每个 CPU 线程取一块输入并行处理",
    "10,000 SKU × 260 周压力测试": "sci 项目验证：demand_forecast < 5s, inventory_planning < 5s, inventory_alert < 3s, xyz_classifier < 2s",
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
    "partition_by 是内存密集型": "官方文档: 'partition_by 映射中的 DataFrame 是 copies，是 memory intensive'",
    "group_by 是内存廉价": "官方文档: 'group_by 是 cheap memory wise，相当于一个 32 位整数列'",
    "diagonal 拼接": "官方文档定义，用于列名不一致的 DataFrame 拼接",
    "rechunk=False 优化": "官方社区建议，在拼接大量文件时关闭自动重分块",
    "Polars 1.40+ API 变更": "sci 项目 19+ 测试用例实战验证",
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
    .collect(engine="streaming")
)

# 4. 分组数量少时的 partition_by 使用
if len(result) < 10000:
    groups_dict = result.partition_by("unique_id", as_dict=True)
    for uid, group_df in groups_dict.items():
        # 防御性列存在检查
        if "sales" not in group_df.columns:
            continue
        avg = group_df["sales"].mean()
else:
    # 分组数量多时改用 group_by + 迭代器
    for uid, group_df in result.group_by("unique_id"):
        pass

# 5. 大量文件拼接示例（diagonal + 生成器 + next/chain）
from itertools import chain
from pathlib import Path

def concat_dataframes_stream(dfs):
    stream = (df for df in dfs if df is not None)
    try:
        first_df = next(stream)
    except StopIteration:
        return None
    return pl.concat(chain([first_df], stream), how="diagonal", rechunk=False)

files = Path("data/").glob("*.csv")
lf_merged = pl.concat(
    concat_dataframes_stream(pl.scan_csv(f) for f in files),
    how="diagonal",
    rechunk=False,
)
result_merged = lf_merged.collect(engine="streaming")
"""


# ============================================================================
# 十二、打印验证
# ============================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("Polars 企业级应用契约")
    print("Polars Enterprise-Grade Application Contract")
    print("=" * 80)
    print(f"核心哲学: {POLARS_CORE_PHILOSOPHY}")
    print(f"策略数量: {len(HIGH_PERFORMANCE_STRATEGIES)} 项")
    print(f"高频操作类别: {len(HIGH_FREQUENCY_OPERATIONS)} 类")
    print("=" * 80)
    print("完整原则体系已加载。")
    print("版本: 2.0.0 | 更新日期: 2026-07-22")
    print("基于 Polars 1.40.1 + sci 项目 19+ 测试用例实战验证")


# ============================================================================
# 十三、CSV 编码自动检测专项方案 [NEW]
# ============================================================================

CSV_ENCODING_DETECTION_SPEC = {
    "名称": "CSV 编码自动检测 + Polars API 编码兼容",
    "适用场景": [
        "用户提供的 CSV 文件编码未知（GBK/UTF-8/UTF-8-BOM/Latin-1）",
        "需要自动适配编码，避免手动指定或硬编码",
    ],
    "核心原则": {
        "检测顺序": "UTF-8 → UTF-8-sig → GBK → GB2312 → Latin-1（按使用频率排序）",
        "scan_csv 编码映射": "UTF-8/UTF-8-sig → 'utf8'；GBK/GB2312 → 'gbk'；Latin-1 → 'latin-1'",
        "回退策略": "如果 scan_csv 不支持检测到的编码，回退到 read_csv() + .lazy()，并输出警告建议用户转换文件为 UTF-8",
    },
    "推荐用法": {
        "代码": """
            import polars as pl
            from pathlib import Path

            ENCODING_CANDIDATES = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin-1"]

            def detect_encoding(file_path: Path) -> str:
                for encoding in ENCODING_CANDIDATES:
                    try:
                        _ = pl.read_csv(file_path, encoding=encoding, separator=",",
                                        has_header=False, n_rows=100,
                                        truncate_ragged_lines=True)
                        return encoding
                    except (UnicodeDecodeError, Exception):
                        continue
                raise ValueError(f"无法自动检测文件编码。已尝试: {ENCODING_CANDIDATES}")
        """,
    },
    "✅ 允许使用": [
        "用户提供的 CSV 文件编码未知时",
        "需要处理来自不同 ERP 系统的导出文件时",
    ],
    "❌ 禁止使用": [
        "硬编码 encoding='gbk' 或 encoding='utf-8'",
        "在 scan_csv 中直接传入 'utf-8'（带连字符）— 必须映射为 'utf8'",
    ],
    "sci 项目 BUG 关联": "BUG #1 (UnicodeDecodeError) + BUG #4 (scan_csv encoding ValueError)",
}


# ============================================================================
# 十四、企业级 ERP 导出文件解析专项方案 [NEW]
# ============================================================================

ERP_FILE_PARSING_SPEC = {
    "名称": "企业级 ERP 导出文件解析方案",
    "适用场景": [
        "ERP 系统导出的宽表格式库存明细表（日度数据横向展开）",
        "多级表头（第 0 行为日期/标签行，第 1 行为业务动作行）",
        "业务动作行中存在大量重复值（如 32 个'入库'列）",
        "尾部包含合计行或筛选求和行",
    ],
    "核心原则": {
        "多级表头解析": "同时读取第 0 行（日期/标签行）和第 1 行（业务动作行），结合两者识别每日三元组（入库/出库/结存）",
        "禁止全量重命名": "业务动作行中存在大量重复值，全量重命名会导致 DuplicateError。必须使用索引定位 + pl.col(original_columns[idx]).alias(field) 精确选择列",
        "日期标签提取": "Polars 读取 CSV 时可能将日期转为 datetime 字符串（'2021-09-01 00:00:00'），需要 _extract_date_label() 函数统一转换为 'M/D' 格式",
        "合并单元格处理": "使用 fill_null(strategy='forward') 向前填充",
    },
    "推荐用法": {
        "代码": """
            # 同时读取日期行（第 0 行）和业务动作行（第 1 行）
            header_df = pl.read_csv(file_path, encoding=encoding, separator=",",
                                    has_header=False, n_rows=2,
                                    truncate_ragged_lines=True)
            date_row = [str(c) if c is not None else "" for c in header_df.row(0)]
            action_row = [str(c) if c is not None else f"col_{i}" for i, c in enumerate(header_df.row(1))]
            
            # 不执行全量重命名！使用索引定位选择列
            original_columns = lf.collect_schema().names()
            select_exprs = []
            for field in STANDARD_FIELDS:
                target_name = column_mapping[field]
                for idx, name in enumerate(action_row):
                    if name == target_name:
                        select_exprs.append(pl.col(original_columns[idx]).alias(field))
                        break  # 只取首次出现的列
            lf = lf.select(select_exprs)
        """,
    },
    "✅ 允许使用": [
        "SAP/金蝶/用友/浪潮等 ERP 系统导出的多级表头宽表",
        "业务动作行中存在重复列名的场景",
    ],
    "❌ 禁止使用": [
        "对业务动作行执行全量 rename（将导致 DuplicateError）",
        "硬编码列索引（不同 ERP 的列顺序可能不同）",
        "忽略第 0 行日期信息（将导致 parse_wide_columns 识别 0 个日期块）",
    ],
    "sci 项目 BUG 关联": "BUG #3 (多行表头) + BUG #5 (rename 整数键) + BUG #6 (DuplicateError) + BUG #12 (日期标签提取)",
}


# ============================================================================
# 十五、企业级数据量压力测试基准 [NEW]
# ============================================================================

STRESS_TEST_BENCHMARK = {
    "名称": "企业级数据量压力测试基准",
    "适用场景": [
        "验证核心分析脚本在接近真实企业数据量下的性能和稳定性",
        "作为持续集成/持续交付（CI/CD）流水线中的性能回归测试",
    ],
    "基准配置": {
        "SKU 数量": "10,000（可配置）",
        "周数": "260（可配置，约 5 年数据）",
        "总数据量": "10,000 × 260 = 2,600,000 行周度数据",
        "数据生成方式": "使用 generate_stress_data.py 生成模拟数据（正态分布，平衡校验通过）",
        "硬件参考": "M1 Pro, 8 CPUs, 16 GB RAM",
        "随机种子": "42（确保可复现）",
    },
    "性能阈值": {
        "demand_forecast.py": "< 5 秒",
        "inventory_planning.py": "< 5 秒",
        "inventory_alert.py": "< 3 秒",
        "xyz_classifier.py": "< 2 秒",
        "全链路端到端": "< 120 秒",
    },
    "验证项": [
        "所有脚本 returncode == 0",
        "产出文件行数 = 10,000 SKU",
        "执行时间在阈值内",
        "平衡校验通过率 100%",
    ],
    "可复现性": "使用固定随机种子（--seed 42）确保每次生成的数据完全一致。"
                 "两次运行生成的 Parquet 文件 MD5 哈希应一致。",
    "sci 项目 BUG 关联": "BUG #10 (SyntaxError global) + BUG #13 (测试数据量不足)",
}