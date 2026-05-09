import { client } from "./client";

export interface BalanceSummaryItem {
  group_key: string | null;
  balance_sum_usd: number;
}

export interface BalanceSummaryHistoryItem {
  month: string;
  group_key: string | null;
  balance_sum_usd: number;
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
  client.get<BalanceSummaryHistoryItem[]>(
    `/reports/balance-summary/history?attribute=side&from=${from}&to=${to}`,
  );
