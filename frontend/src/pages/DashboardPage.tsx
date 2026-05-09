import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { AlertTriangleIcon } from "lucide-react";
import { listBalancesFlat } from "@/api/balances";
import {
  getBalanceSummaryBySide,
  getBalanceSummaryByTags,
  getBalanceSummaryHistory,
  type BalanceSummaryHistoryItem,
  type BalanceSummaryHistoryResponse,
} from "@/api/reports";
import { listTags } from "@/api/tags";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ─── helpers ────────────────────────────────────────────────────────────────

function currentCalendarMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function formatMonthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-US", {
    month: "short",
    year: "2-digit",
  });
}

function subtractMonths(month: string, n: number): string {
  const [y, m] = month.split("-").map(Number);
  const date = new Date(y, m - 1 - n, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function formatUsd(amount: number): string {
  return `$${amount.toLocaleString()}`;
}

function formatDelta(delta: number): string {
  return delta >= 0
    ? `+$${delta.toLocaleString()}`
    : `−$${Math.abs(delta).toLocaleString()}`;
}

function formatYAxis(value: number): string {
  if (Math.abs(value) >= 1_000_000)
    return `$${(value / 1_000_000).toFixed(1)}M`;
  if (Math.abs(value) >= 1_000) return `$${(value / 1_000).toFixed(0)}k`;
  return `$${value}`;
}

function is422(error: unknown): boolean {
  return error instanceof Error && error.message.includes("422");
}

// ─── NetWorthCard ────────────────────────────────────────────────────────────

interface NetWorthCardProps {
  label: string;
  value: number | null;
  delta: number | null;
  loading: boolean;
  error: boolean;
}

function NetWorthCard({ label, value, delta, loading, error }: NetWorthCardProps) {
  const displayValue = loading || error || value === null ? "—" : formatUsd(value);
  const displayDelta =
    !loading && !error && delta !== null ? formatDelta(delta) : null;
  const deltaPositive = delta !== null && delta >= 0;

  return (
    <div className="rounded-lg border bg-card p-6 space-y-2">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold">{displayValue}</p>
      {displayDelta !== null && (
        <p
          className={`text-sm font-medium ${deltaPositive ? "text-green-600" : "text-red-600"}`}
        >
          {displayDelta} vs prior month
        </p>
      )}
      {displayDelta === null && !loading && (
        <p className="text-sm text-muted-foreground">No prior month</p>
      )}
    </div>
  );
}

// ─── MissingRatesWarning ────────────────────────────────────────────────────

function MissingRatesWarning({ month }: { month: string }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
      <AlertTriangleIcon className="h-4 w-4 mt-0.5 shrink-0" />
      <span>
        Exchange rates missing for {formatMonthLabel(month)}. Some figures
        cannot be calculated.{" "}
        <Link to="/exchange-rates" className="underline font-medium">
          Enter exchange rates
        </Link>
      </span>
    </div>
  );
}

// ─── chart helpers ────────────────────────────────────────────────────────────

interface ChartPoint {
  month: string;
  label: string;
  netWorth: number;
}

function toChartPoints(items: BalanceSummaryHistoryItem[]): ChartPoint[] {
  if (!Array.isArray(items)) return [];
  const byMonth = new Map<string, { asset: number; liability: number }>();
  for (const item of items) {
    if (!byMonth.has(item.month))
      byMonth.set(item.month, { asset: 0, liability: 0 });
    const entry = byMonth.get(item.month)!;
    if (item.group_key === "asset") entry.asset = Number(item.balance_sum_usd);
    if (item.group_key === "liability") entry.liability = Number(item.balance_sum_usd);
  }
  return Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, { asset, liability }]) => ({
      month,
      label: formatMonthLabel(month),
      netWorth: asset - liability,
    }));
}

// ─── DashboardPage ───────────────────────────────────────────────────────────

type Range = "6m" | "12m" | "all";

export default function DashboardPage() {
  const [range, setRange] = useState<Range>("12m");

  const { data: allBalances = [] } = useQuery({
    queryKey: ["balances-months"],
    queryFn: listBalancesFlat,
  });

  const { effectiveMonth, priorMonth } = useMemo(() => {
    if (allBalances.length === 0)
      return { effectiveMonth: currentCalendarMonth(), priorMonth: null };
    const sorted = [...new Set(allBalances.map((b) => b.month))].sort();
    const current = sorted[sorted.length - 1];
    const prior = sorted[sorted.length - 2] ?? null;
    return { effectiveMonth: current, priorMonth: prior };
  }, [allBalances]);

  // ── summary queries ──────────────────────────────────────────────────────
  const {
    data: currentSummary = [],
    isLoading: currentLoading,
    error: currentError,
  } = useQuery({
    queryKey: ["reports-summary-side", effectiveMonth],
    queryFn: () => getBalanceSummaryBySide(effectiveMonth),
  });

  const {
    data: priorSummary = [],
    isLoading: priorLoading,
    error: priorError,
  } = useQuery({
    queryKey: ["reports-summary-side", priorMonth],
    queryFn: () => getBalanceSummaryBySide(priorMonth!),
    enabled: !!priorMonth,
  });

  // ── history query ────────────────────────────────────────────────────────
  const historyFrom = useMemo(() => {
    if (range === "all") return "2000-01";
    if (range === "6m") return subtractMonths(effectiveMonth, 5);
    return subtractMonths(effectiveMonth, 11);
  }, [range, effectiveMonth]);

  const {
    data: historyResponse,
    isLoading: historyLoading,
    error: historyError,
  } = useQuery<BalanceSummaryHistoryResponse>({
    queryKey: ["reports-history", historyFrom, effectiveMonth],
    queryFn: () => getBalanceSummaryHistory(historyFrom, effectiveMonth),
  });

  // ── tag query ────────────────────────────────────────────────────────────
  const {
    data: tagSummary = [],
    isLoading: tagLoading,
    error: tagError,
  } = useQuery({
    queryKey: ["reports-summary-tags", effectiveMonth],
    queryFn: () => getBalanceSummaryByTags(effectiveMonth),
  });

  const { data: tags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: listTags,
  });

  const tagNameMap = useMemo(
    () => new Map(tags.map((t) => [t.id, t.name])),
    [tags],
  );

  // ── derived values ────────────────────────────────────────────────────────
  const summaryMissing422 = is422(currentError);
  const summaryLoading = currentLoading || priorLoading;
  const summaryError = !summaryMissing422 && !!currentError;

  const currentAssets = (() => {
    const raw = currentSummary.find((s) => s.group_key === "asset")?.balance_sum_usd;
    return raw !== undefined ? Number(raw) : null;
  })();
  const currentLiabilities = (() => {
    const raw = currentSummary.find((s) => s.group_key === "liability")?.balance_sum_usd;
    return raw !== undefined ? Number(raw) : null;
  })();
  const currentNetWorth =
    currentAssets !== null && currentLiabilities !== null
      ? currentAssets - currentLiabilities
      : null;

  const priorAssets = (() => {
    const raw = priorSummary.find((s) => s.group_key === "asset")?.balance_sum_usd;
    return raw !== undefined ? Number(raw) : null;
  })();
  const priorLiabilities = (() => {
    const raw = priorSummary.find((s) => s.group_key === "liability")?.balance_sum_usd;
    return raw !== undefined ? Number(raw) : null;
  })();
  const priorNetWorth =
    priorAssets !== null && priorLiabilities !== null
      ? priorAssets - priorLiabilities
      : null;

  const deltaAssets =
    currentAssets !== null && priorAssets !== null && !priorError
      ? currentAssets - priorAssets
      : null;
  const deltaLiabilities =
    currentLiabilities !== null && priorLiabilities !== null && !priorError
      ? currentLiabilities - priorLiabilities
      : null;
  const deltaNetWorth =
    currentNetWorth !== null && priorNetWorth !== null && !priorError
      ? currentNetWorth - priorNetWorth
      : null;

  const chartPoints = useMemo(
    () => toChartPoints(historyResponse?.items ?? []),
    [historyResponse],
  );

  const tagChartData = useMemo(() => {
    if (!Array.isArray(tagSummary)) return [];
    const resolve = (key: string | number | null): string => {
      if (key === null) return "Untagged";
      if (typeof key === "number") return tagNameMap.get(key) ?? `Tag ${key}`;
      return key;
    };
    const named = tagSummary
      .filter((t) => t.group_key !== null)
      .map((t) => ({ name: resolve(t.group_key), value: Number(t.balance_sum_usd) }))
      .sort((a, b) => a.name.localeCompare(b.name));
    const untagged = tagSummary
      .filter((t) => t.group_key === null)
      .map((t) => ({ name: "Untagged", value: Number(t.balance_sum_usd) }));
    return [...named, ...untagged];
  }, [tagSummary, tagNameMap]);

  const show422Warning = summaryMissing422 || is422(historyError) || is422(tagError);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      {show422Warning && <MissingRatesWarning month={effectiveMonth} />}

      {/* ── Summary cards ─────────────────────────────────────────────── */}
      {summaryError ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          Failed to load summary.
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <NetWorthCard
            label="Total Assets"
            value={summaryMissing422 ? null : currentAssets}
            delta={summaryMissing422 ? null : deltaAssets}
            loading={summaryLoading}
            error={summaryMissing422}
          />
          <NetWorthCard
            label="Total Liabilities"
            value={summaryMissing422 ? null : currentLiabilities}
            delta={summaryMissing422 ? null : deltaLiabilities}
            loading={summaryLoading}
            error={summaryMissing422}
          />
          <NetWorthCard
            label="Net Worth"
            value={summaryMissing422 ? null : currentNetWorth}
            delta={summaryMissing422 ? null : deltaNetWorth}
            loading={summaryLoading}
            error={summaryMissing422}
          />
        </div>
      )}

      {/* ── Net worth history ─────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Net Worth History</h2>
          <div className="flex gap-1">
            {(["6m", "12m", "all"] as Range[]).map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`px-3 py-1 text-sm rounded-md transition-colors ${
                  range === r
                    ? "bg-foreground text-background font-medium"
                    : "text-muted-foreground hover:bg-muted"
                }`}
              >
                {r === "all" ? "All" : r.toUpperCase()}
              </button>
            ))}
          </div>
        </div>

        {historyLoading ? (
          <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
            Loading…
          </div>
        ) : is422(historyError) ? null : historyError ? (
          <div className="h-48 flex items-center justify-center text-destructive text-sm">
            Failed to load history.
          </div>
        ) : chartPoints.length === 0 ? (
          <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">
            No data for this range.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartPoints} margin={{ top: 4, right: 16, bottom: 0, left: 8 }}>
              <XAxis
                dataKey="label"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tickFormatter={formatYAxis}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                width={64}
              />
              <Tooltip
                formatter={(value: number) => [formatUsd(value), "Net Worth"]}
                labelFormatter={(label) => label}
              />
              <Bar
                dataKey="netWorth"
                fill="hsl(var(--foreground))"
                radius={[3, 3, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      {/* ── Balances by tag ───────────────────────────────────────────── */}
      <div className="space-y-3">
        <h2 className="text-lg font-medium">Balances by Tag</h2>

        {tagLoading ? null : is422(tagError) ? null : tagError ? (
          <p className="text-sm text-destructive">Failed to load tag breakdown.</p>
        ) : tagChartData.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No balance data for {formatMonthLabel(effectiveMonth)}.
          </p>
        ) : (
          <ResponsiveContainer
            width="100%"
            height={Math.max(120, tagChartData.length * 44)}
          >
            <BarChart
              layout="vertical"
              data={tagChartData}
              margin={{ top: 0, right: 16, bottom: 0, left: 8 }}
            >
              <XAxis
                type="number"
                tickFormatter={formatYAxis}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={96}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                formatter={(value: number) => [formatUsd(value), "Total (USD)"]}
              />
              <Bar
                dataKey="value"
                fill="hsl(var(--foreground))"
                radius={[0, 3, 3, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
