import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import { listBalancesFlat, listBalancesByMonth } from "@/api/balances";
import { getBalanceSummaryBySide } from "@/api/reports";
import { listExchangeRates } from "@/api/exchange-rates";
import { listInstitutions } from "@/api/institutions";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function currentCalendarMonth(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function formatMonthLabel(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return new Date(y, m - 1, 1).toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });
}

function prevMonth(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return m === 1
    ? `${y - 1}-12`
    : `${y}-${String(m - 1).padStart(2, "0")}`;
}

function nextMonth(month: string): string {
  const [y, m] = month.split("-").map(Number);
  return m === 12
    ? `${y + 1}-01`
    : `${y}-${String(m + 1).padStart(2, "0")}`;
}

function formatUsd(amount: number): string {
  return amount.toLocaleString();
}

interface SummaryCardProps {
  label: string;
  value: number | null;
  loading: boolean;
}

function SummaryCard({ label, value, loading }: SummaryCardProps) {
  return (
    <div className="rounded-lg border bg-card p-6 space-y-2">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="text-2xl font-semibold">
        {loading || value === null ? "—" : `$${formatUsd(value)}`}
      </p>
    </div>
  );
}

export default function ReportsPage() {
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);

  const { data: allBalances = [] } = useQuery({
    queryKey: ["balances-months"],
    queryFn: listBalancesFlat,
  });

  const defaultMonth = useMemo(() => {
    if (allBalances.length === 0) return currentCalendarMonth();
    return allBalances.reduce(
      (max, b) => (b.month > max ? b.month : max),
      allBalances[0].month,
    );
  }, [allBalances]);

  const effectiveMonth = selectedMonth ?? defaultMonth;

  const {
    data: summary = [],
    isLoading: summaryLoading,
    error: summaryError,
  } = useQuery({
    queryKey: ["reports-summary-side", effectiveMonth],
    queryFn: () => getBalanceSummaryBySide(effectiveMonth),
  });

  const { data: monthBalances = [], isLoading: balancesLoading } = useQuery({
    queryKey: ["balances", effectiveMonth],
    queryFn: () => listBalancesByMonth(effectiveMonth),
  });

  const { data: exchangeRates = [] } = useQuery({
    queryKey: ["exchange-rates", effectiveMonth],
    queryFn: () => listExchangeRates(effectiveMonth),
  });

  const { data: institutions = [] } = useQuery({
    queryKey: ["institutions"],
    queryFn: listInstitutions,
  });

  const institutionName = (id: number) =>
    institutions.find((i) => i.id === id)?.name ?? String(id);

  const assetsUsd =
    summary.find((s) => s.group_key === "asset")?.balance_sum_usd ?? 0;
  const liabilitiesUsd =
    summary.find((s) => s.group_key === "liability")?.balance_sum_usd ?? 0;
  const netWorthUsd = assetsUsd - liabilitiesUsd;
  const summaryLoaded = !summaryLoading && !summaryError;

  const rateMap = useMemo(() => {
    const m = new Map<string, number>();
    for (const er of exchangeRates) {
      m.set(er.currency_code, er.rate);
    }
    return m;
  }, [exchangeRates]);

  const usdEquivalent = (amount: number, currency: string): number | null => {
    if (currency === "USD") return amount;
    const rate = rateMap.get(currency);
    if (rate === undefined) return null;
    return Math.round(amount / rate);
  };

  const assetRows = monthBalances
    .filter((b) => b.side === "asset")
    .sort((a, b) => a.account_name.localeCompare(b.account_name));

  const liabilityRows = monthBalances
    .filter((b) => b.side === "liability")
    .sort((a, b) => a.account_name.localeCompare(b.account_name));

  const assetTotalUsd = assetRows.reduce<number | null>((acc, b) => {
    const eq = usdEquivalent(b.amount, b.currency_code);
    if (acc === null || eq === null) return null;
    return acc + eq;
  }, 0);

  const liabilityTotalUsd = liabilityRows.reduce<number | null>((acc, b) => {
    const eq = usdEquivalent(b.amount, b.currency_code);
    if (acc === null || eq === null) return null;
    return acc + eq;
  }, 0);

  const tableNetWorth =
    assetTotalUsd !== null && liabilityTotalUsd !== null
      ? assetTotalUsd - liabilityTotalUsd
      : null;

  const hasBalances = monthBalances.length > 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Reports</h1>
      </div>

      {/* Month selector */}
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSelectedMonth(prevMonth(effectiveMonth))}
          aria-label="Previous month"
        >
          <ChevronLeftIcon className="h-4 w-4" />
        </Button>
        <span className="w-28 text-center font-medium">
          {formatMonthLabel(effectiveMonth)}
        </span>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSelectedMonth(nextMonth(effectiveMonth))}
          aria-label="Next month"
        >
          <ChevronRightIcon className="h-4 w-4" />
        </Button>
      </div>

      {/* Summary cards */}
      {summaryError ? (
        <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">
            {summaryError instanceof Error
              ? summaryError.message
              : "Failed to load summary. Check that exchange rates are entered for this month."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
          <SummaryCard
            label="Total Assets"
            value={summaryLoaded ? assetsUsd : null}
            loading={summaryLoading}
          />
          <SummaryCard
            label="Total Liabilities"
            value={summaryLoaded ? liabilitiesUsd : null}
            loading={summaryLoading}
          />
          <SummaryCard
            label="Net Worth"
            value={summaryLoaded ? netWorthUsd : null}
            loading={summaryLoading}
          />
        </div>
      )}

      {/* Breakdown table */}
      {!balancesLoading && !hasBalances ? (
        <p className="text-center py-12 text-muted-foreground">
          No balance entries for {formatMonthLabel(effectiveMonth)}.
        </p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account</TableHead>
              <TableHead>Institution</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">USD eq.</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {assetRows.map((b) => {
              const eq = usdEquivalent(b.amount, b.currency_code);
              return (
                <TableRow key={b.id}>
                  <TableCell>{b.account_name}</TableCell>
                  <TableCell>{institutionName(b.institution_id)}</TableCell>
                  <TableCell>{b.currency_code}</TableCell>
                  <TableCell className="text-right">
                    {b.amount.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {eq !== null ? formatUsd(eq) : "—"}
                  </TableCell>
                </TableRow>
              );
            })}
            {assetRows.length > 0 && (
              <TableRow className="font-medium bg-muted/50">
                <TableCell colSpan={4}>Assets</TableCell>
                <TableCell className="text-right">
                  {assetTotalUsd !== null ? formatUsd(assetTotalUsd) : "—"}
                </TableCell>
              </TableRow>
            )}

            {liabilityRows.map((b) => {
              const eq = usdEquivalent(b.amount, b.currency_code);
              return (
                <TableRow key={b.id}>
                  <TableCell>{b.account_name}</TableCell>
                  <TableCell>{institutionName(b.institution_id)}</TableCell>
                  <TableCell>{b.currency_code}</TableCell>
                  <TableCell className="text-right">
                    {b.amount.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right">
                    {eq !== null ? formatUsd(eq) : "—"}
                  </TableCell>
                </TableRow>
              );
            })}
            {liabilityRows.length > 0 && (
              <TableRow className="font-medium bg-muted/50">
                <TableCell colSpan={4}>Liabilities</TableCell>
                <TableCell className="text-right">
                  {liabilityTotalUsd !== null
                    ? formatUsd(liabilityTotalUsd)
                    : "—"}
                </TableCell>
              </TableRow>
            )}

            {hasBalances && (
              <TableRow className="font-semibold border-t-2">
                <TableCell colSpan={4}>Net Worth</TableCell>
                <TableCell className="text-right">
                  {tableNetWorth !== null ? formatUsd(tableNetWorth) : "—"}
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
