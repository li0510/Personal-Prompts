# Python 后端开发完整规范与 AI 约束全集

> **文档用途**：本文件整合了 Python 后端开发中**通用的最佳实践**与 **各特定库的专项约束**，是 AI 辅助编码的完整规范基线。AI 在生成或修改 Python 代码时，必须无条件遵守本文件中的所有 **✅ 允许** 和 **❌ 禁止** 指令。
>
> **适用技术栈**：Python 3.11+ | Nixtla 生态（NeuralForecast, MLForecast, StatsForecast, HierarchicalForecast, UtilsForecast, coreforecast）| SciPy | scikit-learn | NumPy | pandas | Polars | SQLAlchemy | Flask | Ray | Dask | Apache Spark | Optuna | FugueBackend
>
> **版本**：v3.0 | **更新日期**：2026-06


## 第一部分：通用 Python 约束条件（跨库通用）

> 本节规则适用于所有 Python 项目，无论是否使用特定库。它们是 Python 官方标准（PEP 8、PEP 257）及各大成熟开源项目的共同经验。

### 1. 通用命名规范

| 元素类型 | 命名风格 | 示例 | 备注 |
| :--- | :--- | :--- | :--- |
| **类 (Class)** | `CapWords` / `PascalCase` | `UserProfile`, `TimeSeriesForecaster` | 每个单词首字母大写，不使用下划线 |
| **函数 (Function)** | `snake_case` | `get_user_name()`, `calculate_average()` | 全小写，单词间用下划线分隔，使用祈使动词短语 |
| **方法 (Method)** | `snake_case` | `fit()`, `transform()`, `predict()` | 同函数规范，通常为动词或动词短语 |
| **变量 (Variable)** | `snake_case` | `user_id`, `total_amount` | 全小写，单词间用下划线分隔，命名应清晰表意 |
| **常量 (Constant)** | `ALL_CAPS_WITH_UNDERSCORES` | `MAX_RETRIES`, `DEFAULT_PORT` | 全部大写，单词间用下划线分隔 |
| **模块 (Module)** | `snake_case` | `forecast_engine.py` | 简短、全小写，可用下划线提高可读性 |
| **包 (Package)** | `lowercase` | `utils`, `models` | 简短、全小写，**不鼓励**使用下划线 |
| **私有属性/方法** | 前缀 `_` | `_internal_state`, `_update_cache()` | 单下划线开头，表明“仅供内部使用”的约定 |

**通用禁止项**：
- ❌ 禁止使用单字符变量名 `l`（小写 L）、`O`（大写 O）、`I`（大写 I）
- ❌ 禁止使用 Python 保留字作为标识符（`class`, `import`, `return`, `with` 等）
- ❌ 禁止使用内置函数或类型的名称作为变量名（如 `len`, `list`, `dict`, `sum`, `open`）
- ❌ 禁止在一个 `.py` 文件中放置多个公共类（推荐一个文件一个公共类）

### 2. 通用代码风格与布局

| 规则 | 说明 | 标准 |
| :--- | :--- | :--- |
| ✅ **DO** 使用 4 个空格进行缩进 | 禁止使用 Tab 键进行缩进 | PEP 8 |
| ✅ **DO** 限制行长度 | 注释和文档字符串：**72** 字符；代码：推荐 **79** 字符，可放宽至 **88-100** 字符 | PEP 8 |
| ✅ **DO** 顶级定义之间留 **2 个空行** | 模块级类和函数之间 | PEP 8 |
| ✅ **DO** 类内部方法之间留 **1 个空行** | 类内部的方法定义之间 | PEP 8 |
| ✅ **DO** 方法与其文档字符串之间**不留空行** | 文档字符串紧跟在 `def` 行之后 | PEP 257 |
| ✅ **DO** 将所有导入语句放在文件顶部 | 任何模块注释和文档字符串之后 | PEP 8 |
| ✅ **DO** 将导入分组并按顺序排列 | **标准库 → 第三方库 → 本地应用/库**，每组之间留一个空行 | PEP 8 |
| ✅ **DO** 优先使用**绝对导入** | `from package import module` | PEP 8 |
| ❌ **DO NOT** 混用 Tab 和空格 | 必须始终保持一致 | PEP 8 |
| ❌ **DO NOT** 在文档字符串前后留空行 | 除非是多行文档字符串的结尾 | PEP 257 |
| ❌ **DO NOT** 使用 `from module import *` | 严重污染命名空间，导致命名冲突且无法静态分析 | PEP 8 |

### 3. 通用异常处理规范

| 规则 | 说明 | 标准 |
| :--- | :--- | :--- |
| ✅ **DO** 捕获异常时**尽可能指定具体的异常类型** | 如 `ValueError`, `TypeError`, `KeyError`，避免使用裸露的 `except:` | PEP 8 |
| ✅ **DO** 保持 `try` 块**尽可能小** | 只包含可能引发异常的代码，提高可读性 | PEP 8 |
| ✅ **DO** 使用 `else` 子句 | 放置没有异常发生时应执行的代码 | PEP 8 |
| ✅ **DO** 使用 `finally` 子句 | 放置无论是否发生异常都必须执行的代码（如资源清理） | PEP 8 |
| ✅ **DO** 遵循 **EAFP** 风格 | “Easier to Ask for Forgiveness than Permission.” 尽可能“直接尝试执行”并捕获异常 | Python 惯用法 |
| ✅ **DO** 遵循 **“Raise low, catch high”** 原则 | 在底层函数中抛出异常，在上层调用处统一捕获和处理 | 通用最佳实践 |
| ✅ **DO** 使用 `raise ... from` 保留异常链 | `raise NewError("...") from original_exception` 确保调试信息完整 | Python 3 |
| ❌ **DO NOT** 使用裸露的 `except:` | 会意外捕获 `SystemExit` 和 `KeyboardInterrupt`，导致程序无法正常退出 | PEP 8 |
| ❌ **DO NOT** 捕获异常后**什么都不做**（空 `except` 块） | 会掩盖错误，导致难以排查的 Bug | PEP 8 |
| ❌ **DO NOT** 在 `finally` 中使用 `return` 或 `break` | 会覆盖 `try`/`except` 块中的返回值，造成混乱 | PEP 8 |
| ❌ **DO NOT** 将异常用于常规的控制流 | 异常应仅用于错误信号，而非替代条件语句 | 通用最佳实践 |
| ❌ **DO NOT** 使用 `assert` 进行参数验证 | `assert` 在 Python 优化模式 (`-O`) 下会被禁用，导致安全检查失效 | 通用最佳实践 |
| ✅ **DO** 为项目定义专用的异常基类 | 通常命名为 `[ProjectName]Error` | 通用最佳实践 |
| ✅ **DO** 为不同类别的错误定义具体的异常子类 | 如 `NetworkError`, `ValidationError`, `NotFoundError` | 通用最佳实践 |
| ❌ **DO NOT** 直接抛出 `Exception` 基类 | 应使用更具体的异常类型 | 通用最佳实践 |

### 4. 通用测试标准

| 规则 | 说明 |
| :--- | :--- |
| ✅ **DO** 使用 **pytest** 框架编写测试 | Python 社区最主流的测试框架 |
| ✅ **DO** 新功能或 Bug 修复必须附带单元测试 | 确保代码质量和防止回归 |
| ✅ **DO** 在提交前运行所有测试 | 确保新代码不会破坏现有功能 |
| ❌ **DO NOT** 提交未通过测试的代码 | 破坏主分支稳定性 |

### 5. 通用文档与注释规范

| 规则 | 说明 |
| :--- | :--- |
| ✅ **DO** 为所有公共模块、类、方法、函数编写文档字符串 | 描述用途、参数、返回值和可能引发的异常 |
| ✅ **DO** 使用 **三重双引号** `"""` 包围文档字符串 | 统一风格 |
| ✅ **DO** 使用 **numpydoc** 风格的文档字符串 | 所有大型科学计算和数据处理项目都采用此标准 |
| ❌ **DO NOT** 省略公共 API 的文档字符串 | 这是判断代码质量的重要标准 |

### 6. 通用向后兼容性标准

| 规则 | 说明 |
| :--- | :--- |
| ✅ **DO** 非向后兼容的 API 更改**仅**在 **MAJOR** 版本中引入 | 遵循语义化版本规范 (SemVer) |
| ✅ **DO** 弃用 API 在 **MINOR** 版本中引入 | 通过 `DeprecationWarning` 发出警告 |
| ✅ **DO** 弃用功能应至少保留 **2 个次要版本** | 给用户充足的迁移时间 |
| ❌ **DO NOT** 在 PATCH 版本中引入新的弃用 | 修补版本应只包含错误修复 |
| ❌ **DO NOT** 忽略 `DeprecationWarning` | 代码将在未来版本中断 |

### 7. 通用项目协作与贡献标准

| 规则 | 说明 |
| :--- | :--- |
| ✅ **DO** 使用 **Black** 进行代码格式化 | PyData 项目事实标准 |
| ✅ **DO** 使用 **isort** 进行导入排序 | 与 Black 配合使用 |
| ✅ **DO** 使用 **Flake8** 进行代码风格检查 | 捕获常见错误和风格问题 |
| ✅ **DO** 使用 **pre-commit** 钩子 | 在提交前自动运行格式化和检查工具 |
| ✅ **DO** 使用 **mypy** 进行类型检查（PEP 484） | 大型项目应尽可能使用类型提示 |
| ✅ **DO** 为新功能或 Bug 修复提供文档（如适用） | 用户文档与代码同等重要 |
| ✅ **DO** 提交 Pull Request 前，先在 Issue 中讨论设计（如适用） | 避免 PR 被拒绝或做无用功 |
| ❌ **DO NOT** 将大型更改放在单个 PR 中 | 应分解为小的、单一目的的补丁 |
| ❌ **DO NOT** 提交不相关的代码更改（如格式化已有文件） | 保持 PR 聚焦于描述的范围 |


## 第二部分：特定库专项约束条件

> 本节规则针对特定库的官方规范，在使用这些库时必须叠加遵守。

### 8. Nixtla 时序预测生态专项

#### 8.1 NeuralForecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `NeuralForecast` 类实例化模型列表 |
| ✅ **DO** | 使用 `AutoModel` 类进行自动化超参数优化 |
| ✅ **DO** | 在 `BaseAuto` 中通过 `config` 字典定义超参数搜索空间 |
| ✅ **DO** | 使用 `predict(level=...)` 生成预测区间 |
| ❌ **DO NOT** | 不要跳过数据的时间均匀采样要求 |
| ❌ **DO NOT** | 不要在 `AutoModel` 中手动实现优化算法 |

#### 8.2 MLForecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 输入数据**必须**包含 `unique_id`、`ds`、`y` 三列 |
| ✅ **DO** | 使用 `lag_transforms` 字典定义滞后特征转换 |
| ✅ **DO** | 传入 scikit-learn 兼容的 estimators |
| ❌ **DO NOT** | 不要传入缺少必需三列的数据框 |
| ❌ **DO NOT** | 不要在预测时使用与训练时不同的特征结构 |

#### 8.3 StatsForecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `StatsForecast.fit` 拟合统计模型 |
| ✅ **DO** | 使用 `StatsForecast.predict` 进行预测 |

#### 8.4 HierarchicalForecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 reconciled 方法处理层级时序数据 |
| ❌ **DO NOT** | 不要在不考虑层级结构的情况下直接聚合预测 |

#### 8.5 UtilsForecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `utilsforecast.losses` 中的标准损失函数进行评估 |

#### 8.6 coreforecast
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `GroupedArray` 作为核心数据结构，包含 `data` 和 `indptr` 两个 1D NumPy 数组 |
| ✅ **DO** | 使用 `Lag`、`RollingMean`、`RollingStd` 等滞后变换 |
| ✅ **DO** | 使用 `SeasonalRollingMean`、`SeasonalRollingStd` 等季节性滚动变换 |
| ✅ **DO** | 使用 `LocalStandardScaler` 进行局部标准化 |
| ✅ **DO** | **在需要高性能分组运算时，优先考虑使用 coreforecast 替代原生 NumPy** |
| ❌ **DO NOT** | 不要混用不同变换的 `lag` 和 `window_size` 参数 |
| ❌ **DO NOT** | 不要在 `indptr` 中使用非递增或越界的索引值 |
| ❌ **DO NOT** | 不要在不理解 `GroupedArray` 结构的情况下直接使用 coreforecast |

### 9. SciPy 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 遵循 PEP-8 与 PEP-257 标准 |
| ✅ **DO** | 使用 Sphinx + numpydoc 扩展编写文档字符串 |
| ✅ **DO** | 对于参数较多的新函数，在 `*` 后使用显式关键字参数 |
| ❌ **DO NOT** | 不要返回 `tuple`、`namedtuple` 或 `bunch` 作为多元素返回值 |

### 10. scikit-learn 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 所有 estimator **必须**继承 `BaseEstimator` |
| ✅ **DO** | 使用 `check_array` 验证传入的类数组参数 |
| ✅ **DO** | 在 `fit` 中设置的公共属性**必须**以字母开头并以单下划线结尾 |
| ✅ **DO** | 公共 API 中不以下划线 `_` 开头的所有对象都应保持向后兼容 |
| ✅ **DO** | 使用 `sklearn.exceptions` 中的自定义异常类（`NotFittedError`, `ConvergenceWarning` 等） |
| ❌ **DO NOT** | 不要使用 `np.asanyarray` 或 `np.atleast_2d`（会让 `np.matrix` 通过） |
| ❌ **DO NOT** | **不要在任何情况下使用 `import *`** |
| ❌ **DO NOT** | 不要修改或移除公共 API 而不经过**两个发布周期**的弃用警告 |
| ❌ **DO NOT** | 不要返回 `pandas.Series` 作为 `predict()` 的输出 |

### 11. NumPy 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `import numpy as np` |
| ✅ **DO** | 遵循 NumPy 文档字符串标准 |
| ❌ **DO NOT** | 不要使用 `import scipy as sp`（使用完整名称） |

### 12. pandas 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 遵循 **PEP8** 标准，使用 **Black** 和 **Flake8** |
| ✅ **DO** | 强烈鼓励使用 **PEP 484 风格的类型提示** |
| ✅ **DO** | API 破坏性更改**仅**在 **major** 版本中发生 |
| ✅ **DO** | 弃用在 **minor** 版本中引入，在 **major** 版本中强制执行 |
| ❌ **DO NOT** | 不要忽略 `DeprecationWarning`（代码将在未来版本中断） |

### 13. Polars 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 优先使用**表达式 API** |
| ✅ **DO** | 对大型数据集优先使用**惰性 API** |
| ✅ **DO** | 遵循**语义化版本控制规范** |
| ❌ **DO NOT** | 不要将 `Enum` 类型与 `Categorical` 混用 |

### 14. SQLAlchemy 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 坚持 **PEP8**，行宽为 **78 个字符** |
| ✅ **DO** | 使用 **Core**（SQL 表达式语言）或 **ORM**（对象关系映射） |
| ✅ **DO** | 使用 `Engine` 管理数据库连接和连接池 |
| ✅ **DO** | 使用 `SQLAlchemyError` 及其子类处理异常 |
| ❌ **DO NOT** | 不要在 ORM 中直接访问 `Engine` 和 `Connection` 对象 |
| ❌ **DO NOT** | 不要忽略 1.x 到 2.x 的迁移指南 |
| ❌ **DO NOT** | 不要在 `finally` 中返回内容（会覆盖异常） |

### 15. Flask 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 遵循 WSGI 规范（PEP 3333） |
| ✅ **DO** | 使用 **Black** 格式化代码 |
| ✅ **DO** | 使用 **pre-commit** 自动运行格式检查 |
| ✅ **DO** | 使用蓝图（Blueprint）组织路由 |
| ✅ **DO** | 使用应用工厂模式创建应用实例 |
| ✅ **DO** | 使用 `@app.errorhandler()` 注册错误处理函数 |
| ✅ **DO** | 使用 `abort()` 提前终止请求并返回 HTTP 错误码 |
| ❌ **DO NOT** | 不要在全局作用域中创建应用实例 |
| ❌ **DO NOT** | 不要在 Flask 应用中依赖默认的错误页面 |

### 16. Ray 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | Python 代码遵循 **Black** 代码风格 |
| ✅ **DO** | 公共函数必须包含文档字符串和用法示例 |
| ✅ **DO** | 新功能或 bug 修复必须添加新的测试用例 |
| ✅ **DO** | 提交前运行 `pre-commit` 和 `pytest` |
| ✅ **DO** | 使用 `ray.get()` 时捕获 `RayTaskError` 异常 |
| ❌ **DO NOT** | 不要在文档中使用 `code-block:: python`（应使用 `testcode`） |
| ❌ **DO NOT** | 不要在分布式环境中忽略进程崩溃导致的任务失败 |

### 17. Dask 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | Dask 图使用普通的 Python 数据结构（字典、元组、函数）进行编码 |
| ✅ **DO** | 使用 `dask.Task` 类表示任务 |
| ✅ **DO** | 在每次 `compute` 调用中包含大量计算以提高并行性 |
| ❌ **DO NOT** | 不要使用旧的任务表示形式（元组形式），请改用 `dask.Task` 类 |
| ❌ **DO NOT** | 不要忽略 Worker 意外死亡的情况 |

### 18. Apache Spark (PySpark) 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | Python 代码遵循 **PEP 8** 标准 |
| ✅ **DO** | 遵循现有代码库的风格 |
| ✅ **DO** | 所有源文件应包含标准的 Apache 许可证头 |
| ✅ **DO** | 删除行尾空白字符 |
| ❌ **DO NOT** | 行长度限制为 **100 个字符**（而非 PEP 8 的 79 个字符） |
| ❌ **DO NOT** | 编辑现有代码时，不要引入与文件现有风格不一致的样式 |

### 19. Optuna 专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 编码风格使用 **flake8** 检查 |
| ✅ **DO** | 代码使用 **black** 格式化 |
| ✅ **DO** | 类型提示遵循 **PEP484**，使用 **mypy** 检查 |
| ✅ **DO** | 新功能必须附带文档（reStructuredText 格式） |
| ✅ **DO** | 新功能或 bug 修复必须编写充分的测试代码 |
| ✅ **DO** | 在提交 PR 前，先在 issue 中讨论设计 |
| ❌ **DO NOT** | 不要忽略贡献不仅限于 PR，还包括评论和讨论 |

### 20. FugueBackend（Nixtla 并行后端）专项
| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `FugueBackend` 类进行分布式计算，可在 Spark、Dask 和 Ray 之间切换而无需更改代码 |
| ✅ **DO** | 传入分布式 DataFrame 时，StatsForecast 会自动使用对应的引擎 |
| ✅ **DO** | 在运行 Ray 前，先在较小的 Pandas 数据集上测试以确保一切正常 |
| ✅ **DO** | 分布式 DataFrame 按分区处理，避免单个节点内存溢出 |
| ❌ **DO NOT** | 不要在使用分布式后端时忽略 `num_partitions` 参数的配置 |
| ❌ **DO NOT** | 不要在分布式环境中忽略库的安装——确保 `statsforecast` 库已安装在所有 worker 节点上 |


## 第三部分：AI 核心禁止项速查表（最高优先级）

> 以下为 AI 生成 Python 代码时必须**绝对避免**的全局错误，违反任意一条即视为不合格。

| 序号 | 禁止项 | 类别 | 说明 |
| :--- | :--- | :--- | :--- |
| 1 | **禁止使用裸露的 `except:`** | 异常处理 | 会意外捕获 `SystemExit` 和 `KeyboardInterrupt` |
| 2 | **禁止使用 `==` / `!=` 与 `None` 比较** | 代码风格 | 必须使用 `is` / `is not`，这是 PEP 8 的强制性要求 |
| 3 | **禁止使用 `from module import *`** | 导入规范 | 严重污染命名空间，导致代码混乱且难以调试 |
| 4 | **禁止使用单字符变量名 `l`, `O`, `I`** | 命名规范 | 与数字 1 和 0 难以区分，违反 PEP 8 |
| 5 | **禁止捕获异常后什么都不做** | 异常处理 | 空的 `except` 块会悄然掩盖错误，是代码异味 |
| 6 | **禁止在 `finally` 中使用 `return`** | 异常处理 | 覆盖 `try`/`except` 的返回值，导致逻辑错误 |
| 7 | **禁止使用 `assert` 进行参数验证** | 异常处理 | `assert` 在优化模式下会被禁用 |
| 8 | **禁止使用 Python 保留字或内置函数名作为变量名** | 命名规范 | 如 `class`, `list`, `dict`, `sum` |
| 9 | **禁止提交未通过测试的代码** | 测试 | 破坏主分支的稳定性 |
| 10 | **禁止省略公共 API 的文档字符串** | 文档 | 所有公共模块、类、函数都必须有文档 |
| 11 | **禁止修改或移除公共 API 而不经过两个发布周期的弃用** | 向后兼容 | 破坏向后兼容性 |
| 12 | **禁止在 MLForecast 中传入缺少必需列的数据** | Nixtla | 必须包含 `unique_id`、`ds`、`y` |
| 13 | **禁止在 ORM 中直接访问 `Engine` 对象** | SQLAlchemy | 应通过 ORM 公共 API 操作 |
| 14 | **禁止在分布式环境中忽略 Worker 失败** | Dask/Ray | 导致任务失败和资源泄漏 |
| 15 | **禁止使用旧的任务表示形式（元组形式）** | Dask | 已弃用，使用 `dask.Task` 类 |
| 16 | **禁止在文档中使用 `code-block:: python`** | Ray | 应使用 `testcode` |


## 第四部分：使用说明

1.  **AI 约束模式**：将本文档全文作为系统提示词，AI 必须严格遵循所有 ✅ DO 和 ❌ DO NOT 指令。
2.  **代码生成检查**：生成代码后，对照本文档进行自检，确保没有违反任何禁止项。
3.  **项目规范**：可直接作为团队编码规范文档使用。

---

**文档版本**：v0.2.5 | **更新日期**：2026-06