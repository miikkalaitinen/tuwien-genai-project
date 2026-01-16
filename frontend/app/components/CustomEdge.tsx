import { EdgeProps, getStraightPath } from 'reactflow';

const CustomEdge = ({ id, sourceX, sourceY, targetX, targetY, style, markerEnd, label, data }: EdgeProps) => {
  const [edgePath] = getStraightPath({ sourceX, sourceY, targetX, targetY });

  const quarterX = sourceX + (targetX - sourceX) * 0.25;
  const quarterY = sourceY + (targetY - sourceY) * 0.25;
  const threeQuarterX = sourceX + (targetX - sourceX) * 0.75;
  const threeQuarterY = sourceY + (targetY - sourceY) * 0.75;

  const angle = Math.atan2(sourceY - targetY, sourceX - targetX);
  const arrowLength = 16;

  function getArrowPoints(x: number, y: number, angle: number) {
    return [
      [x, y],
      [x - arrowLength * Math.cos(angle - Math.PI / 8), y - arrowLength * Math.sin(angle - Math.PI / 8)],
      [x - arrowLength * Math.cos(angle + Math.PI / 8), y - arrowLength * Math.sin(angle + Math.PI / 8)],
    ];
  }

  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2;

  const labelFontSize = 14;
  const labelPaddingX = 8;
  const labelPaddingY = 4;
  const labelText = String(label ?? '');
  const labelWidth = labelText.length * labelFontSize * 0.6 + labelPaddingX * 2;
  const labelHeight = labelFontSize + labelPaddingY * 2;

  return (
    <g>
      <path id={id} style={style} className="react-flow__edge-path" d={edgePath} markerEnd={markerEnd} />
      <polygon
        points={getArrowPoints(quarterX, quarterY, angle).map((p) => p.join(",")).join(" ")}
        fill={style?.stroke || '#222'}
        opacity={0.85}
      />
      <polygon
        points={getArrowPoints(threeQuarterX, threeQuarterY, angle).map((p) => p.join(",")).join(" ")}
        fill={style?.stroke || '#222'}
        opacity={0.85}
      />
      {label && (
        <g>
          <rect
            x={midX - labelWidth / 2}
            y={midY - labelHeight - 4}
            width={labelWidth}
            height={labelHeight}
            rx={6}
            fill="#222"
            opacity={0.95}
          />
          <text
            x={midX}
            y={midY - labelHeight / 2}
            textAnchor="middle"
            fontWeight="bold"
            fontSize={labelFontSize}
            fill={style?.stroke || '#fff'}
            paintOrder="stroke"
            style={{
              userSelect: "none"
            }}
          >
            {label}
          </text>
        </g>
      )}
    </g>
  );
};

export default CustomEdge;
