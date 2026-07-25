# Vue 3 官方标准与规范完整清单（AI 约束版）

> 本文档依据 Vue 3 官方文档（https://vuejs.org）整理，专为 AI 辅助编码设计。每个标准都附有明确的 **允许（DO）** 和 **禁止（DO NOT）** 指令，请严格遵守。违反禁止项将导致代码不符合官方规范。
>
> **版本说明**：Vue 3（v3.5+） | 最后更新：2026-06

---

## 一、核心框架标准

### 1.1 应用实例（Application API）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `createApp()` 创建应用实例，使用 `app.mount()` 挂载到 DOM 容器 |
| ✅ **DO** | 使用 `app.component()` 注册全局组件（仅在必要时） |
| ✅ **DO** | 使用 `app.use()` 安装插件 |
| ✅ **DO** | 使用 `app.provide()` 进行依赖注入（应用级） |
| ❌ **DO NOT** | 不要使用 `new Vue()` 或 `Vue.extend()`（这是 Vue 2 的 API） |
| ❌ **DO NOT** | 不要直接操作 `app.config` 以外的内部属性 |
| ❌ **DO NOT** | 不要在 `app.mount()` 之后修改 `app.config` |

### 1.2 组合式 API（Composition API）

#### 响应式核心（Reactivity Core）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `ref()` 包装基本类型和对象，使用 `.value` 访问和修改 |
| ✅ **DO** | 使用 `reactive()` 包装对象（不适用于基本类型） |
| ✅ **DO** | 使用 `computed()` 创建计算属性，确保是纯函数 |
| ✅ **DO** | 使用 `watch()` 监听特定数据源变化 |
| ✅ **DO** | 使用 `watchEffect()` 自动追踪依赖并执行副作用 |
| ❌ **DO NOT** | 不要在 `watch()` 或 `watchEffect()` 中直接修改被监听的数据（避免无限循环） |
| ❌ **DO NOT** | 不要对 `reactive` 对象进行解构赋值（会丢失响应性） |
| ❌ **DO NOT** | 不要在 `ref` 或 `reactive` 中存储函数或 DOM 元素 |
| ❌ **DO NOT** | 不要使用 `reactive` 包装 `ref` 对象（会导致嵌套问题） |

#### 生命周期钩子（Lifecycle Hooks）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 在 `onMounted` 中执行 DOM 操作、数据获取 |
| ✅ **DO** | 在 `onBeforeUnmount` 中清理定时器、取消订阅、移除事件监听 |
| ✅ **DO** | 在 `onErrorCaptured` 中捕获并处理子组件错误 |
| ❌ **DO NOT** | 不要在 `onMounted` 中使用 `await` 而不处理错误 |
| ❌ **DO NOT** | 不要在 `onBeforeUnmount` 中执行耗时操作 |
| ❌ **DO NOT** | 不要忘记在 `onBeforeUnmount` 中清理副作用（导致内存泄漏） |

#### 依赖注入（Dependency Injection）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `provide()` 提供依赖，使用 `inject()` 注入依赖 |
| ✅ **DO** | 为 `inject` 提供默认值或使用 `undefined` 检查 |
| ❌ **DO NOT** | 不要修改注入的响应式数据（除非通过提供的函数） |
| ❌ **DO NOT** | 不要直接注入非响应式对象并在组件中修改它 |

### 1.3 选项式 API（Options API）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `data` 选项定义响应式状态（必须返回对象） |
| ✅ **DO** | 使用 `computed` 选项定义计算属性 |
| ✅ **DO** | 使用 `methods` 选项定义方法 |
| ✅ **DO** | 使用 `props` 选项声明接收的属性 |
| ✅ **DO** | 使用 `emits` 选项声明触发的事件 |
| ❌ **DO NOT** | 不要在 `data` 中直接定义箭头函数（`this` 绑定问题） |
| ❌ **DO NOT** | 不要在 `computed` 中进行异步操作 |
| ❌ **DO NOT** | 不要在 `methods` 中修改 `props`（单向数据流） |
| ❌ **DO NOT** | 不要在 `watch` 中直接修改被监听的数据（容易造成死循环） |

### 1.4 内置指令（Built-in Directives）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `v-if` / `v-else-if` / `v-else` 条件渲染 |
| ✅ **DO** | 使用 `v-for` 遍历数组或对象，**必须同时使用 `key`** |
| ✅ **DO** | 使用 `v-bind`（`:`）动态绑定属性 |
| ✅ **DO** | 使用 `v-on`（`@`）绑定事件 |
| ✅ **DO** | 使用 `v-model` 实现双向数据绑定（表单元素） |
| ❌ **DO NOT** | **禁止在同一个元素上同时使用 `v-if` 和 `v-for`**（优先级问题，应使用计算属性过滤） |
| ❌ **DO NOT** | 不要在 `v-for` 中省略 `key`（导致渲染错误） |
| ❌ **DO NOT** | 不要在 `v-for` 中使用 `index` 作为 `key`（如果列表顺序会变化） |
| ❌ **DO NOT** | 不要在 `v-if` / `v-else` 链中绑定相同的 `key` |
| ❌ **DO NOT** | 不要使用 `v-html` 渲染用户提供的 HTML（XSS 风险） |
| ❌ **DO NOT** | 不要在模板中使用复杂表达式（应提取为计算属性） |

### 1.5 特殊属性（Special Attributes）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 在 `v-for` 中始终使用 `:key` |
| ✅ **DO** | 使用 `ref` 获取 DOM 元素或子组件实例 |
| ✅ **DO** | 使用 `is` 属性渲染动态组件 |
| ❌ **DO NOT** | 不要在 `v-for` 中使用 `key` 但值不是唯一标识符 |
| ❌ **DO NOT** | 不要在组件上使用 `ref` 且期望获得 DOM 元素（应使用 `$el`） |

### 1.6 单文件组件（SFC, Single-File Component）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 文件扩展名必须为 `.vue` |
| ✅ **DO** | 在 `<script setup>` 中直接使用组合式 API（推荐） |
| ✅ **DO** | 使用 `<style scoped>` 限定样式作用域 |
| ✅ **DO** | 使用 `<style module>` 进行 CSS Modules |
| ❌ **DO NOT** | 不要在 `.vue` 文件中使用多个 `<script>` 块（除非是 `<script setup>` + `<script>`） |
| ❌ **DO NOT** | 不要在 `<style>` 中使用 `@import` 导致额外请求（应使用 JS import） |
| ❌ **DO NOT** | 不要在 `<style scoped>` 中使用深层选择器 `>>>` 或 `/deep/`（已废弃，改用 `:deep()`） |

---

## 二、生态系统标准

### 2.1 官方路由库（Vue Router 4.x）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `createRouter()` 和 `createWebHistory()` 创建路由实例 |
| ✅ **DO** | 使用 `<RouterView>` 渲染匹配的组件 |
| ✅ **DO** | 使用 `<RouterLink>` 进行导航 |
| ✅ **DO** | 使用 `useRouter()` 和 `useRoute()` 获取路由信息 |
| ❌ **DO NOT** | 不要在组件中直接操作 `this.$router` 或 `this.$route`（如果使用组合式 API） |
| ❌ **DO NOT** | 不要在路由守卫中重复请求数据（应结合 `onBeforeRouteUpdate`） |
| ❌ **DO NOT** | 不要忽略路由参数变化时的组件重用（应使用 `watch` 监听 `route.params`） |

### 2.2 官方状态管理库（Pinia）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `defineStore()` 定义 store，返回 `useStore()` 函数 |
| ✅ **DO** | 在 store 中使用 `state`、`getters`、`actions` 组织逻辑 |
| ✅ **DO** | 使用 `storeToRefs()` 解构响应式状态 |
| ❌ **DO NOT** | 不要在组件中直接修改 `store.state`（应通过 `store.$patch` 或 `actions`） |
| ❌ **DO NOT** | 不要将整个 store 对象解构（会丢失响应性） |
| ❌ **DO NOT** | 不要在 actions 中执行副作用而不进行错误处理 |

### 2.3 官方构建工具（Vite）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `npm create vue@latest` 初始化项目 |
| ✅ **DO** | 使用 `vite.config.js` 自定义构建配置 |
| ✅ **DO** | 使用 `import.meta.env` 访问环境变量 |
| ❌ **DO NOT** | 不要使用 `require()` 引入模块（应使用 ES Module 语法） |
| ❌ **DO NOT** | 不要在 Vite 配置中使用 Node.js 特有的 API（除非使用 `@vitejs/plugin-node`） |

---

## 三、风格指南与代码规范（AI 约束重点）

### 3.1 优先级 A：必要的（Essential - 错误预防）

| 规则 | 允许（DO） | 禁止（DO NOT） |
|------|------------|----------------|
| **组件名使用 PascalCase** | ✅ 组件名始终使用 PascalCase（如 `UserProfile`） | ❌ 不要使用 kebab-case 或 snake_case 命名组件 |
| **组件名使用多个单词** | ✅ 除 `App` 根组件外，所有组件名必须由多个单词组成（如 `UserList`） | ❌ 不要使用单个单词命名组件（如 `User`） |
| **Prop 定义尽量详细** | ✅ 至少指定 `type`，建议添加 `required` 或 `default` | ❌ 不要只使用数组形式定义 props（`props: ['name']`） |
| **`v-for` 必须配合 `key`** | ✅ 始终为 `v-for` 提供唯一的 `:key` | ❌ **绝对禁止**省略 `key` |
| **避免 `v-if` 和 `v-for` 同时使用** | ✅ 使用计算属性过滤数据后再迭代 | ❌ **绝对禁止**在同一元素上同时使用 `v-if` 和 `v-for` |
| **`data` 必须使用函数返回** | ✅ 组件 `data` 选项必须是一个返回对象的函数 | ❌ 不要将 `data` 定义为对象（会导致状态共享） |

### 3.2 优先级 B：强烈推荐的（Strongly Recommended）

| 规则 | 允许（DO） | 禁止（DO NOT） |
|------|------------|----------------|
| **组件文件命名** | ✅ 统一使用 PascalCase 或 kebab-case（保持一致） | ❌ 不要混用命名风格 |
| **基础组件命名** | ✅ 以 `Base`、`App` 或 `V` 为前缀（如 `BaseButton`） | ❌ 不要使用通用单词不加前缀 |
| **单例组件命名** | ✅ 以 `The` 为前缀（如 `TheHeader`） | ❌ 不要使用 `Header` 等通用名 |
| **紧耦合组件命名** | ✅ 以父组件名为前缀（如 `TodoList` 的子组件 `TodoListItem`） | ❌ 不要使用与父组件无关的命名 |
| **Prop 命名** | ✅ 声明时使用 camelCase，模板中使用 kebab-case | ❌ 不要混用命名格式 |
| **模板中的组件名** | ✅ 使用 PascalCase（或 kebab-case，保持一致） | ❌ 不要混用不同格式 |

### 3.3 优先级 C：推荐的（Recommended）

| 规则 | 允许（DO） | 禁止（DO NOT） |
|------|------------|----------------|
| **属性顺序** | ✅ 保持一致（建议：`v-for` > `v-if` > `v-bind` > `v-on` > `v-model`） | ❌ 不要随机排列属性 |
| **`v-bind` 缩写** | ✅ 统一使用 `:` 或 `v-bind`（推荐使用缩写） | ❌ 不要混用缩写和完整写法 |
| **`v-on` 缩写** | ✅ 统一使用 `@` 或 `v-on`（推荐使用缩写） | ❌ 不要混用缩写和完整写法 |

### 3.4 优先级 D：谨慎使用的（Use with Caution）

| 规则 | 允许（DO） | 禁止（DO NOT） |
|------|------------|----------------|
| **`scoped` 样式** | ✅ 使用 `:deep()` 进行深层选择器穿透 | ❌ 不要使用已废弃的 `>>>` 或 `/deep/` |
| **隐式父子通信** | ✅ 使用 `props` 和 `emits` 或 `provide/inject` | ❌ 不要使用 `this.$parent` 或直接修改父组件的 props |
| **全局注册** | ✅ 仅在必要时（如基础组件）全局注册 | ❌ 不要在全局注册过多组件（影响打包体积） |

---

## 四、TypeScript 支持标准

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 在 Vue 3 项目中启用 TypeScript |
| ✅ **DO** | 为 `ref`、`reactive`、`computed` 等使用泛型定义类型 |
| ✅ **DO** | 为 `props` 使用 `PropType` 定义复杂类型 |
| ✅ **DO** | 为 `emits` 使用类型定义 |
| ❌ **DO NOT** | 不要使用 `any` 类型（除非绝对必要） |
| ❌ **DO NOT** | 不要在模板表达式中忽略类型错误 |
| ❌ **DO NOT** | 不要忘记在 `tsconfig.json` 中启用 `"jsx": "preserve"` |

---

## 五、迁移指南（从 Vue 2 迁移）

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 Vue 3 迁移构建（Migration Build）逐步升级 |
| ✅ **DO** | 优先使用组合式 API 重构新组件 |
| ❌ **DO NOT** | 不要在新项目中使用 Vue 2 语法（如 `Vue.component`、`Vue.filter`） |
| ❌ **DO NOT** | 不要使用已废弃的 `$on`、`$off`、`$once` 等事件 API |

---

## 六、性能与质量保障

| 指令 | 说明 |
|------|------|
| ✅ **DO** | 使用 `v-memo` 缓存静态模板子树 |
| ✅ **DO** | 使用 `shouldComponentUpdate`（Vue 中为 `v-memo`）优化性能 |
| ✅ **DO** | 使用 `defineAsyncComponent` 进行组件懒加载 |
| ❌ **DO NOT** | 不要在组件中创建大型对象而不使用 `shallowRef` / `shallowReactive` |
| ❌ **DO NOT** | 不要在 `watch` 中深度监听大型对象（使用 `deep: false` 或 `shallow`） |
| ❌ **DO NOT** | 不要过度使用 `reactive`（应优先使用 `ref` 以避免解构丢失响应性） |

---

## 七、AI 约束总结（核心禁止项）

> 以下为 AI 生成 Vue 3 代码时必须**绝对避免**的常见错误：

| 序号 | 禁止项 | 说明 |
|------|--------|------|
| 1 | **禁止 `v-if` 与 `v-for` 共存** | 违反会导致优先级混乱，应使用计算属性 |
| 2 | **禁止省略 `v-for` 的 `key`** | 导致渲染错误和性能问题 |
| 3 | **禁止修改 `props`** | 违反单向数据流 |
| 4 | **禁止在 `watch` 中直接修改监听数据** | 导致无限循环 |
| 5 | **禁止使用 Vue 2 全局 API** | `Vue.component`、`Vue.directive` 等已废弃 |
| 6 | **禁止在组合式 API 中使用 `this`** | 组合式 API 中 `this` 为 `undefined` |
| 7 | **禁止在模板中使用复杂表达式** | 应提取为计算属性 |
| 8 | **禁止使用 `v-html` 渲染用户输入** | 存在 XSS 安全风险 |
| 9 | **禁止在 `reactive` 中解构** | 丢失响应性 |
| 10 | **禁止在 `ref` 中存储非数据内容** | 如 DOM 元素、函数、Symbol |

---

## 八、使用说明

1. **AI 约束模式**：将本文档全文作为系统提示词，AI 必须严格遵循所有 ✅ DO 和 ❌ DO NOT 指令。
2. **代码生成检查**：生成代码后，对照此文档进行自检，确保没有违反任何禁止项。
3. **项目规范**：可直接作为团队编码规范文档使用。

> **文档版本**：Vue 3（v3.5+）官方规范 | AI 约束版 | 更新日期：2026-06