## ADDED Requirements

### Requirement: 第 9 条管到没有调用方的函数与只有一个调用方的抽象层

九条第 9 条 SHALL 写明：不加、不留当前没有调用方的函数和文件；只有一个调用方、自身不带逻辑的抽象层（只转发参数的包装函数、只有一个实现的基类或接口、只为一处调用建的工厂或策略类）MUST 直接内联，出现第二个调用方再抽。为降低复杂度拆出、带有自己逻辑的辅助函数不算抽象层。React 落法第 9 条 SHALL 同步写明只有一处使用、只转发 props 的包装组件直接内联。九条 MUST 仍是 9 条。

#### Scenario: 只转发参数的包装函数
- **WHEN** 新代码里 `create_order(data)` 只做一件事：原样调用 `_create_order_impl(data)` 并返回结果，且全仓只有一处调用它
- **THEN** 独立审查按九条第 9 条报出，建议把包装层内联

#### Scenario: 只有一个实现的接口
- **WHEN** 新代码定义了一个基类 `Notifier`，全仓只有 `EmailNotifier` 一个子类，调用方也只用这一个
- **THEN** 独立审查按第 9 条报出，建议直接使用具体类，出现第二个实现时再抽基类

#### Scenario: 为降复杂度拆出的辅助函数
- **WHEN** 一个函数超过复杂度上限，拆出 `_parse_header(lines)`，它只有一个调用方，但含自己的解析与判断逻辑
- **THEN** 不违反第 9 条

#### Scenario: 重构后遗留的函数
- **WHEN** 重构后旧函数 `legacy_format()` 已没有任何调用方，仍留在文件里
- **THEN** 独立审查或自动精简按第 9 条报出，建议删除

#### Scenario: 只转发 props 的包装组件
- **WHEN** 新 React 代码里 `<OrderCardWrapper {...props} />` 只渲染 `<OrderCard {...props} />`，只有一处使用
- **THEN** 独立审查按 React 落法第 9 条报出，建议直接使用 `OrderCard`

### Requirement: 第 8 条不为上游已保证的条件再加检查

九条第 8 条 SHALL 写明：不为上游已保证的条件再加检查，包括已校验过的参数、类型已排除的空值、不会抛异常的调用，不再判断或包 `try`。条件是否已被保证，以调用链里可见的校验或类型声明为准；看不出保证时，按第 3 条写明「走到这里说明什么」，而不是删掉检查。

#### Scenario: 已校验的参数再查一遍
- **WHEN** 路由处理已校验 `order_id` 非空并转成整数，内部函数开头又写 `if not order_id: return None`
- **THEN** 独立审查按第 8 条报出，建议删掉重复检查

#### Scenario: 不会抛异常的调用包了 try
- **WHEN** 新代码用 `try: name = user.name.strip() except Exception: name = ""` 包住一个类型为 `str` 的属性读取
- **THEN** 独立审查按第 8 条报出，建议去掉 `try`

#### Scenario: 看不出上游保证
- **WHEN** 一个内部函数检查参数是否为空，但调用链里看不到校验，参数类型也允许空值
- **THEN** 不按第 8 条要求删除这个检查
