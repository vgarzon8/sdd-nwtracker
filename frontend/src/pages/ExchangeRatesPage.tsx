import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronLeftIcon, ChevronRightIcon, Trash2Icon } from "lucide-react";
import {
  listExchangeRates,
  createExchangeRate,
  updateExchangeRate,
  deleteExchangeRate,
  type ExchangeRate,
} from "@/api/exchange-rates";
import { listCurrencies } from "@/api/currencies";
import { listBalancesFlat } from "@/api/balances";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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

interface EditState {
  key: string;
  value: string;
}

export default function ExchangeRatesPage() {
  const queryClient = useQueryClient();
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState | null>(null);
  const [saveErrors, setSaveErrors] = useState<Record<string, string>>({});
  const [deleteTarget, setDeleteTarget] = useState<ExchangeRate | null>(null);

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

  const { data: currencies = [] } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
  });

  const { data: rates = [] } = useQuery({
    queryKey: ["exchange-rates", effectiveMonth],
    queryFn: () => listExchangeRates(effectiveMonth),
  });

  const nonUsdCurrencies = useMemo(
    () => currencies.filter((c) => c.code !== "USD"),
    [currencies],
  );

  const rateByCode = useMemo(
    () => new Map(rates.map((r) => [r.currency_code, r])),
    [rates],
  );

  const invalidateRates = () => {
    queryClient.invalidateQueries({ queryKey: ["exchange-rates", effectiveMonth] });
  };

  const createMutation = useMutation({
    mutationFn: (vars: { body: Parameters<typeof createExchangeRate>[0]; key: string }) =>
      createExchangeRate(vars.body),
    onSuccess: () => {
      invalidateRates();
      setEditState(null);
    },
    onError: (_err: Error, vars) => {
      setSaveErrors((prev) => ({ ...prev, [vars.key]: "Failed to save." }));
    },
  });

  const updateMutation = useMutation({
    mutationFn: (vars: { id: number; rate: number; key: string }) =>
      updateExchangeRate(vars.id, { rate: vars.rate }),
    onSuccess: () => {
      invalidateRates();
      setEditState(null);
    },
    onError: (_err: Error, vars) => {
      setSaveErrors((prev) => ({ ...prev, [vars.key]: "Failed to save." }));
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteExchangeRate(id),
    onSuccess: () => {
      invalidateRates();
      setDeleteTarget(null);
    },
  });

  function startEdit(currencyCode: string) {
    const existing = rateByCode.get(currencyCode);
    setSaveErrors((prev) => {
      const next = { ...prev };
      delete next[currencyCode];
      return next;
    });
    setEditState({
      key: currencyCode,
      value: existing ? String(existing.rate) : "",
    });
  }

  function commitEdit(currencyCode: string) {
    if (!editState) return;
    const trimmed = editState.value.trim();

    if (trimmed === "") {
      setEditState(null);
      return;
    }

    const rate = parseFloat(trimmed);
    if (isNaN(rate) || rate <= 0) {
      setEditState(null);
      return;
    }

    const existing = rateByCode.get(currencyCode);

    if (existing && rate === existing.rate) {
      setEditState(null);
      return;
    }

    if (existing) {
      updateMutation.mutate({ id: existing.id, rate, key: currencyCode });
    } else {
      createMutation.mutate({
        body: { currency_code: currencyCode, month: effectiveMonth, rate },
        key: currencyCode,
      });
    }
  }

  function handleKeyDown(e: React.KeyboardEvent, currencyCode: string) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitEdit(currencyCode);
    } else if (e.key === "Escape") {
      setEditState(null);
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending || deleteMutation.isPending;

  if (nonUsdCurrencies.length === 0 && currencies.length > 0) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-semibold">Exchange Rates</h1>
        <div className="text-center py-16 text-muted-foreground">
          <p>No non-USD currencies found.</p>
          <a href="/currencies" className="text-sm underline">
            Go to Currencies
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Exchange Rates</h1>

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

      {nonUsdCurrencies.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p>No currencies found.</p>
          <a href="/currencies" className="text-sm underline">
            Go to Currencies
          </a>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Currency</TableHead>
              <TableHead className="text-right">Rate (per 1 USD)</TableHead>
              <TableHead className="w-12" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {nonUsdCurrencies.map((currency) => {
              const existing = rateByCode.get(currency.code);
              const isEditing = editState?.key === currency.code;
              const error = saveErrors[currency.code];

              return (
                <TableRow key={currency.code}>
                  <TableCell>
                    <span className="font-mono font-medium">{currency.code}</span>
                    <span className="ml-2 text-muted-foreground text-sm">{currency.name}</span>
                  </TableCell>
                  <TableCell className="text-right">
                    {isEditing ? (
                      <div className="flex flex-col items-end gap-1">
                        <Input
                          autoFocus
                          type="number"
                          step="0.0001"
                          min="0.0001"
                          className="w-36 text-right"
                          value={editState.value}
                          disabled={isPending}
                          onFocus={(e) => e.target.select()}
                          onChange={(e) =>
                            setEditState((s) =>
                              s ? { ...s, value: e.target.value } : s,
                            )
                          }
                          onBlur={() => commitEdit(currency.code)}
                          onKeyDown={(e) => handleKeyDown(e, currency.code)}
                        />
                        {error && (
                          <p className="text-xs text-destructive">{error}</p>
                        )}
                      </div>
                    ) : (
                      <button
                        className="w-full text-right cursor-pointer hover:underline"
                        onClick={() => startEdit(currency.code)}
                        aria-label={`Edit rate for ${currency.code}`}
                      >
                        {existing ? existing.rate.toFixed(4) : "—"}
                      </button>
                    )}
                  </TableCell>
                  <TableCell>
                    {existing && !isEditing && (
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={isPending}
                        onClick={() => setDeleteTarget(existing)}
                        aria-label={`Delete rate for ${currency.code}`}
                      >
                        <Trash2Icon className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={deleteTarget !== null}
        onOpenChange={(open) => {
          if (!open) {
            deleteMutation.reset();
            setDeleteTarget(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete exchange rate</DialogTitle>
            <DialogDescription>
              Delete the {deleteTarget?.currency_code} rate for{" "}
              {deleteTarget ? formatMonthLabel(deleteTarget.month) : ""}? This
              cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteTarget(null)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              disabled={deleteMutation.isPending}
              onClick={() => {
                if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
              }}
            >
              {deleteMutation.isPending ? "Deleting…" : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
