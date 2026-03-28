/**
 * OpsWarden Dark Theme Color Palette
 *
 * 如何使用：
 * 将此颜色配置替换 frontend/pages/ 下各页面 <script id="tailwind-config"> 中的 colors 对象，
 * 并将 <html> 标签改为 <html class="dark" lang="zh-CN">，即可切换为深色主题。
 *
 * 未来实现主题切换的推荐方案：
 * 1. 将颜色替换为 CSS 变量 (var(--color-primary) 等)
 * 2. 在 :root 和 .dark 选择器下分别定义两套变量值
 * 3. 通过 JS 在 <html> 上切换 "dark" class 即可实现切换
 */

const darkThemeColors = {
  "surface-container-low": "#191b22",
  "on-background": "#e2e2eb",
  "on-primary": "#002f68",
  "surface-variant": "#33343b",
  "surface-dim": "#111319",
  "outline-variant": "#424753",
  "surface-tint": "#acc7ff",
  "primary-fixed-dim": "#acc7ff",
  "surface-container-lowest": "#0c0e14",
  "secondary": "#41eec2",
  "primary-container": "#508ff8",
  "background": "#111319",
  "primary": "#acc7ff",
  "surface": "#111319",
  "on-surface-variant": "#c2c6d5",
  "surface-container": "#1e1f26",
  "outline": "#8c909e"
};
