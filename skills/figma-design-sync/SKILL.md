---
name: figma-design-sync
description: >-
  Connect Figma design files to production code. Inspect frames/components, export
  vector SVGs and raster assets, extract Figma Variables/tokens, and translate
  Figma designs into pixel-perfect React + Tailwind code. Trigger for "import this
  Figma file", "convert Figma to code", "把 Figma 设计转成代码", "从 Figma 导出图标/切图",
  "sync design tokens from Figma", "Figma 链接", or whenever the user supplies a
  figma.com URL or node-id to build UI. Works with aria.figma.* tools.
---

# Figma Design Sync — 从 Figma 到代码的生产级联动

连接 Figma 设计文件与代码工程的桥梁。通过解析 Figma 的图层树、AutoLayout 属性与设计变量，将专业 UI/UX 资产精确转译为干净、无模板味的生产级组件与本地资源，彻底避免 AI 凭借想象手写简陋 CSS 图形。

---

## 核心工作流 (Three Core Workflows)

### 1. 资产导出流 (Vector & Asset Export)
当设计包含复杂的矢量图形（如声波波纹、多层光晕、品牌 Logo、特殊图标）：
- **工具调用**: `aria.figma.export_images(file_key, node_ids=[...], format="svg"|"png", scale=1.0)`
- **落地规范**:
  - 图标与矢量图形强制使用 `format="svg"`，下载后存入工程的 `src/assets/` 或相应图标组件中。
  - 3D 渲染图、带复杂阴影光斑的插画导出 `@2x` 或 `@3x` PNG，保持 Retina 高清。
  - 清理导出的 SVG 垃圾属性（移除 Figma 内部特定的命名空间、冗余 defs）。

### 2. 组件转译流 (Design-to-Code Translation)
将 Figma 画板/组件精准转换为 React + Tailwind 代码：
- **工具调用**: `aria.figma.nodes(file_key, node_ids=[...], depth=3)`
- **属性映射矩阵**:
  - **AutoLayout**:
    - `layoutMode: "HORIZONTAL"` → `flex flex-row`
    - `layoutMode: "VERTICAL"` → `flex flex-col`
    - `primaryAxisAlignItems: "CENTER"` / `counterAxisAlignItems: "CENTER"` → `items-center justify-center`
    - `itemSpacing` → `gap-{n}`
    - `paddingLeft/Right/Top/Bottom` → `px-{n} py-{n}`
  - **几何与圆角**:
    - `cornerRadius` → 映射至最近的系统 Token（如 `rounded-full`、`rounded-[22px]`）
    - `strokes` / `strokeWeight` → `border border-[var(--border)]`
  - **排版 (Typography)**:
    - 提取 `fontSize`, `fontWeight`, `lineHeightPx`, `letterSpacing`。
    - 检查是否符合所在项目的排版等级，严禁随意引入未注册的孤立字号。
  - **色彩与填充 (Fills)**:
    - 提取 `SOLID` 或 `GRADIENT_RADIAL` / `GRADIENT_LINEAR`。
    - 优先映射到项目已有的 CSS Token（如 `var(--t0)`, `var(--base)`, `var(--s1)`）。

### 3. Token 同步流 (Design Token Sync)
- **工具调用**: `aria.figma.variables(file_key)`
- 读取 Figma Variables（Color/Float/String）及其不同 Mode（Light / Dark）。
- 输出或更新项目中的 `design-tokens.json` 与 `arthera-tokens.css`。

---

## 严守设计审查原则 (Design Guardrails)

1. **拒绝 AI 模板味**: 必须以 Figma 实际图层数据为事实来源（Source of Truth），绝不在转译时凭空捏造无关的彩虹渐变或随机圆角。
2. **结合宿主项目规范**:
   - 在 Arthera 项目中，自动应用 [`aria-ui-design`](docs/design/aria-ui-design/SKILL.md) 宪法：保证黑白灰基底、零 Emoji、使用 `lucide-react` 图标体系。
   - 在对话界面中，遵循 [`conversational-ui-restraint`](skills/conversational-ui-restraint/SKILL.md)：界面克制，内容第一。
