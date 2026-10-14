# Idiom rationale — Oceans in Motion v4

The current FIT3179 specification says an HD submission should use **at least 8 advanced idioms across more than 10 charts**, and that **all map idioms count as advanced**. This version contains 12 charts and 8 deliberately different advanced idiom types.

| Chart | Idiom | Advanced? | What it shows | Why this idiom fits |
|---|---|---:|---|---|
| 01 | Point map | Yes | Individual ALA occurrence locations | Position is the direct channel for exact recorded location. |
| 02 | Proportional-symbol map | Yes | 2° cells: record volume + focal-species representation | Size and colour answer two different spatial-summary questions without plotting thousands of points. |
| 03 | Lollipop | No | ALA record totals by focal species | A simple baseline check makes sampling imbalance obvious before ecological interpretation. |
| 04 | Ordinal status ladder | Supporting | EPBC listing level | Status is ordinal, so left-to-right severity ordering is clearer than a decorative advanced idiom. |
| 05 | Bipartite network | Yes | Species ↔ documented threats | The data are relational. A network reveals shared pressures and common connections without fabricating a severity score. |
| 06 | Categorical polygon map | Yes | BIA locations by behaviour | Spatial extent matters; categorical colour communicates why each area is important. |
| 07 | Heatmap | Yes | Species × BIA behaviour counts | A matrix supports rapid comparison of two categorical dimensions. |
| 08 | Radial bar | Yes | Monthly occurrence pattern for one species | Month is cyclic; December reconnects naturally to January. |
| 09 | Bump chart | Yes | Monthly rank of species by record count | Rank suppresses raw-volume dominance and reveals changes in relative position. |
| 10 | Paired time-series | No | Total Shark Control Program catches + deceased share | Two aligned views separate volume from mortality proportion, avoiding misleading stacked-area interpretation. |
| 11 | Layered overlay map | Yes | Marine parks + selected BIA | The task is spatial comparison between two polygon datasets, so layering is meaningful. |
| 12 | 100% stacked bar | No | IUCN zoning mix by marine-park network | Composition is the question; normalising every row to 100% makes the mix comparable. |

## Eight distinct advanced idiom types

1. Point map
2. Proportional-symbol map
3. Bipartite network
4. Categorical polygon map
5. Heatmap
6. Radial bar
7. Bump chart
8. Layered overlay map

## Why this is stronger than forcing every chart to be advanced

The rubric requires advanced idioms to be **effective and meaningful**. The status ladder, catch profile and zone-composition chart remain deliberately simple because a more exotic idiom would make those specific tasks harder to understand for an average Australian audience.

## Interactivity

- One cross-story species selector updates the species-specific point map, BIA map, radial seasonal chart, bump-chart focus and protection overlay.
- The BIA map has its own behaviour filter.
- The protection overlay also has a behaviour filter.
- The threat network highlights connected links on hover.
- All maps and charts retain tooltips where useful.
