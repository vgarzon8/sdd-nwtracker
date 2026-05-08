import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon, Trash2Icon } from "lucide-react";
import {
  listCurrencies,
  createCurrency,
  deleteCurrency,
  type Currency,
} from "@/api/currencies";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
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

export default function CurrenciesPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("");
  const [addOpen, setAddOpen] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<Currency | null>(null);
  const [formCode, setFormCode] = useState("");
  const [formName, setFormName] = useState("");
  const [formError, setFormError] = useState("");

  const { data: currencies = [], isLoading } = useQuery({
    queryKey: ["currencies"],
    queryFn: listCurrencies,
  });

  const createMutation = useMutation({
    mutationFn: createCurrency,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currencies"] });
      setAddOpen(false);
      setFormCode("");
      setFormName("");
      setFormError("");
    },
    onError: (err: Error) => {
      setFormError(err.message);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCurrency,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["currencies"] });
      setDeleteTarget(null);
    },
  });

  const filtered = currencies.filter((c) => {
    const q = filter.toLowerCase();
    return c.code.toLowerCase().includes(q) || c.name.toLowerCase().includes(q);
  });

  function openAdd() {
    setFormCode("");
    setFormName("");
    setFormError("");
    setAddOpen(true);
  }

  function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    createMutation.mutate({ code: formCode.trim().toUpperCase(), name: formName.trim() });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Currencies</h1>
        <Button onClick={openAdd}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Add currency
        </Button>
      </div>

      <Input
        placeholder="Filter currencies…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="max-w-sm"
      />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          {currencies.length === 0 ? (
            <>
              <p>No currencies yet.</p>
              <Button variant="link" onClick={openAdd}>
                Add one to get started
              </Button>
            </>
          ) : (
            <p>No currencies match your filter.</p>
          )}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-24">Code</TableHead>
              <TableHead>Name</TableHead>
              <TableHead className="w-16" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((c) => (
              <TableRow key={c.code}>
                <TableCell>
                  <Badge variant="secondary">{c.code}</Badge>
                </TableCell>
                <TableCell>{c.name}</TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteTarget(c)}
                    aria-label={`Delete ${c.code}`}
                  >
                    <Trash2Icon className="h-4 w-4 text-destructive" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Add dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add currency</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAdd} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="code">Code</Label>
              <Input
                id="code"
                placeholder="USD"
                value={formCode}
                onChange={(e) => setFormCode(e.target.value)}
                required
                maxLength={10}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="US Dollar"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
              />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setAddOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending ? "Saving…" : "Save"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete confirmation */}
      <AlertDialog
        open={deleteTarget !== null}
        onOpenChange={(open) => !open && setDeleteTarget(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete {deleteTarget?.code}?</AlertDialogTitle>
            <AlertDialogDescription>
              This cannot be undone. Currencies referenced by accounts or exchange
              rates cannot be deleted.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.code)}
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
