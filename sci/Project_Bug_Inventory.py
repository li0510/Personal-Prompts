"""
供应链智能分析平台 — BUG 清单文件 (SCI_Bug_Inventory.py)

版本: 0.2.5
最后更新: 2026-07-24
项目: Supply-Chain-Intelligence (sci)

本文件记录了项目开发期间在子模式 B（追因式讨论）中发现并成功修复的全部 BUGs。
每条 BUG 包含结构化字段，具备可迁移、可复用、Skill 化属性，
可被 AI Agent 直接读取并作为代码生成的约束条件。

属性说明：
    - id: 唯一标识
    - title: 简要描述
    - category: 分类（Polars API / 性能 / 测试 / 业务逻辑 / 语法）
    - severity: 严重程度（高 / 中 / 低）
    - symptom: 错误现象
    - root_cause: 根因分析
    - fix: 修正方案
    - forbidden_pattern: 禁止重复的代码模式
    - applicable_principle: 违反的 Product_Principles 原则
    - migration_value: 可迁移价值（其他项目如何受益）

结构：
    1. Polars API 使用错误
    2. 性能陷阱
    3. 测试配置漂移
    4. 业务逻辑缺陷
    5. 语法错误
"""
from __future__ import annotations

from typing import Any

# ═══════════════════════════════════════════════════════════════════
# 一、Polars API 使用错误
# ═══════════════════════════════════════════════════════════════════

BUG_001: dict[str, Any] = {
    "id": "BUG-001",
    "title": "CSV 编码硬编码导致 UnicodeDecodeError",
    "category": "Polars API",
    "severity": "高",
    "symptom": (
        "UnicodeDecodeError: 'gbk' codec can't decode byte 0xac in position 34: "
        "illegal multibyte sequence"
    ),
    "root_cause": "CSV 文件实际编码为 UTF-8，但脚本硬编码 encoding='gbk'，未自动检测编码。",
    "fix": (
        "实现 detect_encoding() 函数，按优先级尝试 UTF-8 → UTF-8-sig → GBK → GB2312 → Latin-1。"
        "在 data_extractor.py 和 data_profiler.py 中使用编码自动检测替代硬编码。"
    ),
    "forbidden_pattern": "pl.read_csv(file_path, encoding='gbk') — 硬编码编码参数",
    "applicable_principle": "P44（优雅降级）、P45（透明告知）",
    "migration_value": "任何处理多来源 CSV 文件的 Polars 项目都应实现编码自动检测，避免硬编码。",
}

BUG_002: dict[str, Any] = {
    "id": "BUG-002",
    "title": "Series 对象误用 DataFrame 属性 .height",
    "category": "Polars API",
    "severity": "中",
    "symptom": "AttributeError: 'Series' object has no attribute 'height'",
    "root_cause": "在 data_profiler.py 类型推断部分对 Series 对象使用了 .height 属性。Series 没有 .height 属性，应使用 .len() 或 len(series)。",
    "fix": "将 non_null.height 改为 non_null.len()。",
    "forbidden_pattern": "series.height — Series 不支持此属性",
    "applicable_principle": "Polars 高频操作推荐与禁止对照表",
    "migration_value": "Polars 中 DataFrame 使用 .height，Series 使用 .len()，不可混用。",
}

BUG_003: dict[str, Any] = {
    "id": "BUG-003",
    "title": "scan_csv 编码参数不兼容 'utf-8'（带连字符）",
    "category": "Polars API",
    "severity": "高",
    "symptom": "ValueError: csv `encoding` must be one of {'utf8', 'utf8-lossy'}, got utf-8",
    "root_cause": "Polars 的 scan_csv() 仅接受 'utf8'/'utf8-lossy'，不接受带连字符的 'utf-8'。",
    "fix": "在 read_csv_lazy() 中增加编码映射：'utf-8'/'utf-8-sig' → 'utf8'，其他编码回退到 read_csv() + .lazy()。",
    "forbidden_pattern": "pl.scan_csv(file, encoding='utf-8') — 必须使用 'utf8'",
    "applicable_principle": "Polars 1.40+ API 兼容性",
    "migration_value": "升级到 Polars 1.40+ 时必须检查所有 scan_csv 的 encoding 参数。",
}

BUG_004: dict[str, Any] = {
    "id": "BUG-004",
    "title": "rename 使用整数索引作为键导致 TypeError",
    "category": "Polars API",
    "severity": "高",
    "symptom": "TypeError: 'int' object is not an instance of 'str' while processing 'existing'",
    "root_cause": "lf.rename(dict(enumerate(new_columns))) 使用整数 0,1,2... 作为旧列名键。Polars 1.40+ 要求 rename 的映射键必须是字符串。",
    "fix": "改为 dict(zip(old_columns, new_columns))，其中 old_columns 是 lf.collect_schema().names() 返回的字符串列表。",
    "forbidden_pattern": "lf.rename(dict(enumerate(new_columns))) — 禁止使用整数索引作为键",
    "applicable_principle": "Polars 1.40+ API 变更",
    "migration_value": "Polars 1.40+ 中所有 rename 操作必须使用字符串映射。",
}

BUG_005: dict[str, Any] = {
    "id": "BUG-005",
    "title": "全量 rename 导致 DuplicateError（重复列名）",
    "category": "Polars API",
    "severity": "高",
    "symptom": "polars.exceptions.DuplicateError: column '入库' is duplicate",
    "root_cause": "业务动作行中存在 32 个重复的'入库'/'出库'/'结存'列名。全量 rename 将 32 个不同的原始列映射到相同目标名，导致重复列。",
    "fix": "删除全量 rename。改用索引定位 + pl.col(original_columns[idx]).alias(field) 精确选择每个标准字段首次出现的列。",
    "forbidden_pattern": "对含重复值的表头行执行全量 rename",
    "applicable_principle": "P40（全局一致性）",
    "migration_value": "处理 ERP 导出的宽表时，业务动作行中常有重复列名，必须使用索引定位 + alias 而非全量 rename。",
}

BUG_006: dict[str, Any] = {
    "id": "BUG-006",
    "title": "Join 键类型不一致导致 SchemaError",
    "category": "Polars API",
    "severity": "高",
    "symptom": "SchemaError: datatypes of join keys don't match — cat vs str",
    "root_cause": "summary_df 的物料编码被转换为 Categorical 以优化性能，但 cross_validate 中 weekly_agg 的物料编码为 str。Polars 1.40+ 不允许跨类型 join。",
    "fix": "在 cross_validate 中 join 前将 summary_df 的物料编码转换为 pl.Utf8。",
    "forbidden_pattern": "Join 键类型不一致（Categorical vs str）",
    "applicable_principle": "Polars 1.40+ Join 键类型一致性",
    "migration_value": "使用 Categorical 优化后，Join 前必须确保双方键类型一致。",
}

BUG_007: dict[str, Any] = {
    "id": "BUG-007",
    "title": "Polars 1.40 中 .mean()/.sum() 返回 DataFrame 而非标量",
    "category": "Polars API",
    "severity": "中",
    "symptom": "TypeError: float() argument must be a string or a real number, not 'DataFrame'",
    "root_cause": "Polars 1.40 中 .mean()/.sum() 返回 DataFrame（单行单列），而非 Python 标量。需要使用 .item() 提取标量值。",
    "fix": "在 .mean()/.sum() 后添加 .item()：series.mean().item()。",
    "forbidden_pattern": "float(series.mean()) — 必须使用 .item() 提取标量",
    "applicable_principle": "Polars 1.40+ 标量提取",
    "migration_value": "升级 Polars 1.40+ 后，所有聚合函数返回 DataFrame，需通过 .item() 提取标量。",
}

BUG_008: dict[str, Any] = {
    "id": "BUG-008",
    "title": "Series.filter() 不接受表达式参数",
    "category": "Polars API",
    "severity": "高",
    "symptom": "TypeError: Series constructor called with unsupported type 'Expr'",
    "root_cause": "Polars 1.40 中 Series.filter() 只接受布尔 Series/列表，不接受 pl.col(...) > ... 表达式。表达式过滤应使用 DataFrame.filter()。",
    "fix": "将 merged['周转率'].filter(pl.col('周转率') > 0) 改为 merged.filter(pl.col('周转率') > 0)['周转率']。",
    "forbidden_pattern": "series.filter(pl.col(...) > ...) — 表达式过滤必须使用 DataFrame",
    "applicable_principle": "Polars 1.40+ Series vs DataFrame API 区分",
    "migration_value": "Polars 1.40+ 中 Series 和 DataFrame 的 filter 参数类型不同，不可混用。",
}

BUG_009: dict[str, Any] = {
    "id": "BUG-009",
    "title": "str.strip_chars() 空参数导致 InvalidOperationError",
    "category": "Polars API",
    "severity": "高",
    "symptom": "InvalidOperationError: `bitor` operation not supported for dtype `str`",
    "root_cause": "在 _build_exclusion_mask 中使用 str.strip_chars() == '' 和 str.strip_chars() != ''，Polars 1.40 中此方法无参数时行为异常。且 Python 运算符优先级导致 `|` 在 `==` 之前计算，引发类型推导错误。",
    "fix": "用括号显式包裹 `==` 比较表达式以提升优先级。",
    "forbidden_pattern": "str.strip_chars() 不带参数 + 运算符优先级未用括号显式控制",
    "applicable_principle": "Python 运算符优先级 + Polars 1.40+ API 兼容性",
    "migration_value": "Polars 表达式链中，Python 比较运算符（==/!=）的优先级低于按位运算符（|/&），必须用括号显式控制。",
}

# ═══════════════════════════════════════════════════════════════════
# 二、性能陷阱
# ═══════════════════════════════════════════════════════════════════

BUG_010: dict[str, Any] = {
    "id": "BUG-010",
    "title": "逐物料 filter 全表导致 O(n²) 性能陷阱",
    "category": "性能",
    "severity": "高",
    "symptom": (
        "对 5,000 SKU × 52 万行的 weekly_df 逐物料执行 filter，"
        "耗时从 < 1 秒暴涨至 30+ 秒，企业级数据量下不可接受。"
    ),
    "root_cause": "在 demand_forecast.py 的 _holt_forecast、_detect_trend、_calculate_metrics 中对全表执行 weekly_df.filter(pl.col('物料编码') == code)，每个物料一次全表扫描，O(n²) 复杂度。",
    "fix": "使用 partition_by('物料编码', as_dict=True) 预分组为 dict，后续直接从 dict 取值，O(n) 复杂度。",
    "forbidden_pattern": (
        "for code in codes:\n"
        "    group = df.filter(pl.col('material_code') == code)  # O(n²) 陷阱"
    ),
    "applicable_principle": "Polars 策略 2（原生表达式）、策略 7（批量操作）",
    "migration_value": "任何需要逐物料计算的场景，必须先 partition_by 预分组，禁止逐物料 filter 全表。",
}

BUG_011: dict[str, Any] = {
    "id": "BUG-011",
    "title": "多次 collect() 导致多次物化",
    "category": "性能",
    "severity": "高",
    "symptom": "extract_weekly() 对 31 个日期块分别执行 collect()，宽表解析耗时显著增加。",
    "root_cause": "对每个日期块执行 lf.select(...).collect()，导致 31 次独立物化，未利用 Polars 的惰性优化。",
    "fix": "将所有日期块的 select 表达式合并为单次 collect()，一次性提取所有需要的列，然后在内存中构建长表。",
    "forbidden_pattern": "for block in daily_blocks: block.collect() — 多次 collect 导致多次物化",
    "applicable_principle": "Polars 策略 7（批量操作，减少 collect() 调用）",
    "migration_value": "任何宽表解析场景，必须将所有列选择合并为单次 collect，避免多次物化。",
}

BUG_012: dict[str, Any] = {
    "id": "BUG-012",
    "title": "多指标聚合使用分离的 .sum()/.mean() 导致多次全表扫描",
    "category": "性能",
    "severity": "中",
    "symptom": "inventory_turnover.py 中多次调用 merged['结存数量'].sum()、merged['周转率'].mean()，每次调用一次全表扫描。",
    "root_cause": "对同一 DataFrame 分离调用 .sum()/.mean()/.filter().mean()，未使用一次 select 并行计算所有标量。",
    "fix": "使用 df.select([Expr1, Expr2, ...]) 一次 select 并行计算所有汇总标量，通过 .item() 提取各值。",
    "forbidden_pattern": "total = df['a'].sum(); avg = df['b'].mean() — 多次全表扫描",
    "applicable_principle": "Polars 策略 7（批量操作）+ 多指标一次 select 并行计算",
    "migration_value": "任何需要计算多个汇总指标的场景，必须合并为一次 select，避免多次全表扫描。",
}

BUG_013: dict[str, Any] = {
    "id": "BUG-013",
    "title": "concat_dataframes_stream 未使用生成器模式导致内存峰值",
    "category": "性能",
    "severity": "中",
    "symptom": "data_extractor.py 的 main() 中 _weekly_dfs 使用 list.append() 收集所有文件的周度数据后再传入 concat_dataframes_stream，多文件时内存峰值高。",
    "root_cause": "先收集所有 DataFrame 到列表，再传入拼接函数，导致内存中同时持有所有文件的 DataFrame。",
    "fix": "使用生成器 + next() + itertools.chain 模式，逐文件 yield DataFrame，避免列表中同时持有全部数据。",
    "forbidden_pattern": "dfs_list.append(df); pl.concat(dfs_list) — 内存峰值",
    "applicable_principle": "pl.concat + diagonal + 生成器 专项方案",
    "migration_value": "多文件拼接必须使用生成器模式，配合 next() + itertools.chain 实现流式处理。",
}

# ═══════════════════════════════════════════════════════════════════
# 三、测试配置漂移
# ═══════════════════════════════════════════════════════════════════

BUG_014: dict[str, Any] = {
    "id": "BUG-014",
    "title": "测试文件未同步更新导致配置漂移（--summary 参数缺失）",
    "category": "测试",
    "severity": "高",
    "symptom": "inventory_planning.py: error: the following arguments are required: --summary",
    "root_cause": "阶段 K 为 inventory_planning.py 新增了 --summary 必需参数，但 test_06、test_10、test_11 中调用该脚本的命令行未同步更新。",
    "fix": "在所有调用 inventory_planning.py 的测试文件中添加 --summary 参数，指向 extracted_summary.parquet。",
    "forbidden_pattern": "生产代码新增必需参数后未全局搜索更新所有调用点",
    "applicable_principle": "P33（输出完整性）、配置漂移预防",
    "migration_value": "任何生产代码的接口变更（新增必需参数、修改文件名等），必须全局搜索所有调用点（脚本、测试、文档）并同步更新。",
}

BUG_015: dict[str, Any] = {
    "id": "BUG-015",
    "title": "测试文件引用已废弃的输出文件名",
    "category": "测试",
    "severity": "高",
    "symptom": "AssertionError: 前置条件不满足: extracted_data.parquet 不存在",
    "root_cause": "阶段 A 将 data_extractor.py 的输出从 extracted_data.parquet 改为双输出（extracted_summary.parquet + extracted_weekly.parquet），但 test_02~07 仍引用旧文件名。",
    "fix": "全量更新测试文件中的文件名引用：extracted_data.parquet → extracted_summary.parquet 或 extracted_weekly.parquet。",
    "forbidden_pattern": "生产代码变更输出文件名后未全局搜索更新测试引用",
    "applicable_principle": "P33（输出完整性）、配置漂移预防",
    "migration_value": "生产代码的输出文件名变更必须在测试套件中全量搜索替换，确保无遗漏。",
}

# ═══════════════════════════════════════════════════════════════════
# 四、业务逻辑缺陷
# ═══════════════════════════════════════════════════════════════════

BUG_016: dict[str, Any] = {
    "id": "BUG-016",
    "title": "多行表头检测逻辑不完整",
    "category": "业务逻辑",
    "severity": "中",
    "symptom": "has_multi_header 返回 False（实际应为 True），导致 parse_wide_columns 识别 0 个日期块。",
    "root_cause": "原检测逻辑仅判断'多个包含标准字段的行'，未处理'第一个匹配行之前存在非空标题行'的模式。",
    "fix": "增加模式 B：检查第一个匹配行之前是否有非空且非数据的标题行。同时新增 parse_wide_columns 的双行解析（日期行 + 业务动作行）。",
    "forbidden_pattern": "仅检测'包含标准字段的行数 > 1'作为多行表头的判定条件",
    "applicable_principle": "P44（优雅降级）、业务场景完整性",
    "migration_value": "ERP 导出的表格常见多级表头（标题行 + 日期行 + 业务动作行），需要同时解析多行才能正确识别列结构。",
}

BUG_017: dict[str, Any] = {
    "id": "BUG-017",
    "title": "尾部合计行未被自动排除",
    "category": "业务逻辑",
    "severity": "中",
    "symptom": "error_report.json 中记录 6 项报错，合计行被当作普通物料处理，导致交叉验证失败。",
    "root_cause": "extract_from_file 仅通过 --data-start-row 指定数据起始行，未自动检测并排除尾部合计行。",
    "fix": "增加 _build_exclusion_mask 和 _record_excluded_rows，使用关键词检测（'合计'/'总计'/'小计'）+ 物料编码异常检测（非 GSN-XXXXX 格式）双重防线自动排除合计行。",
    "forbidden_pattern": "仅通过起始行号控制数据范围，不处理尾部合计行",
    "applicable_principle": "P44（优雅降级）、P45（透明告知）",
    "migration_value": "ERP 导出表格的尾部常见合计/汇总行，需要自动检测并排除，避免影响数据分析结果。",
}

BUG_018: dict[str, Any] = {
    "id": "BUG-018",
    "title": "Holt-Winters 乘法模型除零错误（间歇性需求碰撞）",
    "category": "业务逻辑",
    "severity": "高",
    "symptom": "ZeroDivisionError: float division by zero",
    "root_cause": "间歇性需求物料（大量零值周期）被误判为乘法模型，初始化季节指数为零，平滑迭代中分母为零。",
    "fix": "增加间歇性数据前置判断（零值占比 > 30% → 加法模型）+ 乘法模型更新中分母零值保护（max(divisor, 1e-10)）+ 后续引入 TSB/IMAPA 替代 Holt-Winters 处理间歇性/块状需求。",
    "forbidden_pattern": "将 Holt-Winters 乘法模型应用于零值占比 > 30% 的间歇性时序",
    "applicable_principle": "P44（优雅降级）、业务场景适配",
    "migration_value": "需求模式分类（ADI + CV²）应先于预测模型选择，间歇性需求应使用 TSB/IMAPA 而非 Holt-Winters。",
}

# ═══════════════════════════════════════════════════════════════════
# 五、语法错误
# ═══════════════════════════════════════════════════════════════════

BUG_019: dict[str, Any] = {
    "id": "BUG-019",
    "title": "global 声明在变量使用之后（重复犯错）",
    "category": "语法",
    "severity": "高",
    "symptom": "SyntaxError: name 'DEFAULT_SEED' is used prior to global declaration",
    "root_cause": "parser.add_argument(default=DEFAULT_SEED) 在 global DEFAULT_SEED 声明之前引用了模块常量。这是 Python 语法规则：global 声明必须在所有同名变量使用之前。",
    "fix": "消除 global 声明，改为函数参数传递种子值。",
    "forbidden_pattern": "def main():\n    parser.add_argument(default=MODULE_CONSTANT)\n    ...\n    global MODULE_CONSTANT  # ❌ global 在使用之后",
    "applicable_principle": "P5（避免 global 修改模块常量）",
    "migration_value": "Python 中 global 声明必须在变量首次使用之前。更优方案是通过函数参数传递而非修改模块常量。",
}

BUG_020: dict[str, Any] = {
    "id": "BUG-020",
    "title": "global DEFAULT_IMAPA_MAX_WINDOW 重复 BUG-019 错误",
    "category": "语法",
    "severity": "高",
    "symptom": "SyntaxError: name 'DEFAULT_IMAPA_MAX_WINDOW' is used prior to global declaration",
    "root_cause": "与 BUG-019 完全相同的错误模式——parser.add_argument(default=DEFAULT_IMAPA_MAX_WINDOW) 在 global 声明之前引用模块常量。",
    "fix": "消除 global 声明，改为函数参数传递 imapa_max_window。",
    "forbidden_pattern": "同 BUG-019",
    "applicable_principle": "P5（避免 global 修改模块常量）+ BUG-019 的教训未被吸收",
    "migration_value": "同一错误模式的重复出现说明需要将 BUG-019 列为代码审查检查项。",
}

# ═══════════════════════════════════════════════════════════════════
# 六、统计清单
# ═══════════════════════════════════════════════════════════════════

BUG_INVENTORY_STATS: dict[str, int | dict[str, int | str] | str] = {
    "total_bugs": 20,
    "by_category": {
        "Polars API": 9,
        "性能": 4,
        "测试": 2,
        "业务逻辑": 3,
        "语法": 2,
    },
    "by_severity": {
        "高": 14,
        "中": 6,
        "低": 0,
    },
    "most_repeated_pattern": "global 声明在变量使用之后（BUG-019 和 BUG-020）",
    "most_impactful_category": "Polars API 使用错误（9 个，占 45%），主要源于 Polars 1.40 的 breaking changes",
}

__all__: list[str] = [
    "BUG_001", "BUG_002", "BUG_003", "BUG_004", "BUG_005",
    "BUG_006", "BUG_007", "BUG_008", "BUG_009", "BUG_010",
    "BUG_011", "BUG_012", "BUG_013", "BUG_014", "BUG_015",
    "BUG_016", "BUG_017", "BUG_018", "BUG_019", "BUG_020",
    "BUG_INVENTORY_STATS",
]

__version__: str = "0.2.5"
__description__: str = (
    "供应链智能分析平台（Supply-Chain-Intelligence）"
    "项目开发期间全部 BUGs 的结构化清单。"
    "包含 20 个已修复 BUGs，按类别（Polars API / 性能 / 测试 / 业务逻辑 / 语法）组织。"
    "每条 BUG 包含禁止模式，可直接作为 AI Agent 的代码生成约束条件。"
)

# ═══════════════════════════════════════════════════════════════════
# 打印验证
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 80)
    print("供应链智能分析平台 — BUG 清单文件")
    print(f"版本: {__version__}")
    print(f"总 BUGs 数: {BUG_INVENTORY_STATS['total_bugs']}")
    print(f"分类: {BUG_INVENTORY_STATS['by_category']}")
    print(f"严重程度: {BUG_INVENTORY_STATS['by_severity']}")
    print(f"最常重复模式: {BUG_INVENTORY_STATS['most_repeated_pattern']}")
    print(f"最易出错类别: {BUG_INVENTORY_STATS['most_impactful_category']}")
    print("=" * 80)
    print("完整 BUGs 清单已加载。")