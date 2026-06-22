"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Settings,
  Database,
  Search,
  Workflow,
  Activity,
  Terminal,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/config", label: "Configuration", icon: Settings },
  { href: "/data", label: "Data & Components", icon: Database },
  { href: "/retrieval", label: "Retrieval & Query", icon: Search },
  { href: "/workflow", label: "Workflow & HITL", icon: Workflow },
  { href: "/observability", label: "Observability", icon: Activity },
  { href: "/cli", label: "CLI Launcher", icon: Terminal },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 flex-col border-r bg-card">
      <div className="flex h-16 items-center border-b px-6">
        <span className="text-lg font-semibold">Compliance Analyzer</span>
      </div>
      <nav className="flex-1 space-y-1 p-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t p-4">
        <p className="text-xs text-muted-foreground">
          v0.1.0 — Local-first, zero-cloud
        </p>
      </div>
    </aside>
  );
}
