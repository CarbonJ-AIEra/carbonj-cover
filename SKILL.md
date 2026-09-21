---
name: carbonj-cover
description: 生成小红书、B 站、视频号、公众号和 YouTube 的 AI 工具实操视频封面，支持脚本模式与 Agent 自主模式、真实视频证据和六种平台输出。仅在用户明确提到 carbonj-cover、$carbonj-cover、使用 carbonj-cover 或指定本 Skill 时触发；普通封面、首图、视频封面请求不要自动触发。
---

# carbonj-cover

为 AI 工具实操内容生成稳定、清楚、干净、精致的纯图视频封面。封面中不包含创作者人物、头像或人物嵌入；生成结果即为最终图片，没有额外的本地视觉合成步骤。

## 两种执行模式

- **模式一 · 脚本模式（默认）**：使用 `generate_carbonj_cover.py` 本地选帧、调用 ZenMux 分析与生图，输出完整的无人物最终封面。需要 Python、ffmpeg、ZenMux key。
- **模式二 · Agent 自主执行**：不调外部 Gemini、不需要 ZenMux key；执行 Agent 自己按 SOP 选帧、分析和生图。完整流程见 `references/agent-native-flow.md`。

## 配置与输出

- `SKILL_DIR`：当前这份 `SKILL.md` 所在目录。
- 用户配置：`${CARBONJ_COVER_CONFIG:-$HOME/.carbonj-cover/config.json}`。只使用 `mode`、`script_path`、`video_library_root`、`product_asset_mirror`、`api_key_file` 与可选 `creator_name`；不读取任何人物素材或人物配置。
- 脚本：优先 `$SKILL_DIR/scripts/generate_carbonj_cover.py`，否则读取配置 `script_path`。二者都不存在时说明安装不完整。
- API key：优先 `ZENMUX_API_KEY`；备用文件仅从 `api_key_file` 配置或 `--api-key-file` 读取。不得写入提示词、sidecar、日志或最终回复。

默认平台输出为六张独立封面：小红书 `3:4`、B 站首页 `4:3`、视频号 `16:9`、公众号 `2.35:1`、YouTube `16:9`、YouTube Shorts `9:16`。抖音复用小红书 `3:4`。最终封面写在输入视频或图片同目录：`<视频名>_3x4.png`、`_4x3.png`、`_16x9.png`、`_2.35x1.png`、`_youtube_16x9.png`、`_youtube_9x16.png`；中间产物写在 `<视频名>.carbonj-cover/`。

如果配置了 `video_library_root`，先无覆盖地将源视频归入 `<video_library_root>/<视频标题>/`，再生成字幕、封面与 sidecar。

## 模式选择

1. 读取用户配置的 `mode`。
2. 已设为 `script` 或 `agent-native` 时直接执行，不再询问。
3. 未设置时询问一次用户偏好，合并写入配置，不整份覆盖。
4. 用户可在单次任务临时指定模式，不改默认偏好。

`agent-native` 需要多模态视觉与参考图生图能力。在 Codex 中使用 `.system/imagegen` 的 `image_gen` 工具。若当前环境不具备生图能力，说明情况并提供在 Codex 执行或本次临时改用脚本模式两个选择；不要静默失败或改写默认偏好。

走 Agent 自主模式时，先完整读 `references/agent-native-flow.md` 和 `references/cover-rules.md`，按 SOP 执行，忽略下面所有针对脚本的参数说明。

## 标题确认闸门（必须先执行）

标题确认前，不得抽帧、调用生图工具或外部 API、运行脚本，或写入最终封面。此阶段只可读取用户提供的视频标题、字幕、文稿和必要的文件元信息。

1. 用户没有提供明确标题时，先通读可用字幕/文稿，给出 5 个短而有钩子的封面标题建议。标题必须忠于内容，不夸大、不编造。
2. 用户已输入标题时，把它作为候选，询问是否确认使用。
3. 仅在用户明确回复“确认”“用第 N 个”或给出明确自定义标题后，才进行选帧、分析、写 prompt 和生图。
4. 用户修改标题时，回到标题确认闸门。

## 确认后执行

- 封面主标题由执行 Agent 在运行脚本前根据字幕、文稿和真实素材提炼；用户确认后的标题必须原样通过 `--title` 传入，不再被分析模型改写。
- 有 `.srt`、`.ass`、`.txt` 或文稿时先抽成纯文本并完整阅读，优先借用视频原话中的强判断；没有相关资料时才克制精简视频标题。
- 用真实画面作为证据来源，重建成完整封面。不得复制或裁切一张图冒充多个独立画幅。

默认入口：

```bash
python3 "$CARBONJ_COVER_SCRIPT" \
  --video "<视频路径>" \
  --title "<用户已确认的封面主标题>" \
  --subtitle "<纯文本字幕或文稿路径，有则必传>" \
  --topic "<补充背景>"
```

截图或已选关键帧入口：

```bash
python3 "$CARBONJ_COVER_SCRIPT" \
  --image "<截图或关键帧路径>" \
  --logo "<可选 Logo 路径>" \
  --title "<用户已确认的标题>" \
  --topic "<补充背景>"
```

默认不传 `--aspect`，并行生成六个版本。单独重跑时使用 `--aspect 3x4`、`4x3`、`16x9`、`2.35x1`、`youtube_16x9` 或 `youtube_9x16`。

## 常用参数与验证

- `--subtitle`：字幕/脚本/转录文件；有完整文稿时优先传。
- `--logo`：可多次传多个产品 Logo 作为参考资产。
- `--frame-count`、`--scan-fps`、`--candidate-seconds`：控制本地候选帧预筛。
- `--no-allow-subtitle`：禁用封面副标题。
- `--dry-run`：不调 API，只准备本地文件和 prompt。
- `--skip-generate`：只执行分析并写 prompt。
- `--generation-only`：不将屏幕帧和 Logo 上传给图片 API。

如果能识别主产品但缺少 Logo，读取 `references/product-assets.md`，按其中规则寻找官方或可信透明 PNG，归档到 `$SKILL_DIR/assets/product-logos/`，并通过 `--logo` 传入。

## 不可违反

- 只有用户明确提到 `carbonj-cover`、`$carbonj-cover`、`使用 carbonj-cover` 或指定本 Skill 时，才使用本 Skill。
- 生图模型必须一次性生成完整的最终封面，包括真实屏幕证据、标题、产品标识、点缀和风格化效果；禁止生图后本地贴图、拼接、重排、裁切或视觉修补。
- 最终封面、重建 UI 和源截图处理均不得包含人物、人脸、头像、摄像头气泡、真人画中画、吉祥物或角色。
- 默认不添加固定顶部 Panel、品牌字标、顶栏或横线，除非用户在单次任务中明确提出。
- 不得带入历史任务的产品名、模型名、关键词、品牌色或点缀；所有文字和元素仅来自当前视频、标题、字幕、截图或用户补充信息。
- 每次生图前必须保存 `.prompt.md`；完成后必须保留 `analysis.json`、`cover_plan.md`、`manifest.final.json`、API 原始响应和最终图片。
- 所有 sidecar 只描述当前最终状态，不写编辑历史或 changelog。

## 输出说明

完成后说明最终图片、对应 prompt sidecar、`analysis.json`、`cover_plan.md` 的路径，以及使用的参考帧和 Logo。对需要修改的单个平台，按对应 `--aspect` 重跑。
