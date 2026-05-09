import { useMemo, useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react";
import {
  listBalancesFlat,
  listBalancesByMonth,
  createBalance,
  updateBalance,
  rollForward,
  type BalanceDetail,
} from "@/api/balances";
import { listAccounts, type Account } from "@/api/accounts";
import { listInstitutions } from "@/api/institutions";
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

interface MergedRow {
  account: Account;
  balance: BalanceDetail | null;
}

interface EditState {
  key: string;
  value: string;
}

export default function BalancesPage() {
  const queryClient = useQueryClient();
  // null = user hasn't navigated yet; derive default from data
  const [selectedMonth, setSelectedMonth] = useState<string | null>(null);
  const [editState, setEditState] = useState<EditState | null>(null);
  const [saveErrors, setSaveErrors] = useState<Record<string, string>>({});
  const [rollForwardOpen, setRollForwardOpen] = useState(false);
  const [rollForwardError, setRollForwardError] = useState<string | null>(null);

  const { data: allBalances = [] } = useQuery({
    queryKey: ["balances-months"],
    queryFn: listBalancesFlat,
  });

  // Derive the default month from data without an effect
  const defaultMonth = useMemo(() => {
    if (allBalances.length === 0) return currentCalendarMonth();
    return allBalances.reduce(
      (max, b) => (b.month > max ? b.month : max),
      allBalances[0].month,
    );
  }, [allBalances]);

  const effectiveMonth = selectedMonth ?? defaultMonth;

  const { data: monthBalances = [] } = useQuery({
    queryKey: ["balances", effectiveMonth],
    queryFn: () => listBalancesByMonth(effectiveMonth),
  });

  const { data: accounts = [] } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

  const { data: institutions = [] } = useQuery({
    queryKey: ["institutions"],
    queryFn: listInstitutions,
  });

  const invalidateBalances = () => {
    queryClient.invalidateQueries({ queryKey: ["balances", effectiveMonth] });
    queryClient.invalidateQueries({ queryKey: ["balances-months"] });
  };

  const sourceMonth = useMemo(() => {
    const prior = allBalances
      .map((b) => b.month)
      .filter((m) => m < effectiveMonth);
    if (prior.length === 0) return undefined;
    return prior.reduce((max, m) => (m > max ? m : max));
  }, [allBalances, effectiveMonth]);

  const rollForwardMutation = useMutation({
    mutationFn: () => rollForward(effectiveMonth),
    onSuccess: () => {
      invalidateBalances();
      setRollForwardOpen(false);
      setRollForwardError(null);
    },
    onError: (err: Error) => {
      setRollForwardError(err.message || "Roll-forward failed.");
    },
  });

  const createMutation = useMutation({
    mutationFn: (vars: { body: Parameters<typeof createBalance>[0]; key: string }) =>
      createBalance(vars.body),
    onSuccess: () => {
      invalidateBalances();
      setEditState(null);
    },
    onError: (_err: Error, vars) => {
      setSaveErrors((prev) => ({ ...prev, [vars.key]: "Failed to save." }));
    },
  });

  const updateMutation = useMutation({
    mutationFn: (vars: { id: number; amount: number; key: string }) =>
      updateBalance(vars.id, { amount: vars.amount }),
    onSuccess: () => {
      invalidateBalances();
      setEditState(null);
    },
    onError: (_err: Error, vars) => {
      setSaveErrors((prev) => ({ ...prev, [vars.key]: "Failed to save." }));
    },
  });

  const activeAccounts = accounts
    .filter((a) => a.status === "active")
    .sort((a, b) => a.name.localeCompare(b.name));

  const institutionName = (id: number) =>
    institutions.find((i) => i.id === id)?.name ?? String(id);

  const rows: MergedRow[] = activeAccounts.map((account) => ({
    account,
    balance: monthBalances.find((b) => b.account_id === account.id) ?? null,
  }));

  function rowKey(row: MergedRow): string {
    return row.balance ? String(row.balance.id) : `new-${row.account.id}`;
  }

  function startEdit(row: MergedRow) {
    const key = rowKey(row);
    setSaveErrors((prev) => {
      const next = { ...prev };
      delete next[key];
      return next;
    });
    setEditState({
      key,
      value: row.balance !== null ? String(row.balance.amount) : "",
    });
  }

  function commitEdit(row: MergedRow) {
    if (!editState) return;
    const trimmed = editState.value.trim();

    // No value entered — cancel
    if (trimmed === "") {
      setEditState(null);
      return;
    }

    const amount = parseInt(trimmed, 10);
    if (isNaN(amount)) {
      setEditState(null);
      return;
    }

    // Unchanged — skip
    if (row.balance && amount === row.balance.amount) {
      setEditState(null);
      return;
    }

    const key = editState.key;
    if (row.balance) {
      updateMutation.mutate({ id: row.balance.id, amount, key });
    } else {
      createMutation.mutate({
        body: { account_id: row.account.id, month: effectiveMonth, amount },
        key,
      });
    }
  }

  function handleKeyDown(e: React.KeyboardEvent, row: MergedRow) {
    if (e.key === "Enter") {
      e.preventDefault();
      commitEdit(row);
    } else if (e.key === "Escape") {
      setEditState(null);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Balances</h1>
        <div className="flex gap-2">
          <Button
            variant="outline"
            disabled={!sourceMonth}
            onClick={() => {
              setRollForwardError(null);
              setRollForwardOpen(true);
            }}
          >
            Roll forward
          </Button>
        </div>
      </div>

      <Dialog
        open={rollForwardOpen}
        onOpenChange={(open) => {
          if (!open) {
            setRollForwardError(null);
            rollForwardMutation.reset();
          }
          setRollForwardOpen(open);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Roll forward to {formatMonthLabel(effectiveMonth)}
            </DialogTitle>
            <DialogDescription>
              {sourceMonth
                ? `Copies ${formatMonthLabel(sourceMonth)} balances for ${
                    rows.filter((r) => r.balance === null).length
                  } active account(s) with no ${formatMonthLabel(effectiveMonth)} entry.`
                : "No prior month with data found."}
            </DialogDescription>
          </DialogHeader>
          {rollForwardError && (
            <p className="text-sm text-destructive">{rollForwardError}</p>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setRollForwardOpen(false)}
              disabled={rollForwardMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={() => rollForwardMutation.mutate()}
              disabled={rollForwardMutation.isPending || !sourceMonth}
            >
              {rollForwardMutation.isPending ? "Rolling forward…" : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

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

      {activeAccounts.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p>No active accounts found.</p>
          <a href="/accounts" className="text-sm underline">
            Go to Accounts
          </a>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account</TableHead>
              <TableHead>Institution</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Amount</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => {
              const key = rowKey(row);
              const isEditing = editState?.key === key;
              const isPending =
                createMutation.isPending || updateMutation.isPending;
              const error = saveErrors[key];

              return (
                <TableRow key={key}>
                  <TableCell>{row.account.name}</TableCell>
                  <TableCell>
                    {institutionName(row.account.institution_id)}
                  </TableCell>
                  <TableCell>{row.account.currency_code}</TableCell>
                  <TableCell className="capitalize">
                    {row.balance?.side ?? row.account.side}
                  </TableCell>
                  <TableCell className="text-right">
                    {isEditing ? (
                      <div className="flex flex-col items-end gap-1">
                        <Input
                          autoFocus
                          type="number"
                          className="w-36 text-right"
                          value={editState.value}
                          disabled={isPending}
                          onFocus={(e) => e.target.select()}
                          onChange={(e) =>
                            setEditState((s) =>
                              s ? { ...s, value: e.target.value } : s
                            )
                          }
                          onBlur={() => commitEdit(row)}
                          onKeyDown={(e) => handleKeyDown(e, row)}
                        />
                        {error && (
                          <p className="text-xs text-destructive">{error}</p>
                        )}
                      </div>
                    ) : (
                      <button
                        className="w-full text-right cursor-pointer hover:underline"
                        onClick={() => startEdit(row)}
                        aria-label={`Edit amount for ${row.account.name}`}
                      >
                        {row.balance !== null
                          ? row.balance.amount.toLocaleString()
                          : "—"}
                      </button>
                    )}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
