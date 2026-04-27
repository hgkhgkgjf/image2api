export type ImagePromptCategory = {
  slug: string;
  label: string;
  hint: string;
};

export type ImagePromptCategoryGroup = {
  slug: string;
  group: string;
  items: ImagePromptCategory[];
};

export const IMAGE_PROMPT_CATEGORY_AUTO = "auto";

export const IMAGE_PROMPT_CATEGORY_GROUPS: ImagePromptCategoryGroup[] = [
  {
    slug: "use-cases",
    group: "使用场景",
    items: [
      { slug: "profile-avatar", label: "个人资料 / 头像", hint: "头像、个人展示、社交身份视觉" },
      { slug: "social-media-post", label: "社交媒体帖子", hint: "社交平台帖子、封面、拼贴" },
      { slug: "infographic-edu-visual", label: "信息图 / 教育视觉图", hint: "知识图解、流程、讲解卡片" },
      { slug: "youtube-thumbnail", label: "YouTube 缩略图", hint: "高点击率封面、强标题、视觉焦点" },
      { slug: "comic-storyboard", label: "漫画 / 故事板", hint: "分镜、连续叙事、漫画页" },
      { slug: "product-marketing", label: "产品营销", hint: "品牌广告、卖点展示、商业摄影" },
      { slug: "ecommerce-main-image", label: "电商主图", hint: "商品主图、白底图、卖点排版" },
      { slug: "game-asset", label: "游戏素材", hint: "角色、道具、UI、图标、场景概念" },
      { slug: "poster-flyer", label: "海报 / 传单", hint: "活动海报、宣传单、KV" },
      { slug: "app-web-design", label: "App / 网页设计", hint: "界面稿、落地页、组件视觉" },
    ],
  },
  {
    slug: "styles",
    group: "风格",
    items: [
      { slug: "photography", label: "摄影", hint: "真实摄影、镜头、光线" },
      { slug: "cinematic-film-still", label: "电影 / 电影剧照", hint: "电影感构图、色彩分级" },
      { slug: "anime-manga", label: "动漫 / 漫画", hint: "二次元、赛璐璐、漫画质感" },
      { slug: "black-white-anime", label: "黑白漫画页 / 自动分镜对白", hint: "自动分镜、多格漫画、对白气泡、网点灰阶" },
      { slug: "illustration", label: "插画", hint: "商业插画、绘本、数字绘画" },
      { slug: "sketch-line-art", label: "草图 / 线稿", hint: "素描、钢笔线条、排线" },
      { slug: "comic-graphic-novel", label: "漫画 / 图画小说", hint: "漫画格、墨线、叙事张力" },
      { slug: "3d-render", label: "3D 渲染", hint: "CGI、材质、建模、灯光" },
      { slug: "chibi-q-style", label: "Q 版 / Q 萌风", hint: "可爱比例、圆润造型" },
      { slug: "isometric", label: "等距", hint: "等距视角、微缩场景" },
      { slug: "pixel-art", label: "像素艺术", hint: "像素、低分辨率、游戏质感" },
      { slug: "oil-painting", label: "油画", hint: "厚涂、画布、经典笔触" },
      { slug: "watercolor", label: "水彩画", hint: "透明水彩、晕染、纸张纹理" },
      { slug: "ink-chinese-style", label: "水墨 / 中国风", hint: "留白、水墨、宣纸、国风" },
      { slug: "retro-vintage", label: "复古 / 怀旧", hint: "胶片、旧照片、复古印刷" },
      { slug: "cyberpunk-sci-fi", label: "赛博朋克 / 科幻", hint: "霓虹、未来城市、科技界面" },
      { slug: "minimalism", label: "极简主义", hint: "留白、少元素、克制配色" },
    ],
  },
  {
    slug: "subjects",
    group: "主体",
    items: [
      { slug: "portrait-selfie", label: "人像 / 自拍", hint: "人物肖像、自拍、半身/全身" },
      { slug: "influencer-model", label: "网红 / 模特", hint: "时尚大片、生活方式、模特展示" },
      { slug: "character", label: "角色", hint: "原创角色、IP 设定、角色立绘" },
      { slug: "group-couple", label: "团体 / 情侣", hint: "多人合照、情侣、团队" },
      { slug: "product", label: "产品", hint: "实体商品、科技产品、包装" },
      { slug: "food-drink", label: "食品 / 饮料", hint: "美食摄影、饮品、食品广告" },
      { slug: "fashion-item", label: "时尚单品", hint: "服装、鞋包、配饰" },
      { slug: "animal-creature", label: "动物 / 生物", hint: "动物、宠物、幻想生物" },
      { slug: "vehicle", label: "车辆", hint: "汽车、摩托、飞行器" },
      { slug: "architecture-interior", label: "建筑 / 室内设计", hint: "建筑、室内、家装、展厅" },
      { slug: "landscape-nature", label: "风景 / 自然", hint: "山川、森林、海岸" },
      { slug: "cityscape-street", label: "城市风光 / 街道", hint: "街景、夜景、都市空间" },
      { slug: "diagram-chart", label: "图表", hint: "示意图、图解、结构说明" },
      { slug: "text-typography", label: "文本 / 排版", hint: "准确文字、Logo、字体设计" },
      { slug: "abstract-background", label: "摘要 / 背景", hint: "抽象图形、壁纸、纹理背景" },
    ],
  },
];

export function getImagePromptCategoryLabel(slug: string) {
  if (!slug || slug === IMAGE_PROMPT_CATEGORY_AUTO) {
    return "自动识别";
  }
  for (const group of IMAGE_PROMPT_CATEGORY_GROUPS) {
    const item = group.items.find((category) => category.slug === slug);
    if (item) {
      return `${group.group} / ${item.label}`;
    }
  }
  return "自动识别";
}
