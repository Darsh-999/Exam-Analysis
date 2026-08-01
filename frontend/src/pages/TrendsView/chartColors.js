// Fixed chart color system per FRONTEND_DESIGN.md §6.6. These are used
// as-is everywhere on the Trends screen instead of picking colors per chart,
// so the whole page reads as one coherent system.

// Single-series charts (Questions per Year, Mark Distribution): one solid
// brand color, no per-bar variation.
export const BRAND_COLOR = '#eb6834';

// Multi-series/categorical charts (topic frequency, subtopic frequency,
// marks-per-paper segments): fixed order, assigned by identity not rank.
// Beyond 8 distinct entries on one chart, fold the remainder into "Other".
export const CATEGORICAL_PALETTE = [
  '#2a78d6', // blue
  '#eb6834', // orange
  '#1baf7a', // aqua
  '#eda100', // yellow
  '#e87ba4', // magenta
  '#008300', // green
  '#4a3aa7', // violet
  '#e34948', // red
];
export const OTHER_COLOR = '#a6a39b'; // muted gray, matches --color-text-muted
export const OTHER_LABEL = 'Other';

// Sequential ramp for the topic-year heatmap - one hue, light to dark,
// independent of the categorical palette above.
export const HEATMAP_STEPS = ['#eef4fb', '#c6ddf3', '#8ebde7', '#4f96d6', '#2a78d6', '#1a4f8f'];

// Status colors for Allocation Health - reserved, never reused elsewhere.
export const STATUS_COLORS = {
  singleAllocated: '#0ca30c', // good
  multiAllocated: '#f5a623', // informational, not bad
  unallocated: '#d03b3b', // the thing actually worth worrying about
};

// Builds a stable label -> color lookup: the first 8 distinct labels (in the
// order they're first seen) get one categorical color each; anything beyond
// that gets OTHER_COLOR. Call this once per independent set of entities (see
// TrendsView for the shared topic map vs. subtopic frequency's own map) and
// reuse the returned function - it must NOT be rebuilt on every render/toggle,
// or colors would shuffle instead of staying tied to each topic's identity.
//
// The returned function also has an `.isKnown(label)` check - charts that
// render a Legend (Marks per Paper, Topic Distribution) need this to merge
// every beyond-the-8th label into one combined "Other" series/slice, rather
// than keeping them as separate series that just happen to share a color
// (which would still clutter the legend with a redundant entry per label).
export function createColorAssigner(labelsInOrder) {
  const colorByLabel = new Map();
  for (const label of labelsInOrder) {
    if (colorByLabel.size >= CATEGORICAL_PALETTE.length) break;
    if (!colorByLabel.has(label)) {
      colorByLabel.set(label, CATEGORICAL_PALETTE[colorByLabel.size]);
    }
  }

  const getColor = (label) => colorByLabel.get(label) ?? OTHER_COLOR;
  getColor.isKnown = (label) => colorByLabel.has(label);
  return getColor;
}

// value: 0-1 fraction of the max count in the current heatmap.
export function heatmapColorFor(fraction) {
  if (fraction <= 0) return HEATMAP_STEPS[0];
  const index = Math.min(
    HEATMAP_STEPS.length - 1,
    Math.ceil(fraction * (HEATMAP_STEPS.length - 1))
  );
  return HEATMAP_STEPS[index];
}
