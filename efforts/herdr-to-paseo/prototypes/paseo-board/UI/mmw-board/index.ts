import type { PluginContext } from "@getpaseo/plugin";
import { BoardSurface } from "./board.client";
import { boardRpc, specsRpc } from "./board.shared";
import { buildBoard, listSpecs } from "./tracker.server";

export default function contribute(plugin: PluginContext) {
  plugin.handle(boardRpc, ({ repoPath, spec, sinceHours }) => buildBoard(repoPath, spec, sinceHours));
  plugin.handle(specsRpc, async ({ repoPath }) => ({ specs: await listSpecs(repoPath) }));
  plugin.addSurface("board", BoardSurface);
  plugin.addSidebarItem({
    id: "board",
    title: "mmw board",
    icon: "LayoutDashboard",
    surface: "board",
  });
  return () => {};
}
