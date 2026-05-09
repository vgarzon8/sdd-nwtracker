import { client } from "./client";

export interface BalanceSummaryItem {
  group_key: string | null;
  balance_sum_usd: number;
}

export const getBalanceSummaryBySide = (month: string) =>
  client.get<BalanceSummaryItem[]>(
    `/reports/balance-summary?attribute=side&month=${month}`,
  );
