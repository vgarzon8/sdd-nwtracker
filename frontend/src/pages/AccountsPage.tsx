import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon, PencilIcon, Trash2Icon } from "lucide-react";
import {
  listAccounts,
  createAccount,
  updateAccount,
  deleteAccountPreview,
  deleteAccountConfirm,
  type Account,
  type AccountSide,
  type AccountStatus,
  type AccountDeletePreview,
} from "@/api/accounts";
import { listInstitutions } from "@/api/institutions";
import { listCurrencies } from "@/api/currencies";
import { listTags } from "@/api/tags";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DeleteState {
  account: Account;
  preview: AccountDeletePreview;
}

interface FormState {
  name: string;
  institution_id: string;
  currency_code: string;
  side: string;
  status: string;
  tag_ids: number[];
}

const emptyForm = (): FormState => ({
  name: "",
  institution_id: "",
  currency_code: "",
  side: "",
  status: "active" as AccountStatus,
  tag_ids: [],
});

interface FieldErrors {
  name?: string;
  institution_id?: string;
  currency_code?: string;
  side?: string;
}

export default function AccountsPage() {
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<AccountStatus | "all">("all");
  const [tagFilter, setTagFilter] = useState<string | "all">("all");
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Account | null>(null);
  const [deleteState, setDeleteState] = useState<DeleteState | null>(null);
  const [form, setForm] = useState<FormState>(emptyForm());
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");

  const { data: accounts = [], isLoading } = useQuery({
    queryKey: ["accounts"],
    queryFn: listAccounts,
  });

  const { data: institutions = [] } = useQuery({
    queryKey: ["institutions"],
    queryFn: listInstitutions,
  });

  const { data: currencies = [] } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
  });

  const { data: tags = [] } = useQuery({
    queryKey: ["tags"],
    queryFn: listTags,
  });

  const createMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      closeForm();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: number; body: Parameters<typeof updateAccount>[1] }) =>
      updateAccount(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      closeForm();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccountConfirm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["accounts"] });
      setDeleteState(null);
    },
  });

  const filtered = accounts.filter((a) => {
    if (statusFilter !== "all" && a.status !== statusFilter) return false;
    if (tagFilter !== "all" && !a.tag_ids.includes(Number(tagFilter))) return false;
    return true;
  });

  function openAdd() {
    setEditTarget(null);
    setForm(emptyForm());
    setFieldErrors({});
    setFormError("");
    setFormOpen(true);
  }

  function openEdit(account: Account) {
    setEditTarget(account);
    setForm({
      name: account.name,
      institution_id: String(account.institution_id),
      currency_code: account.currency_code,
      side: account.side,
      status: account.status,
      tag_ids: account.tag_ids,
    });
    setFieldErrors({});
    setFormError("");
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditTarget(null);
    setForm(emptyForm());
    setFieldErrors({});
    setFormError("");
  }

  function validate(): boolean {
    const errors: FieldErrors = {};
    if (!form.name.trim()) errors.name = "Name is required.";
    if (!form.institution_id) errors.institution_id = "Select an institution.";
    if (!form.currency_code) errors.currency_code = "Select a currency.";
    if (!form.side) errors.side = "Select a side.";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    if (!validate()) return;
    const body = {
      name: form.name.trim(),
      institution_id: Number(form.institution_id),
      currency_code: form.currency_code,
      side: form.side as AccountSide,
      status: form.status as AccountStatus,
      tag_ids: form.tag_ids,
    };
    if (editTarget) {
      updateMutation.mutate({ id: editTarget.id, body });
    } else {
      createMutation.mutate(body);
    }
  }

  async function handleDeleteClick(account: Account) {
    try {
      const preview = await deleteAccountPreview(account.id);
      setDeleteState({ account, preview });
    } catch (err) {
      console.error("Failed to load delete preview:", err);
    }
  }

  function toggleTag(tagId: number) {
    setForm((f) => ({
      ...f,
      tag_ids: f.tag_ids.includes(tagId)
        ? f.tag_ids.filter((id) => id !== tagId)
        : [...f.tag_ids, tagId],
    }));
  }

  const institutionName = (id: number) =>
    institutions.find((i) => i.id === id)?.name ?? String(id);

  const tagName = (id: number) =>
    tags.find((t) => t.id === id)?.name ?? String(id);

  const isPending = createMutation.isPending || updateMutation.isPending;
  const { account: del, preview } = deleteState ?? {};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Accounts</h1>
        <Button onClick={openAdd}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Add account
        </Button>
      </div>

      <div className="flex items-center gap-3">
        <Select value={statusFilter} onValueChange={(v) => setStatusFilter(v as AccountStatus | "all")}>
          <SelectTrigger className="w-36">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All statuses</SelectItem>
            <SelectItem value="active">Active</SelectItem>
            <SelectItem value="closed">Closed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={tagFilter} onValueChange={setTagFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Tag" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All tags</SelectItem>
            {tags.map((t) => (
              <SelectItem key={t.id} value={String(t.id)}>
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : accounts.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p>No accounts yet.</p>
          <Button variant="link" onClick={openAdd}>
            Add account
          </Button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          <p>No accounts match the selected filters.</p>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Institution</TableHead>
              <TableHead>Currency</TableHead>
              <TableHead>Side</TableHead>
              <TableHead>Tags</TableHead>
              <TableHead className="w-24" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((account) => (
              <TableRow
                key={account.id}
                className={account.status === "closed" ? "opacity-50" : ""}
              >
                <TableCell>{account.name}</TableCell>
                <TableCell>{institutionName(account.institution_id)}</TableCell>
                <TableCell>{account.currency_code}</TableCell>
                <TableCell className="capitalize">{account.side}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {account.tag_ids.map((id) => (
                      <Badge key={id} variant="secondary">
                        {tagName(id)}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => openEdit(account)}
                      aria-label={`Edit ${account.name}`}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteClick(account)}
                      aria-label={`Delete ${account.name}`}
                    >
                      <Trash2Icon className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Create / edit dialog */}
      <Dialog open={formOpen} onOpenChange={(open) => !open && closeForm()}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editTarget ? "Edit account" : "Add account"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="acct-name">Name</Label>
              <Input
                id="acct-name"
                placeholder="Savings"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
              />
              {fieldErrors.name && (
                <p className="text-sm text-destructive">{fieldErrors.name}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="acct-institution">Institution</Label>
              <Select
                value={form.institution_id}
                onValueChange={(v) => setForm((f) => ({ ...f, institution_id: v }))}
              >
                <SelectTrigger id="acct-institution">
                  <SelectValue placeholder="Select institution" />
                </SelectTrigger>
                <SelectContent>
                  {institutions.map((i) => (
                    <SelectItem key={i.id} value={String(i.id)}>
                      {i.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {fieldErrors.institution_id && (
                <p className="text-sm text-destructive">{fieldErrors.institution_id}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="acct-currency">Currency</Label>
              <Select
                value={form.currency_code}
                onValueChange={(v) => setForm((f) => ({ ...f, currency_code: v }))}
              >
                <SelectTrigger id="acct-currency">
                  <SelectValue placeholder="Select currency" />
                </SelectTrigger>
                <SelectContent>
                  {currencies.map((c) => (
                    <SelectItem key={c.code} value={c.code}>
                      {c.code} — {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {fieldErrors.currency_code && (
                <p className="text-sm text-destructive">{fieldErrors.currency_code}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="acct-side">Side</Label>
              <Select
                value={form.side}
                onValueChange={(v) => setForm((f) => ({ ...f, side: v }))}
              >
                <SelectTrigger id="acct-side">
                  <SelectValue placeholder="Select side" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="asset">Asset</SelectItem>
                  <SelectItem value="liability">Liability</SelectItem>
                </SelectContent>
              </Select>
              {fieldErrors.side && (
                <p className="text-sm text-destructive">{fieldErrors.side}</p>
              )}
            </div>

            <div className="space-y-1">
              <Label htmlFor="acct-status">Status</Label>
              <Select
                value={form.status}
                onValueChange={(v) => setForm((f) => ({ ...f, status: v }))}
              >
                <SelectTrigger id="acct-status">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="active">Active</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {tags.length > 0 && (
              <div className="space-y-2">
                <Label>Tags</Label>
                <div className="space-y-2">
                  {tags.map((t) => (
                    <div key={t.id} className="flex items-center gap-2">
                      <Checkbox
                        id={`tag-${t.id}`}
                        checked={form.tag_ids.includes(t.id)}
                        onCheckedChange={() => toggleTag(t.id)}
                      />
                      <Label htmlFor={`tag-${t.id}`} className="font-normal cursor-pointer">
                        {t.name}
                      </Label>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {formError && (
              <p className="text-sm text-destructive">{formError}</p>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeForm}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending
                  ? "Saving…"
                  : editTarget
                    ? "Save changes"
                    : "Add account"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Cascade delete confirmation */}
      <AlertDialog
        open={deleteState !== null}
        onOpenChange={(open) => !open && setDeleteState(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete account "{del?.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              {preview && preview.balances_to_delete > 0 ? (
                <>
                  This will also delete{" "}
                  <strong>{preview.balances_to_delete} balance(s)</strong>. This
                  cannot be undone.
                </>
              ) : (
                "This cannot be undone."
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => del && deleteMutation.mutate(del.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
