import { client } from "./client";

export interface BalanceSummaryItem {
  group_key: string | null;
  balance_sum_usd: number;
}

export interface BalanceSummaryHistoryItem {
  month: string;
  group_key: string | number | null;
  balance_sum_usd: number;
}

export interface BalanceSummaryHistoryResponse {
  from_month: string;
  to_month: string;
  items: BalanceSummaryHistoryItem[];
}

export const getBalanceSummaryBySide = (month: string) =>
  client.get<BalanceSummaryItem[]>(
    `/reports/balance-summary?attribute=side&month=${month}`,
  );

export const getBalanceSummaryByTags = (month: string) =>
  client.get<BalanceSummaryItem[]>(
    `/reports/balance-summary?attribute=tags&month=${month}`,
  );

export const getBalanceSummaryHistory = (from: string, to: string) =>
  client.get<BalanceSummaryHistoryResponse>(
    `/reports/balance-summary/history?attribute=side&from=${from}&to=${to}`,
  );
