// ESLint 基础规则：代码写法的机械部分（rules/code-style.md）。只导出纯规则，不引插件：插件会从本仓库目录解析，而这里没有 node_modules
export default {
  "no-console": "error",
  "no-nested-ternary": "error",
  // 空块（含空 catch，九条第 8 条）。确需空 catch 的项目在自己的配置里放宽并写明原因
  "no-empty": "error",
  // 取 15 而非 Python 的 10：JSX 里每个 && 和 ?: 都算一个分支，同样的上限放到组件上会严得多。
  // 项目当前代码超出时，在自己的配置里用当前最复杂函数的值覆盖，写明递减计划，只降不升
  complexity: ["error", 15],
};
