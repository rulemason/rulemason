// 复杂度探针：只开 complexity、不做类型检查的 ESLint 配置，存量清理的诊断、改前、改后都用它数函数复杂度（用法见同目录 cleanup.md）
import { createRequire } from "node:module";
import path from "node:path";

const root = process.env.PROBE_ROOT;
const max = Number(process.env.PROBE_MAX);
if (!root) {
  throw new Error("complexity-probe：需要设置 PROBE_ROOT（装有项目 ESLint 与插件的目录）");
}
// 阈值不给默认值，免得前后两次悄悄用了不同的阈值
if (!Number.isInteger(max) || max <= 0) {
  throw new Error("complexity-probe：PROBE_MAX 须为正整数（复杂度阈值）");
}

// 插件从项目目录解析：本文件在 skill 目录下，普通 import 找不到项目的依赖；被测文件也可以在别处（如临时 worktree）。
// createRequire 只认绝对路径，PROBE_ROOT 写成相对路径时按当前目录展开
const require = createRequire(path.join(path.resolve(root), "package.json"));

function optional(name) {
  try {
    return require(name);
  } catch (error) {
    // 走到这里说明这个包本身没装：对应的文件类型不测，启动时写明；装了却加载失败的照常报错，不当成没装
    if (error.code === "MODULE_NOT_FOUND" && error.message.includes(`'${name}'`)) {
      return null;
    }
    throw error;
  }
}

const tseslint = optional("typescript-eslint");
const html = optional("eslint-plugin-html");
const jsOptions = { ecmaVersion: "latest", sourceType: "module", parserOptions: { ecmaFeatures: { jsx: true } } };

// 范围只由传进来的文件清单决定（取自项目自己的 lint），这里不写忽略规则
const config = [
  { rules: { complexity: ["error", max] } },
  { files: ["**/*.{js,mjs,jsx}"], languageOptions: jsOptions },
  { files: ["**/*.cjs"], languageOptions: { ...jsOptions, sourceType: "commonjs" } },
];
const skipped = [];
if (tseslint) {
  config.push({ files: ["**/*.{ts,tsx,mts,cts}"], languageOptions: { ...jsOptions, parser: tseslint.parser } });
} else {
  skipped.push("TS 未测（项目没装 typescript-eslint）");
}
if (html) {
  config.push({
    files: ["**/*.html"],
    plugins: { html },
    languageOptions: { ...jsOptions, sourceType: "script" },
  });
} else {
  skipped.push("HTML 未测（项目没装 eslint-plugin-html）");
}

// 写到标准错误，不混进 --format json 的结果：汇报要写明哪些文件类型没测。
// 不用 console：本文件随 skill 放进项目，项目用 eslint . 时会扫到它，rulemason 基础规则禁用 console
process.stderr.write(`complexity-probe：阈值 ${max}${skipped.length ? "；" + skipped.join("；") : ""}\n`);

export default config;
