import {
  TRAIL_BOARD_HEIGHT,
  TRAIL_BOARD_WIDTH,
  TRAIL_NODE_RADIUS,
} from "../config/trailConfig";
import type { TrailNodeLayout } from "../types/trailMakingTypes";

interface TrailMakingBoardProps {
  nodes: TrailNodeLayout[];
  completedCount: number;
  onPointerMove: (event: React.PointerEvent<SVGSVGElement>) => void;
  onNodeClick: (node: TrailNodeLayout, event: React.PointerEvent<SVGCircleElement>) => void;
}

export function TrailMakingBoard({
  nodes,
  completedCount,
  onPointerMove,
  onNodeClick,
}: TrailMakingBoardProps) {
  const completedNodes = nodes.filter((node) => node.sequence_index < completedCount);
  const polylinePoints = completedNodes.map((node) => `${node.x},${node.y}`).join(" ");

  return (
    <div className="trail-board">
      <svg
        className="trail-board__svg"
        viewBox={`0 0 ${TRAIL_BOARD_WIDTH} ${TRAIL_BOARD_HEIGHT}`}
        role="img"
        aria-label="Trail Making board"
        onPointerMove={onPointerMove}
      >
        {polylinePoints ? (
          <polyline
            points={polylinePoints}
            fill="none"
            stroke="rgba(47, 80, 128, 0.72)"
            strokeWidth="8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ) : null}
        {nodes.map((node) => {
          const isCompleted = node.sequence_index < completedCount;
          return (
            <g key={node.node_id} className={`trail-board__node ${isCompleted ? "is-completed" : ""}`}>
              <circle
                cx={node.x}
                cy={node.y}
                r={TRAIL_NODE_RADIUS}
                onPointerDown={(event) => onNodeClick(node, event)}
              />
              <text x={node.x} y={node.y} textAnchor="middle" dominantBaseline="central">
                {node.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
