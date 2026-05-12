export type CsvFormat = "friendly" | "raw";

export interface TableCounts {
  inserted: number;
  updated: number;
}

export interface ImportResult {
  imported: Record<string, TableCounts>;
  skipped: Record<string, number>;
  warnings: string[];
}

export interface ImportError {
  messages: string[];
}

export function triggerExport(format: CsvFormat = "friendly"): void {
  const url =
    format === "raw" ? "/api/export?format=raw" : "/api/export";
  window.location.href = url;
}

function parseImportError(detail: unknown): string[] {
  if (typeof detail === "string") return [detail];
  if (detail && typeof detail === "object") {
    const d = detail as Record<string, unknown>;
    if (Array.isArray(d.errors)) return d.errors as string[];
    if (typeof d.message === "string") {
      const base = d.message;
      if (Array.isArray(d.missing))
        return [`${base}: ${(d.missing as string[]).join(", ")}`];
      return [base];
    }
  }
  return ["Import failed. Please check the file and try again."];
}

export async function importCsv(
  file: File,
  format: CsvFormat = "friendly",
): Promise<ImportResult> {
  const body = new FormData();
  body.append("file", file);

  const url =
    format === "raw" ? "/api/import?format=raw" : "/api/import";
  const res = await fetch(url, { method: "POST", body });

  if (!res.ok) {
    let messages: string[];
    try {
      const json = (await res.json()) as { detail?: unknown };
      messages = parseImportError(json.detail);
    } catch {
      messages = [`Import failed: ${res.statusText}`];
    }
    const err: ImportError = { messages };
    throw err;
  }

  return res.json() as Promise<ImportResult>;
}
