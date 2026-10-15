# 面试组件架构图资源

阅读入口：[7 张组件架构图](../../interview/图解/00-组件架构.md)。每张 `.svg` 对应同名 `.drawio`，SVG 的 `content` 属性嵌入同一份未压缩 mxfile 图源。

- `.drawio`：用 diagrams.net 打开，可编辑组件、分组和连线。
- `.svg`：文档直接展示，也可用 diagrams.net 打开嵌入的图源。
- `generate.py`：七张图的共同布局定义，使用 Python 标准库生成两个格式，并检查容器范围、文字空间、正交连线和无关节点穿越。

重新生成：在项目根目录运行 `python3 docs/assets/interview-architecture/generate.py`。若直接在 diagrams.net 修改，请同时导出 SVG（选择包含图表数据）；之后重新运行脚本会覆盖这些手动修改，应先同步修改脚本中的布局。

颜色在七张图中固定表示模块，进程边界与 Replica 对象边界使用不同线型。端口来自本地 demo 配置，角色与 shard 是教学示例。标签表示 RPC、调用或事件关系；详细时序继续看原有 Mermaid 流程图。
