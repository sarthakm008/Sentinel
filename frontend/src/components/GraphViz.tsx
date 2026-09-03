// GraphViz component - network visualization using React Flow

import React, { useEffect, useRef } from 'react';
import {
  GraphNode as GraphNodeType,
  GraphEdge,
  GraphResponse,
} from '../types';

// Simple canvas-based graph visualization (no external deps)
interface GraphVizProps {
  data: GraphResponse | null;
  width?: number;
  height?: number;
}

const NODE_COLORS: Record<string, string> = {
  customer: '#3b82f6',
  device: '#8b5cf6',
  address: '#22c55e',
  payment: '#f59e0b',
};

const NODE_SHAPES: Record<string, 'circle' | 'square' | 'diamond' | 'hexagon'> = {
  customer: 'circle',
  device: 'square',
  address: 'diamond',
  payment: 'hexagon',
};

export function GraphViz({ data, width = 600, height = 400 }: GraphVizProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !data) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = width;
    canvas.height = height;

    const nodes = data.nodes;
    const edges = data.edges;

    // Force-directed layout (simple)
    const positions: Record<string, { x: number; y: number; vx: number; vy: number }> = {};

    // Initialize positions
    nodes.forEach((node, i) => {
      const angle = (i / nodes.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.3;
      positions[node.id] = {
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
        vx: 0,
        vy: 0,
      };
    });

    // Force simulation
    const simulate = () => {
      if (!ctx) return;

      // Repulsion between all nodes
      nodes.forEach((nodeA) => {
        nodes.forEach((nodeB) => {
          if (nodeA.id === nodeB.id) return;
          const posA = positions[nodeA.id];
          const posB = positions[nodeB.id];
          const dx = posA.x - posB.x;
          const dy = posA.y - posB.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const force = 1000 / (dist * dist);
          posA.vx += (dx / dist) * force;
          posA.vy += (dy / dist) * force;
        });
      });

      // Attraction along edges
      edges.forEach((edge) => {
        const posA = positions[edge.source];
        const posB = positions[edge.target];
        if (!posA || !posB) return;
        const dx = posB.x - posA.x;
        const dy = posB.y - posA.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const force = dist * 0.01;
        posA.vx += (dx / dist) * force;
        posA.vy += (dy / dist) * force;
        posB.vx -= (dx / dist) * force;
        posB.vy -= (dy / dist) * force;
      });

      // Center gravity
      nodes.forEach((node) => {
        const pos = positions[node.id];
        const dx = width / 2 - pos.x;
        const dy = height / 2 - pos.y;
        pos.vx += dx * 0.001;
        pos.vy += dy * 0.001;
      });

      // Update positions with damping
      nodes.forEach((node) => {
        const pos = positions[node.id];
        pos.vx *= 0.9;
        pos.vy *= 0.9;
        pos.x += pos.vx;
        pos.y += pos.vy;
      });

      // Render
      ctx.clearRect(0, 0, width, height);

      // Draw edges
      ctx.strokeStyle = '#9ca3af';
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
        ctx.fillStyle = '#6b7280';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(edge.relationship.replace('shares_', ''), mx, my - 5);
      });

      // Draw nodes
      nodes.forEach((node) => {
        const pos = positions[node.id];
        const color = NODE_COLORS[node.type] || '#6b7280';
        const isTarget = node.is_target;

        ctx.beginPath();
        const radius = isTarget ? 18 : 14;

        if (NODE_SHAPES[node.type] === 'circle') {
          ctx.arc(pos.x, pos.y, radius, 0, 2 * Math.PI);
        } else if (NODE_SHAPES[node.type] === 'square') {
          ctx.rect(pos.x - radius, pos.y - radius, radius * 2, radius * 2);
        } else if (NODE_SHAPES[node.type] === 'diamond') {
          ctx.moveTo(pos.x, pos.y - radius);
          ctx.lineTo(pos.x + radius, pos.y);
          ctx.lineTo(pos.x, pos.y + radius);
          ctx.lineTo(pos.x - radius, pos.y);
          ctx.closePath();
        }

        ctx.fillStyle = color;
        ctx.fill();

        if (isTarget) {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 3;
          ctx.stroke();
        } else {
          ctx.strokeStyle = '#fff';
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Node label
        ctx.fillStyle = '#1f2937';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        const label = node.label.length > 12 ? node.label.slice(0, 10) + '..' : node.label;
        ctx.fillText(label, pos.x, pos.y + radius + 14);
      });

      animationRef.current = requestAnimationFrame(simulate);
    };

    simulate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [data, width, height]);

  if (!data) {
    return (
      <div className="w-full h-96 flex items-center justify-center bg-gray-50 rounded-lg border border-gray-200">
        <p className="text-gray-500">No graph data available</p>
      </div>
    );
  }

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        className="w-full h-auto bg-white rounded-lg border border-gray-200"
      />
      <div className="absolute bottom-2 right-2 bg-white/90 backdrop-blur rounded p-2 text-xs text-gray-600">
        <div className="flex items-center gap-1 mb-1">
          <span className="w-3 h-3 rounded-full bg-blue-500"></span> Customer
        </div>
        <div className="flex items-center gap-1 mb-1">
          <span className="w-3 h-3 rounded bg-purple-500"></span> Device
        </div>
        <div className="flex items-center gap-1 mb-1">
          <span className="w-3 h-3 rotate-45 bg-green-500"></span> Address
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 bg-yellow-500 clip-path-polygon"></span> Payment
        </div>
        <div className="flex items-center gap-1 mt-1 border-t pt-1">
          <span className="w-5 h-5 rounded-full border-3 border-red-500 bg-transparent"></span> Target
        </div>
      </div>
    </div>
  );
}