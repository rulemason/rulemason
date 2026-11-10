<!-- 怎么在本机看 rulemason.com 落地页，以及以后怎么部署。这一步只写步骤，不替你部署，也不改 DNS。-->

# rulemason.com 落地页

`website/` 是 rulemason 的静态落地页，中文在 `/`，英文在 `/en/`。页面是普通 HTML、CSS 和少量 JS，构建结果就是这些文件本身，可以放到 Cloudflare Pages、Vercel 或 GitHub Pages。

不进 Python 发行包。根目录 `pyproject.toml` 的 wheel 只收 `src/rulemason`，sdist 的 `only-include` 没有 `website/`。

演示 GIF、静帧和 `assets/banner.png` 是仓库 `docs/assets/` 的副本。换了源头之后，把同名文件再拷进 `website/assets/`，并把 GIF 的第一帧导出为 `website/assets/stills/` 里的同名 PNG（打开「减少动效」时用这一帧）。

## 本地预览

在 `website/` 目录里起一个静态服务。页面用的是以 `/` 开头的路径，所以站点根必须是这个目录，不能是仓库根。

```bash
cd website
python3 -m http.server 4173
```

- 中文：<http://127.0.0.1:4173/>
- 英文：<http://127.0.0.1:4173/en/>

## 部署到 Cloudflare Pages

1. Cloudflare 控制台打开 Workers & Pages，Create，选 Pages，Connect to Git。
2. 选仓库 `rulemason/rulemason`。
3. Framework preset 选 None。Build command 留空。Build output directory 填 `website`。
4. 保存并部署。预览地址出来之后，打开首页和 `/en/` 看一遍。
5. 项目里 Custom domains，添加 `rulemason.com`。如果还要 `www`，按页面提示再加一条。

DNS 由你在域名那边改，本仓库不改：

- 域名已经在这个 Cloudflare 账号里时，Pages 会提示把根域名指到这个项目。根域名用 CNAME 时由 Cloudflare 做展平。
- 域名还在别的注册商时，按 Pages 给出的记录去改，或把 nameserver 交给 Cloudflare。改之前核对记录名、目标和原有邮件记录，避免把邮箱解析一起换掉。

## 部署到 Vercel

1. Add New，Project，Import Git Repository，选 `rulemason/rulemason`。
2. Framework Preset 选 Other。Root Directory 填 `website`。
3. Build Command 留空。Output Directory 留空（根目录已经是 `website/`，输出就是当前目录）。
4. Deploy。打开预览地址的首页和 `/en/`。
5. Settings，Domains，添加 `rulemason.com`。

按 Vercel 给出的 A 记录或 CNAME 到注册商改解析。同样不在这个仓库里改 DNS。改之前核对会不会盖掉已有的邮件记录。

## 部署到 GitHub Pages

可以用 Actions 把 `website/` 作为产物发布。构建步骤留空，上传的目录是 `website`。仓库 Pages 设置里再填自定义域名 `rulemason.com`，并按 GitHub 当时给出的记录去改 DNS。

## 不在这次做的事

不创建 Cloudflare 或 Vercel 项目，不改 `rulemason.com` 的 DNS，也不把页面接到现有的 CI 里。CI 仍只跑 ruff 和测试。
