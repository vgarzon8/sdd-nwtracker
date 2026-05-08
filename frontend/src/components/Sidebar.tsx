import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
}

interface NavGroup {
  heading?: string;
  items: NavItem[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    items: [{ to: "/dashboard", label: "Dashboard" }],
  },
  {
    heading: "Reference Data",
    items: [
      { to: "/currencies", label: "Currencies" },
      { to: "/tags", label: "Tags" },
      { to: "/institutions", label: "Institutions" },
    ],
  },
  {
    items: [
      { to: "/accounts", label: "Accounts" },
      { to: "/balances", label: "Balances" },
      { to: "/reports", label: "Reports" },
      { to: "/import-export", label: "Import / Export" },
    ],
  },
];

export default function Sidebar() {
  return (
    <aside className="w-52 shrink-0 border-r border-border bg-background h-full flex flex-col">
      <div className="px-4 py-4 border-b border-border">
        <span className="font-semibold text-foreground tracking-tight">nwtracker</span>
      </div>
      <nav className="flex-1 overflow-y-auto px-2 py-3 space-y-4">
        {NAV_GROUPS.map((group, i) => (
          <div key={i}>
            {group.heading && (
              <p className="px-2 mb-1 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                {group.heading}
              </p>
            )}
            <ul className="space-y-0.5">
              {group.items.map(({ to, label }) => (
                <li key={to}>
                  <NavLink
                    to={to}
                    className={({ isActive }) =>
                      cn(
                        "block rounded-md px-2 py-1.5 text-sm transition-colors",
                        isActive
                          ? "bg-muted font-medium text-foreground"
                          : "text-muted-foreground hover:bg-muted hover:text-foreground",
                      )
                    }
                  >
                    {label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  );
}
