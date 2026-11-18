import {
  TRAIL_BOARD_HEIGHT,
  TRAIL_BOARD_PADDING,
  TRAIL_BOARD_WIDTH,
  TRAIL_MIN_NODE_DISTANCE,
} from "../config/trailConfig";
import type { TrailNodeLayout, TrailNodeType } from "../types/trailMakingTypes";
import { createSeededRandom } from "./seededRandom";

function inferNodeType(label: string): TrailNodeType {
  return /^\d+$/.test(label) ? "number" : "letter";
}

export function generateTrailLayout(sequence: readonly string[], seed: string): TrailNodeLayout[] {
  const random = createSeededRandom(seed);
  const nodes: TrailNodeLayout[] = [];

  for (let index = 0; index < sequence.length; index += 1) {
    let placed = false;
    for (let attempt = 0; attempt < 400 && !placed; attempt += 1) {
      const x = TRAIL_BOARD_PADDING + random() * (TRAIL_BOARD_WIDTH - (TRAIL_BOARD_PADDING * 2));
      const y = TRAIL_BOARD_PADDING + random() * (TRAIL_BOARD_HEIGHT - (TRAIL_BOARD_PADDING * 2));
      const tooClose = nodes.some((node) => Math.hypot(node.x - x, node.y - y) < TRAIL_MIN_NODE_DISTANCE);
      if (!tooClose) {
        nodes.push({
          node_id: `trail-node-${index}`,
          label: sequence[index],
          node_type: inferNodeType(sequence[index]),
          sequence_index: index,
          x,
          y,
        });
        placed = true;
      }
    }
    if (!placed) {
      const fallbackX = TRAIL_BOARD_PADDING + ((index % 5) * ((TRAIL_BOARD_WIDTH - (TRAIL_BOARD_PADDING * 2)) / 4));
      const fallbackY = TRAIL_BOARD_PADDING + (Math.floor(index / 5) * ((TRAIL_BOARD_HEIGHT - (TRAIL_BOARD_PADDING * 2)) / 4));
      nodes.push({
        node_id: `trail-node-${index}`,
        label: sequence[index],
        node_type: inferNodeType(sequence[index]),
        sequence_index: index,
        x: fallbackX,
        y: fallbackY,
      });
    }
  }

  return nodes;
}
