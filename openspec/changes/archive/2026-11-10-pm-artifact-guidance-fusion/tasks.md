## 1. 确认范围（实现闸门）

- [x] 1.1 用户确认方案 A+B（含结构提示预设）与关键词最小集合
- [x] 1.2 确认不移植 PM slash 命令面、不拷贝 PMS（CC BY-NC-SA）正文、不进默认判断红线

## 2. 规矩与分发

- [x] 2.1 自研 `rules/product-artifact-caution.md` + 入口/`COPIED_SHARED`/契约一句
- [x] 2.2 `must_contain`/`pattern` severity 兼容增强；包内 product-artifact 预设；init/update 幂等种子；CLI `--preset` 扩展且保留 hint|strict=prose
- [x] 2.3 测试：分发、入口、种子幂等、hint/strict、旧 prose/cjk/field、坏配置、误报边界、remove、wheel/sdist 干净安装执行

## 3. 验证与交付

- [x] 3.1 ruff / 完整 pytest / openspec strict / 构建 / 低成本 rulemason 检查
- [x] 3.2 付费 Jev / 判断回归：不跑并注明
- [x] 3.3 前后对比、配置说明、verification；**本地提交**；不归档、不推送、不发版
