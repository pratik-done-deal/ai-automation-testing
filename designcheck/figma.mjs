#!/usr/bin/env node
// Figma REST API helper (works with a personal access token, no Dev Mode needed).
//
//   node figma.mjs frames --url <figma-file-url>                       list pages/frames with node ids
//   node figma.mjs image  --url <figma-frame-url> --out design.png [--node 12:345] [--scale 1]
//   node figma.mjs spec   --url <figma-frame-url> --out design-spec.json [--node 12:345]
//
// Requires FIGMA_TOKEN in the environment.

import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const API = 'https://api.figma.com/v1';

const [command, ...rest] = process.argv.slice(2);
const args = parseArgs(rest);

if (!['frames', 'image', 'spec'].includes(command)) {
  fail('Usage: node figma.mjs <frames|image|spec> --url <figma-url> [--node id] [--out path] [--scale n]');
}
if (!process.env.FIGMA_TOKEN) {
  fail('FIGMA_TOKEN is not set. Create one in Figma → Settings → Security → Personal access tokens, then `export FIGMA_TOKEN=figd_...` (e.g. in ~/.zshrc).');
}

const { fileKey, nodeId: urlNodeId } = parseFigmaUrl(args.url || '');
const nodeId = normalizeNodeId(args.node) || urlNodeId;

if (command === 'frames') {
  const file = await api(`/files/${fileKey}?depth=2`);
  const pages = file.document.children.map((page) => ({
    page: page.name,
    frames: (page.children || [])
      .filter((n) => ['FRAME', 'COMPONENT', 'SECTION', 'COMPONENT_SET'].includes(n.type))
      .map((n) => ({ id: n.id, name: n.name, type: n.type })),
  }));
  console.log(JSON.stringify({ file: file.name, fileKey, pages }, null, 2));
} else {
  if (!nodeId) fail('No node id. Use a frame link containing ?node-id=... or pass --node 12:345');
  if (!args.out) fail('--out is required');
  await mkdir(path.dirname(args.out), { recursive: true });

  if (command === 'image') {
    const scale = Number(args.scale || 1);
    const res = await api(`/images/${fileKey}?ids=${encodeURIComponent(nodeId)}&format=png&scale=${scale}`);
    const imageUrl = res.images?.[nodeId];
    if (!imageUrl) fail(`Figma returned no image for node ${nodeId}${res.err ? `: ${res.err}` : ''}`);
    const png = await fetch(imageUrl);
    if (!png.ok) fail(`Downloading render failed: HTTP ${png.status}`);
    await writeFile(args.out, Buffer.from(await png.arrayBuffer()));
    const doc = await getNode(nodeId);
    const box = doc.absoluteBoundingBox || {};
    console.log(JSON.stringify({ out: args.out, node: nodeId, name: doc.name, frameWidth: box.width, frameHeight: box.height, scale }));
  } else {
    const doc = await getNode(nodeId);
    const origin = doc.absoluteBoundingBox || { x: 0, y: 0 };
    await writeFile(args.out, JSON.stringify(trim(doc, origin), null, 2));
    console.log(JSON.stringify({ out: args.out, node: nodeId, name: doc.name, frameWidth: origin.width, frameHeight: origin.height }));
  }
}

async function getNode(id) {
  const res = await api(`/files/${fileKey}/nodes?ids=${encodeURIComponent(id)}`);
  const doc = res.nodes?.[id]?.document;
  if (!doc) fail(`Node ${id} not found in file ${fileKey}`);
  return doc;
}

async function api(endpoint) {
  const res = await fetch(API + endpoint, { headers: { 'X-Figma-Token': process.env.FIGMA_TOKEN } });
  if (res.status === 403) fail('Figma API 403: token invalid/expired or no access to this file.');
  if (res.status === 404) fail('Figma API 404: file not found. Check the URL.');
  if (res.status === 429) fail(`Figma API rate limit hit (429). Retry after ${res.headers.get('retry-after') || 'a minute'}s.`);
  if (!res.ok) fail(`Figma API error ${res.status}: ${await res.text()}`);
  return res.json();
}

// Reduce the raw Figma node tree to the properties that matter for UI comparison.
function trim(node, origin) {
  const out = { name: node.name, type: node.type, id: node.id };
  const box = node.absoluteBoundingBox;
  if (box) out.box = { x: round(box.x - origin.x), y: round(box.y - origin.y), w: round(box.width), h: round(box.height) };

  const fills = visible(node.fills);
  if (fills.length) out.fills = fills.map(paint);
  const strokes = visible(node.strokes);
  if (strokes.length) out.border = { colors: strokes.map(paint), weight: node.strokeWeight, align: node.strokeAlign };

  if (node.cornerRadius) out.radius = node.cornerRadius;
  else if (node.rectangleCornerRadii) out.radius = node.rectangleCornerRadii;
  if (node.opacity != null && node.opacity < 1) out.opacity = round(node.opacity);

  if (node.layoutMode && node.layoutMode !== 'NONE') {
    out.layout = {
      direction: node.layoutMode === 'HORIZONTAL' ? 'row' : 'column',
      gap: node.itemSpacing || 0,
      padding: [node.paddingTop || 0, node.paddingRight || 0, node.paddingBottom || 0, node.paddingLeft || 0],
      justify: node.primaryAxisAlignItems,
      align: node.counterAxisAlignItems,
    };
  }

  const effects = visible(node.effects);
  if (effects.length) {
    out.effects = effects.map((e) => ({ type: e.type, radius: e.radius, spread: e.spread, offset: e.offset, color: e.color && hex(e.color) }));
  }

  if (node.type === 'TEXT') {
    const s = node.style || {};
    out.text = node.characters;
    out.font = {
      family: s.fontFamily,
      size: s.fontSize,
      weight: s.fontWeight,
      lineHeight: s.lineHeightPx && round(s.lineHeightPx),
      letterSpacing: s.letterSpacing && round(s.letterSpacing),
      align: s.textAlignHorizontal,
      case: s.textCase,
    };
  }

  const children = (node.children || []).filter((c) => c.visible !== false);
  if (children.length) out.children = children.map((c) => trim(c, origin));
  return out;
}

function paint(p) {
  if (p.type === 'SOLID') return hex({ ...p.color, a: (p.color.a ?? 1) * (p.opacity ?? 1) });
  if (p.type?.startsWith('GRADIENT')) return { type: p.type, stops: (p.gradientStops || []).map((s) => hex(s.color)) };
  return p.type;
}

function hex({ r, g, b, a = 1 }) {
  const h = (v) => Math.round(v * 255).toString(16).padStart(2, '0');
  return `#${h(r)}${h(g)}${h(b)}${a < 1 ? h(a) : ''}`;
}

function visible(list) {
  return (list || []).filter((x) => x.visible !== false);
}

function round(n) {
  return Math.round(n * 100) / 100;
}

function parseFigmaUrl(url) {
  const key = url.match(/figma\.com\/(?:file|design|proto|board)\/([A-Za-z0-9]+)/);
  if (!key) fail(`Not a Figma file URL: "${url}"`);
  const node = url.match(/[?&]node-id=([^&#]+)/);
  return { fileKey: key[1], nodeId: node ? normalizeNodeId(decodeURIComponent(node[1])) : null };
}

function normalizeNodeId(id) {
  return id ? id.replace(/-/g, ':') : null;
}

function parseArgs(list) {
  const out = {};
  for (let i = 0; i < list.length; i++) {
    if (list[i].startsWith('--')) out[list[i].slice(2)] = list[i + 1]?.startsWith('--') ? true : list[++i];
  }
  return out;
}

function fail(message) {
  console.error(message);
  process.exit(1);
}
