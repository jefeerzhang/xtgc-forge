# `assets/diagram/` · 选题工坊可视化源文件

本目录是 SKILL.md 和 README.md 中 mermaid 图的**源文件**。

## 文件清单

| 文件 | 用途 | 嵌入位置 |
|---|---|---|
| `pipeline.mermaid` | 工作流全景图源文件：6 步流水线 + 5 闸硬暂停 + 6 道防线 + 六段式交付 | 参考源，嵌入 `README.md` 顶部 |
| `xtgc-workflow.png` | README 顶部「选题工坊工作流」配图（豆包 Seedream 5.0 生成） | `README.md` 顶部 |
| `checkpoint-flow.mermaid` | 5 闸硬暂停时序图(用户 ↔ Agent ↔ check_step ↔ verdict) | (待嵌入 `SKILL.md` 的"强制 5 次 Checkpoint"小节) |

## 渲染方式

### GitHub 内置

GitHub 在 `.md` / `.mermaid` 文件中内置 mermaid 渲染,直接看即可。本仓库的所有 mermaid
块都按 GitHub 兼容语法写,不依赖 mermaid CLI。

### 本地转 PNG

如需本地预览或导出图片:

```bash
# 一次性安装
npm install -g @mermaid-js/mermaid-cli
# Windows 无 Chrome 下载权限时, 指向系统浏览器:
# $env:PUPPETEER_EXECUTABLE_PATH = "C:\Program Files\Google\Chrome\Application\chrome.exe"

# 转 PNG（时序图，透明底）
npx -p @mermaid-js/mermaid-cli mmdc -i checkpoint-flow.mermaid -o checkpoint-flow.png -b transparent
```

> 注：`xtgc-workflow.png`（README 顶部配图）现由豆包 Seedream 5.0 生图生成，
> 不由此目录渲染。`pipeline.mermaid` 保留作为流程内容参考源。

## 维护原则

- **不改叙事,只改图**。图与文字描述必须同步改。
- **新图先入本目录**,再嵌入 SKILL.md / README.md。`git diff` 时优先看本目录。
- **不在 SKILL.md 内嵌完整 mermaid 块超过 1 个**,减少文档长度。第二个图放时序图,引用本目录。

## 验证

每个 mermaid 文件提交前:

```bash
# 渲染验证(任选其一)
npx -p @mermaid-js/mermaid-cli mmdc -i pipeline.mermaid -o /tmp/p.png && echo OK
# 或在线:https://mermaid.live/
```