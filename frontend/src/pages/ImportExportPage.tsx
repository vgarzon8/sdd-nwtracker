import { useRef, useState } from "react";
import {
  triggerExport,
  importCsv,
  type ImportResult,
  type ImportError,
} from "@/api/csv";
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

const TABLE_LABELS: Record<string, string> = {
  currencies: "Currencies",
  tags: "Tags",
  institutions: "Institutions",
  accounts: "Accounts",
  balances: "Balances",
  exchange_rates: "Exchange Rates",
};

export default function ImportExportPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  function reset() {
    setFile(null);
    setResult(null);
    setErrors([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

  async function handleImport() {
    if (!file) return;
    setImporting(true);
    setResult(null);
    setErrors([]);
    try {
      const res = await importCsv(file);
      setResult(res);
    } catch (err) {
      const importErr = err as ImportError;
      setErrors(importErr.messages ?? ["Import failed."]);
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="space-y-10">
      <h1 className="text-2xl font-semibold">Import / Export</h1>

      {/* Export */}
      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-medium">Export</h2>
          <p className="text-sm text-muted-foreground">
            Download all data as a ZIP of CSV files.
          </p>
        </div>
        <Button variant="outline" onClick={triggerExport}>
          Export
        </Button>
      </section>

      {/* Import */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-medium">Import</h2>
          <p className="text-sm text-muted-foreground">
            Upload a ZIP file containing all CSV tables. Existing rows are
            updated; new rows are inserted.
          </p>
        </div>

        {result ? (
          <div className="space-y-4">
            <p className="font-medium">Import complete</p>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Table</TableHead>
                  <TableHead className="text-right">Inserted</TableHead>
                  <TableHead className="text-right">Updated</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(result.imported).map(([key, counts]) => (
                  <TableRow key={key}>
                    <TableCell>{TABLE_LABELS[key] ?? key}</TableCell>
                    <TableCell className="text-right">
                      {counts.inserted}
                    </TableCell>
                    <TableCell className="text-right">
                      {counts.updated}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            <Button variant="outline" onClick={reset}>
              Import another file
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            <Input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              className="max-w-sm"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
            {errors.length > 0 && (
              <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-4 space-y-1">
                {errors.map((msg, i) => (
                  <p key={i} className="text-sm text-destructive">
                    {msg}
                  </p>
                ))}
              </div>
            )}
            <Button
              disabled={!file || importing}
              onClick={handleImport}
            >
              {importing ? "Importing…" : "Import"}
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
