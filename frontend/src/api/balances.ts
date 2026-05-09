import { client } from "./client";

export type BalanceSide = "asset" | "liability";

export interface Balance {
  id: number;
  account_id: number;
  month: string;
  amount: number;
}

export interface BalanceDetail {
  id: number;
  account_id: number;
  month: string;
  amount: number;
  account_name: string;
  institution_id: number;
  currency_code: string;
  side: BalanceSide;
}

export interface BalanceCreate {
  account_id: number;
  month: string;
  amount: number;
}

export interface BalanceUpdate {
  amount: number;
}

export const listBalancesFlat = () => client.get<Balance[]>("/balances");
export const listBalancesByMonth = (month: string) =>
  client.get<BalanceDetail[]>(`/balances?month=${month}`);
export const createBalance = (body: BalanceCreate) =>
  client.post<Balance>("/balances", body);
export const updateBalance = (id: number, body: BalanceUpdate) =>
  client.put<Balance>(`/balances/${id}`, body);
