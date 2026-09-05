// GraphViz component - improved network visualization with radial/force-directed layout

import { useEffect, useRef } from 'react';
import {
  GraphNode as GraphNodeType,
  GraphResponse,
} from '../types';

// Canvas-based graph visualization with improved radial layout
interface GraphVizProps {
  data: GraphResponse | null;
  width?: number;
  height?: number;
}

// Use CSS variables for colors to support light/dark mode
const NODE_SHAPES: Record<string, 'circle' | 'square' | 'diamond' | 'hexagon'> = {
  customer: 'circle',
  device: 'square',
  address: 'diamond',
  payment: 'hexagon',
};

const TARGET_RADIUS = 28;
const ENTITY_RADIUS = 20;
const NEIGHBOR_RADIUS = 18;
const MIN_NODE_DISTANCE = 90;
const EDGE_LENGTH = 120;

interface NodePosition {
  x: number;
  y: number;
  vx: number;
  vy: number;
  fixed?: boolean;
}

function drawShape(ctx: CanvasRenderingContext2D, type: string, x: number, y: number, radius: number) {
  ctx.beginPath();
  switch (NODE_SHAPES[type]) {
    case 'circle':
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      break;
    case 'square':
      ctx.rect(x - radius, y - radius, radius * 2, radius * 2);
      break;
    case 'diamond':
      ctx.moveTo(x, y - radius);
      ctx.lineTo(x + radius, y);
      ctx.lineTo(x, y + radius);
      ctx.lineTo(x - radius, y);
      ctx.closePath();
      break;
    case 'hexagon':
      for (let i = 0; i < 6; i++) {
        const angle = (i * Math.PI / 3) - Math.PI / 6;
        const px = x + radius * Math.cos(angle);
        const py = y + radius * Math.sin(angle);
        if (i === 0) ctx.moveTo(px, py);
        else ctx.lineTo(px, py);
      }
      ctx.closePath();
      break;
  }
}

function getNodeColor(ctx: CanvasRenderingContext2D, node: GraphNodeType, isTarget: boolean): string {
  if (isTarget) {
    return getComputedStyle(document.documentElement).getPropertyValue('--color-risk-critical') || '#ef4444';
  }
  switch (node.type) {
    case 'customer':
      return getComputedStyle(document.documentElement).getPropertyValue('--color-primary') || '#1e40af';
    case 'device':
      return getComputedStyle(document.documentElement).getPropertyValue('--color-risk-medium') || '#b45309';
    case 'address':
      return getComputedStyle(document.documentElement).getPropertyValue('--color-risk-low') || '#047857';
    case 'payment':
      return getComputedStyle(document.documentElement).getPropertyValue('--color-risk-high') || '#dc2626';
    default:
      return getComputedStyle(document.documentElement).getPropertyValue('--color-primary') || '#1e40af';
  }
}

function getNodeStrokeColor(ctx: CanvasRenderingContext2D, isTarget: boolean): string {
  if (isTarget) {
    return getComputedStyle(document.documentElement).getPropertyValue('--color-risk-critical') || '#ef4444';
  }
  return getComputedStyle(document.documentElement).getPropertyValue('--color-surface') || '#ffffff';
}

function getNodeLabelColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-text-primary') || '#1c1917';
}

function getEdgeColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-border') || '#e2e8f0';
}

function getEdgeLabelColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-text-muted') || '#94a3b8';
}

function getLabelBgColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-surface') || '#ffffff';
}

function getCanvasBgColor(): string {
  return getComputedStyle(document.documentElement).getPropertyValue('--color-surface') || '#ffffff';
}

export function GraphViz({ data, width = 700, height = 500 }: GraphVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>(null);
  const pulsePhaseRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = width;
    canvas.height = height;

    const nodes = data.nodes;
    const edges = data.edges;

    // Find target customer
    const targetNode = nodes.find((n) => n.is_target);
    const targetId = targetNode?.id;

    // Build adjacency for connected customers
    const customerNodes = nodes.filter((n) => n.type === 'customer');
    const entityNodes = nodes.filter((n) => n.type !== 'customer');
    const connectedCustomers = customerNodes.filter((n) => n.id !== targetId);

    // Separate entities by type
    const devices = entityNodes.filter((n) => n.type === 'device');
    const addresses = entityNodes.filter((n) => n.type === 'address');
    const payments = entityNodes.filter((n) => n.type === 'payment');

    // Initialize positions with radial layout centered on target
    const positions: Record<string, NodePosition> = {};

    // Place target at center
    if (targetNode) {
      positions[targetId!] = {
        x: width / 2,
        y: height / 2,
        vx: 0,
        vy: 0,
        fixed: true,
      };
    }

    // Helper to place nodes in a ring around center
    const placeInRing = (nodeIds: string[], centerX: number, centerY: number, radius: number, startAngle: number = 0, angleOffset: number = 0) => {
      const count = nodeIds.length;
      if (count === 0) return;
      const angleStep = (2 * Math.PI) / count;
      nodeIds.forEach((id, i) => {
        const angle = startAngle + i * angleStep + angleOffset;
        positions[id] = {
          x: centerX + radius * Math.cos(angle),
          y: centerY + radius * Math.sin(angle),
          vx: 0,
          vy: 0,
        };
      });
    };

    // Place entities in rings around target
    if (targetNode) {
      // First ring: shared entities (devices, addresses, payments)
      const sharedEntities = [...devices, ...addresses, ...payments].map((n) => n.id);
      placeInRing(sharedEntities, width / 2, height / 2, 140, 0, 0);

      // Second ring: connected customers
      const connectedCustomerIds = connectedCustomers.map((n) => n.id);
      placeInRing(connectedCustomerIds, width / 2, height / 2, 220, Math.PI / Math.max(1, connectedCustomerIds.length), 0.5);
    } else {
      // Fallback: distribute all nodes evenly
      const allIds = nodes.map((n) => n.id);
      placeInRing(allIds, width / 2, height / 2, Math.min(width, height) * 0.35);
    }

    // Force simulation for fine-tuning
    const simulate = () => {
      if (!ctx) return;

      // Refresh colors from CSS variables each frame for theme changes
      const edgeColor = getEdgeColor();
      const edgeLabelColor = getEdgeLabelColor();
      const labelColor = getNodeLabelColor();
      const labelBgColor = getLabelBgColor();
      const canvasBgColor = getCanvasBgColor();

      // Repulsion between all nodes (stronger for closer nodes)
      nodes.forEach((nodeA) => {
        const posA = positions[nodeA.id];
        if (!posA || posA.fixed) return;

        nodes.forEach((nodeB) => {
          if (nodeA.id === nodeB.id) return;
          const posB = positions[nodeB.id];
          if (!posB) return;

          const dx = posA.x - posB.x;
          const dy = posA.y - posB.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;

          // Stronger repulsion for close nodes
          if (dist < MIN_NODE_DISTANCE) {
            const force = (MIN_NODE_DISTANCE - dist) * 0.5 + 1000 / (dist * dist);
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;
            posA.vx += fx;
            posA.vy += fy;
          }
        });
      });

      // Edge attraction (keep connected nodes at reasonable distance)
      edges.forEach((edge) => {
        const posA = positions[edge.source];
        const posB = positions[edge.target];
        if (!posA || !posB) return;

        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        // Spring force to maintain edge length
        const force = (dist - EDGE_LENGTH) * 0.03;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        if (!positions[edge.source].fixed) {
          positions[edge.source].vx += fx;
          positions[edge.source].vy += fy;
        }
        if (!positions[edge.target].fixed) {
          positions[edge.target].vx -= fx;
          positions[edge.target].vy -= fy;
        }
      });

      // Boundary constraints - keep nodes within canvas with margin
      const margin = 60;
      nodes.forEach((node) => {
        const pos = positions[node.id];
        if (!pos || pos.fixed) return;

        if (pos.x < margin) {
          pos.vx += (margin - pos.x) * 0.05;
        }
        if (pos.x > width - margin) {
          pos.vx -= (pos.x - (width - margin)) * 0.05;
        }
        if (pos.y < margin) {
          pos.vy += (margin - pos.y) * 0.05;
        }
        if (pos.y > height - margin) {
          pos.vy -= (pos.y - (height - margin)) * 0.05;
        }
      });

      // Update positions with damping
      nodes.forEach((node) => {
        const pos = positions[node.id];
        if (!pos || pos.fixed) return;

        pos.vx *= 0.85;
        pos.vy *= 0.85;
        pos.x += pos.vx;
        pos.y += pos.vy;
      });

      // Pulse animation for target node
      pulsePhaseRef.current += 0.08;

      // Render
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = canvasBgColor;
      ctx.fillRect(0, 0, width, height);

      // Draw edges
      ctx.strokeStyle = edgeColor;
      ctx.lineWidth = 1.5;
      edges.forEach((edge) => {
        const posA = positions[edge.source];
        const posB = positions[edge.target];
        if (!posA || !posB) return;
        ctx.beginPath();
        ctx.moveTo(posA.x, posA.y);
        ctx.lineTo(posB.x, posB.y);
        ctx.stroke();

        // Edge label
        const mx = (posA.x + posB.x) / 2;
        const my = (posA.y + posB.y) / 2;
        ctx.fillStyle = edgeLabelColor;
        ctx.font = '10px var(--font-sans, sans-serif)';
        ctx.textAlign = 'center';
        ctx.fillText(edge.relationship.replace('shares_', ''), mx, my - 5);
      });

      // Draw nodes
      nodes.forEach((node) => {
        const pos = positions[node.id];
        if (!pos) return;

        const isTarget = node.is_target;
        let radius = ENTITY_RADIUS;
        if (isTarget) radius = TARGET_RADIUS;
        else if (node.type === 'customer') radius = NEIGHBOR_RADIUS;

        const fillColor = getNodeColor(ctx, node, isTarget);
        const strokeColor = getNodeStrokeColor(ctx, isTarget);
        const labelBg = labelBgColor;

        ctx.beginPath();
        drawShape(ctx, node.type, pos.x, pos.y, radius);

        ctx.fillStyle = fillColor;
        ctx.fill();

        // Target node pulse effect
        if (isTarget) {
          const pulseRadius = radius + 4 + Math.sin(pulsePhaseRef.current) * 3;
          ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue('--color-risk-critical') || '#ef4444';
          ctx.lineWidth = 2;
          ctx.globalAlpha = 0.4 + 0.3 * Math.sin(pulsePhaseRef.current);
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, pulseRadius, 0, 2 * Math.PI);
          ctx.stroke();
          ctx.globalAlpha = 1;
        }

        ctx.strokeStyle = strokeColor;
        ctx.lineWidth = isTarget ? 3 : 2;
        ctx.stroke();

        // Node label with better positioning to avoid overlap
        ctx.fillStyle = labelColor;
        ctx.font = '11px var(--font-sans, sans-serif)';
        ctx.textAlign = 'center';

        // Position label below node with more space
        const label = node.label.length > 14 ? node.label.slice(0, 12) + '..' : node.label;
        const labelY = pos.y + radius + 18;

        // Draw label background for readability
        const textMetrics = ctx.measureText(label);
        const textWidth = textMetrics.width;
        const textHeight = 14;
        const padding = 4;

        ctx.fillStyle = labelBg;
        ctx.fillRect(pos.x - textWidth / 2 - padding, labelY - textHeight - padding, textWidth + padding * 2, textHeight + padding * 2);

        ctx.fillStyle = labelColor;
        ctx.fillText(label, pos.x, labelY + textHeight / 2 - 2);
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    // Run initial layout
    const runLayout = () => {
      let iterations = 0;
      const maxIterations = 120;

      const step = () => {
        if (iterations >= maxIterations) return;
        simulate();
        iterations++;
        animationRef.current = requestAnimationFrame(step);
      };
      step();
    };

    runLayout();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [data, width, height]);

  if (!data) {
    return (
      <div className="w-full h-96 flex items-center justify-center panel">
        <p className="text-text-muted">No graph data available</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="w-full h-auto panel"
      />
      <div className="absolute top-2 left-2 panel p-2 text-xs text-text-secondary shadow-md" style={{ minWidth: '140px' }}>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded-full" style={{ backgroundColor: 'var(--color-primary)' }}></span>
          <span>Customer</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded" style={{ backgroundColor: 'var(--color-risk-medium)' }}></span>
          <span>Device</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rotate-45" style={{ backgroundColor: 'var(--color-risk-low)' }}></span>
          <span>Address</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3" style={{ backgroundColor: 'var(--color-risk-high)', clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}></span>
          <span>Payment</span>
        </div>
        <div className="flex items-center gap-2 mt-1 border-t border-border pt-1">
          <span className="w-5 h-5 rounded-full border-2 bg-transparent" style={{ borderColor: 'var(--color-risk-critical)' }}></span>
          <span>Target</span>
        </div>
      </div>
    </div>
  );
}