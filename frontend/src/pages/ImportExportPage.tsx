import { useRef, useState } from "react";
import {
  triggerExport,
  importCsv,
  type CsvFormat,
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
  account_tags: "Account Tags",
  balances: "Balances",
  exchange_rates: "Exchange Rates",
};

const FORMAT_DESCRIPTIONS: Record<CsvFormat, { subtitle: string }> = {
  friendly: {
    subtitle:
      "Human-readable names, no IDs. Best for manual editing or migration.",
  },
  raw: {
    subtitle:
      "Schema-aligned with IDs and foreign keys. Best for backup and restore.",
  },
};

export default function ImportExportPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [format, setFormat] = useState<CsvFormat>("friendly");
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  function handleFormatChange(next: CsvFormat) {
    setFormat(next);
    setFile(null);
    setResult(null);
    setErrors([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  }

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
      const res = await importCsv(file, format);
      setResult(res);
    } catch (err) {
      const importErr = err as ImportError;
      setErrors(importErr.messages ?? ["Import failed."]);
    } finally {
      setImporting(false);
    }
  }

  const hasSkipped =
    result != null &&
    Object.values(result.skipped ?? {}).some((n) => n > 0);

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Import / Export</h1>

      {/* Format toggle */}
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">
          Format:
        </span>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant={format === "friendly" ? "default" : "outline"}
            onClick={() => handleFormatChange("friendly")}
          >
            User-friendly
          </Button>
          <Button
            size="sm"
            variant={format === "raw" ? "default" : "outline"}
            onClick={() => handleFormatChange("raw")}
          >
            Raw
          </Button>
        </div>
      </div>

      {/* Export */}
      <section className="space-y-3">
        <div>
          <h2 className="text-lg font-medium">Export</h2>
          <p className="text-sm text-muted-foreground">
            {FORMAT_DESCRIPTIONS[format].subtitle}
          </p>
        </div>
        <Button variant="outline" onClick={() => triggerExport(format)}>
          Export
        </Button>
      </section>

      {/* Import */}
      <section className="space-y-4">
        <div>
          <h2 className="text-lg font-medium">Import</h2>
          <p className="text-sm text-muted-foreground">
            {FORMAT_DESCRIPTIONS[format].subtitle} Existing rows are updated;
            new rows are inserted.
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
                  {hasSkipped && (
                    <TableHead className="text-right">Skipped</TableHead>
                  )}
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
                    {hasSkipped && (
                      <TableCell className="text-right">
                        {result.skipped?.[key] ?? 0}
                      </TableCell>
                    )}
                  </TableRow>
                ))}
              </TableBody>
            </Table>
            {result.warnings && result.warnings.length > 0 && (
              <div className="rounded-lg border border-yellow-500/50 bg-yellow-500/10 p-4 space-y-1">
                <p className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                  {result.warnings.length} warning
                  {result.warnings.length !== 1 ? "s" : ""}
                </p>
                <ul className="list-disc list-inside space-y-0.5">
                  {result.warnings.map((msg, i) => (
                    <li key={i} className="text-sm text-yellow-700 dark:text-yellow-400">
                      {msg}
                    </li>
                  ))}
                </ul>
              </div>
            )}
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
            <Button disabled={!file || importing} onClick={handleImport}>
              {importing ? "Importing…" : "Import"}
            </Button>
          </div>
        )}
      </section>
    </div>
  );
}
