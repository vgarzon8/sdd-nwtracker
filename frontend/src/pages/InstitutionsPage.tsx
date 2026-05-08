import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PlusIcon, PencilIcon, Trash2Icon } from "lucide-react";
import {
  listInstitutions,
  createInstitution,
  updateInstitution,
  deleteInstitutionPreview,
  deleteInstitutionConfirm,
  type Institution,
  type InstitutionDeletePreview,
} from "@/api/institutions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
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
  institution: Institution;
  preview: InstitutionDeletePreview;
}

export default function InstitutionsPage() {
  const queryClient = useQueryClient();
  const [filter, setFilter] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Institution | null>(null);
  const [deleteState, setDeleteState] = useState<DeleteState | null>(null);
  const [formName, setFormName] = useState("");
  const [formError, setFormError] = useState("");

  const { data: institutions = [], isLoading } = useQuery({
    queryKey: ["institutions"],
    queryFn: listInstitutions,
  });

  const createMutation = useMutation({
    mutationFn: createInstitution,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
      closeForm();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, name }: { id: number; name: string }) =>
      updateInstitution(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
      closeForm();
    },
    onError: (err: Error) => setFormError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteInstitutionConfirm,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["institutions"] });
      setDeleteState(null);
    },
  });

  const filtered = institutions.filter((i) =>
    i.name.toLowerCase().includes(filter.toLowerCase()),
  );

  function openAdd() {
    setEditTarget(null);
    setFormName("");
    setFormError("");
    setFormOpen(true);
  }

  function openEdit(institution: Institution) {
    setEditTarget(institution);
    setFormName(institution.name);
    setFormError("");
    setFormOpen(true);
  }

  function closeForm() {
    setFormOpen(false);
    setEditTarget(null);
    setFormName("");
    setFormError("");
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError("");
    const name = formName.trim();
    if (editTarget) {
      updateMutation.mutate({ id: editTarget.id, name });
    } else {
      createMutation.mutate({ name });
    }
  }

  async function handleDeleteClick(institution: Institution) {
    try {
      const preview = await deleteInstitutionPreview(institution.id);
      setDeleteState({ institution, preview });
    } catch (err) {
      console.error("Failed to load delete preview:", err);
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;
  const { institution: del, preview } = deleteState ?? {};

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Institutions</h1>
        <Button onClick={openAdd}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Add institution
        </Button>
      </div>

      <Input
        placeholder="Filter institutions…"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        className="max-w-sm"
      />

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : filtered.length === 0 ? (
        <div className="text-center py-16 text-muted-foreground">
          {institutions.length === 0 ? (
            <>
              <p>No institutions yet.</p>
              <Button variant="link" onClick={openAdd}>
                Add one to get started
              </Button>
            </>
          ) : (
            <p>No institutions match your filter.</p>
          )}
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead className="w-24" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {filtered.map((inst) => (
              <TableRow key={inst.id}>
                <TableCell>{inst.name}</TableCell>
                <TableCell>
                  <div className="flex items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => openEdit(inst)}
                      aria-label={`Edit ${inst.name}`}
                    >
                      <PencilIcon className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteClick(inst)}
                      aria-label={`Delete ${inst.name}`}
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
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editTarget ? "Edit institution" : "Add institution"}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="inst-name">Name</Label>
              <Input
                id="inst-name"
                placeholder="Chase"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                required
              />
            </div>
            {formError && <p className="text-sm text-destructive">{formError}</p>}
            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeForm}>
                Cancel
              </Button>
              <Button type="submit" disabled={isPending}>
                {isPending ? "Saving…" : "Save"}
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
            <AlertDialogTitle>Delete "{del?.name}"?</AlertDialogTitle>
            <AlertDialogDescription>
              {preview && (preview.accounts_to_delete > 0 || preview.balances_to_delete > 0) ? (
                <>
                  This will also delete{" "}
                  <strong>{preview.accounts_to_delete} account(s)</strong> and{" "}
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
