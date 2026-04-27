from __future__ import annotations

from typing import Any


IMAGE_PROMPT_CATEGORY_GROUPS: list[dict[str, Any]] = [
    {
        "slug": "use-cases",
        "group": "使用场景",
        "items": [
            {"slug": "profile-avatar", "label": "个人资料 / 头像", "hint": "适合头像、个人展示、社交身份视觉。"},
            {"slug": "social-media-post", "label": "社交媒体帖子", "hint": "适合小红书、Instagram、朋友圈、短内容封面与拼贴。"},
            {"slug": "infographic-edu-visual", "label": "信息图 / 教育视觉图", "hint": "适合知识图解、流程、讲解、卡片化学习材料。"},
            {"slug": "youtube-thumbnail", "label": "YouTube 缩略图", "hint": "适合高点击率封面、强标题、戏剧化视觉焦点。"},
            {"slug": "comic-storyboard", "label": "漫画 / 故事板", "hint": "适合分镜、连续叙事、漫画页、故事板。"},
            {"slug": "product-marketing", "label": "产品营销", "hint": "适合品牌广告、卖点展示、KV、商业摄影。"},
            {"slug": "ecommerce-main-image", "label": "电商主图", "hint": "适合商品主图、白底/场景图、卖点排版。"},
            {"slug": "game-asset", "label": "游戏素材", "hint": "适合角色、道具、UI、图标、场景概念。"},
            {"slug": "poster-flyer", "label": "海报 / 传单", "hint": "适合活动海报、宣传单、音乐会/电影海报。"},
            {"slug": "app-web-design", "label": "App / 网页设计", "hint": "适合界面稿、落地页、组件、仪表盘视觉。"},
        ],
    },
    {
        "slug": "styles",
        "group": "风格",
        "items": [
            {"slug": "photography", "label": "摄影", "hint": "强调镜头、光线、焦段、真实摄影质感。"},
            {"slug": "cinematic-film-still", "label": "电影 / 电影剧照", "hint": "强调电影感构图、灯光、色彩分级、剧照质感。"},
            {"slug": "anime-manga", "label": "动漫 / 漫画", "hint": "强调二次元角色、线条、赛璐璐或绘画渲染。"},
            {"slug": "black-white-anime", "label": "黑白漫画页 / 自动分镜对白", "hint": "根据剧情自动拆成多个漫画格，生成黑白日漫线稿、对白气泡、旁白框、网点灰阶与阅读顺序。"},
            {"slug": "illustration", "label": "插画", "hint": "强调商业插画、绘本、编辑插画或数字绘画。"},
            {"slug": "sketch-line-art", "label": "草图 / 线稿", "hint": "强调素描、铅笔、钢笔、轮廓线、排线。"},
            {"slug": "comic-graphic-novel", "label": "漫画 / 图画小说", "hint": "强调漫画格、分镜、墨线、叙事张力。"},
            {"slug": "3d-render", "label": "3D 渲染", "hint": "强调材质、灯光、建模、CGI、产品级渲染。"},
            {"slug": "chibi-q-style", "label": "Q 版 / Q 萌风", "hint": "强调可爱比例、圆润造型、萌系表情。"},
            {"slug": "isometric", "label": "等距", "hint": "强调等距视角、微缩场景、清晰结构。"},
            {"slug": "pixel-art", "label": "像素艺术", "hint": "强调低分辨率像素、调色板、游戏像素质感。"},
            {"slug": "oil-painting", "label": "油画", "hint": "强调厚涂、笔触、画布、经典绘画光影。"},
            {"slug": "watercolor", "label": "水彩画", "hint": "强调透明水彩、纸张纹理、晕染、柔和边缘。"},
            {"slug": "ink-chinese-style", "label": "水墨 / 中国风", "hint": "强调留白、水墨、国风、宣纸、书画气韵。"},
            {"slug": "retro-vintage", "label": "复古 / 怀旧", "hint": "强调胶片、老照片、复古印刷、怀旧色调。"},
            {"slug": "cyberpunk-sci-fi", "label": "赛博朋克 / 科幻", "hint": "强调霓虹、未来城市、科技界面、科幻材质。"},
            {"slug": "minimalism", "label": "极简主义", "hint": "强调留白、少量元素、克制配色、干净排版。"},
        ],
    },
    {
        "slug": "subjects",
        "group": "主体",
        "items": [
            {"slug": "portrait-selfie", "label": "人像 / 自拍", "hint": "适合人物肖像、自拍、半身或全身人物。"},
            {"slug": "influencer-model", "label": "网红 / 模特", "hint": "适合时尚大片、生活方式、模特展示。"},
            {"slug": "character", "label": "角色", "hint": "适合原创角色、IP 设定、角色立绘。"},
            {"slug": "group-couple", "label": "团体 / 情侣", "hint": "适合多人合照、情侣、团队、组合关系。"},
            {"slug": "product", "label": "产品", "hint": "适合实体商品、科技产品、包装、爆炸图。"},
            {"slug": "food-drink", "label": "食品 / 饮料", "hint": "适合美食摄影、饮品、菜单、食品广告。"},
            {"slug": "fashion-item", "label": "时尚单品", "hint": "适合服装、鞋包、配饰、穿搭单品。"},
            {"slug": "animal-creature", "label": "动物 / 生物", "hint": "适合动物、宠物、幻想生物、怪物。"},
            {"slug": "vehicle", "label": "车辆", "hint": "适合汽车、摩托、飞行器、交通工具。"},
            {"slug": "architecture-interior", "label": "建筑 / 室内设计", "hint": "适合建筑外观、室内空间、家装、展厅。"},
            {"slug": "landscape-nature", "label": "风景 / 自然", "hint": "适合山川、森林、海岸、自然景观。"},
            {"slug": "cityscape-street", "label": "城市风光 / 街道", "hint": "适合街景、城市夜景、街拍、都市空间。"},
            {"slug": "diagram-chart", "label": "图表", "hint": "适合示意图、图解、图表、结构说明。"},
            {"slug": "text-typography", "label": "文本 / 排版", "hint": "适合准确文字、Logo、海报排版、字体设计。"},
            {"slug": "abstract-background", "label": "摘要 / 背景", "hint": "适合抽象图形、壁纸、纹理、背景素材。"},
        ],
    },
]

ALL_IMAGE_PROMPT_CATEGORIES: list[dict[str, str]] = [
    {"group": group["group"], **item}
    for group in IMAGE_PROMPT_CATEGORY_GROUPS
    for item in group["items"]
]

_IMAGE_PROMPT_CATEGORY_BY_SLUG = {item["slug"]: item for item in ALL_IMAGE_PROMPT_CATEGORIES}


def get_image_prompt_category(slug: str | None) -> dict[str, str] | None:
    normalized = str(slug or "").strip()
    if not normalized or normalized == "auto":
        return None
    return _IMAGE_PROMPT_CATEGORY_BY_SLUG.get(normalized)


def list_image_prompt_category_groups() -> list[dict[str, Any]]:
    return IMAGE_PROMPT_CATEGORY_GROUPS


def _category_catalog_text() -> str:
    lines: list[str] = []
    for group in IMAGE_PROMPT_CATEGORY_GROUPS:
        lines.append(f"{group['group']}：")
        for item in group["items"]:
            lines.append(f"- {item['slug']}：{item['label']}（{item['hint']}）")
    return "\n".join(lines)


def build_image_prompt_standardizer_request(
    user_prompt: str,
    category_slug: str | None = None,
    mode: str = "generate",
    size: str | None = None,
) -> tuple[str, str]:
    category = get_image_prompt_category(category_slug)
    selected_category = (
        f"{category['group']} / {category['label']} ({category['slug']})"
        if category
        else "自动识别：请从分类体系中选择最匹配的 1-2 个类别"
    )
    mode_label = "图生图 / 图片编辑" if mode == "edit" else "文生图"
    size_hint = str(size or "未指定").strip() or "未指定"

    instructions = f"""你是 GPT Image 2 专用提示词工程师，熟悉 YouMind-OpenLab/awesome-gpt-image-2 的分类体系。你的任务是把用户的自然语言想法改写成可直接用于 GPT Image 2 / gpt-image-2 的标准高质量提示词。

分类体系（必须覆盖并遵循）：
{_category_catalog_text()}

输出要求：
1. 只输出最终提示词正文，不要解释、不要 Markdown 代码块、不要前后寒暄。
2. 保留用户的真实意图，不要引入用户没有要求的品牌、人物身份、版权角色或敏感属性；如果用户给出具体文字、Logo、日期、数字、语言内容，必须逐字保留并明确要求准确排版。若用户选择了具体分类，最终提示词必须显式体现该分类的关键视觉语言，不要自行改成无关分类。
3. 根据所选分类补全：画面类型、主体、场景/背景、构图、镜头/视角、光线、色彩、材质/质感、细节层级、文本/排版要求、输出比例、质量要求。
4. 如果选择“黑白漫画页 / 自动分镜对白”，最终提示词必须生成“一整页黑白漫画”，而不是单张插画：
   - 自动根据用户剧情拆成 3-8 个分镜格，明确 page_layout、panel_count、reading_order、panel_borders、gutter。
   - 为每个分镜写清：镜头景别、人物动作、表情、背景、构图、气氛、拟声词/SFX、对白气泡或旁白框内容。
   - 如果用户没有提供对白，你必须根据情节自动补 1-3 句简短自然的中文对白/旁白；如果用户指定语言或台词，必须逐字保留。
   - 必须包含：monochrome / black and white manga page、clean line art、high contrast ink、screentone / grayscale shading、crisp panel borders、speech bubbles、caption boxes、manga SFX、no color。
   - 不要输出“无文字/无对白/无 Logo”作为默认约束；只有用户明确要求无字时才禁止文字。
   - 输出格式优先使用结构化 JSON 风格，字段包含 type、page_layout、panel_count、reading_order、panels、style、lettering、quality、negative_constraints。
5. 如果是图生图/编辑模式，要把提示词写成“基于参考图，保留主体身份/结构/构图中需要保留的部分，只改变用户要求改变的部分”的编辑指令。
6. 推荐使用紧凑的结构化提示词格式（可以是 JSON 风格对象或分段自然语言），字段可包含 type、subject、style、scene/background、composition、lighting、color_palette、details、text/layout、quality、negative_constraints。
7. 提示词语言以中文为主，专业镜头、材质、设计术语可保留英文；最终结果必须自然、可执行、适合直接生图。
""".strip()

    user_message = f"""用户原始输入：
{user_prompt.strip()}

当前模式：{mode_label}
选择分类：{selected_category}
画幅比例：{size_hint}

请把上面的输入转化为 GPT Image 2 标准提示词。""".strip()
    return instructions, user_message
