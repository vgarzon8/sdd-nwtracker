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

export interface RollForwardMonthResult {
  month: string;
  inserted: number;
  skipped: number;
}

export interface RollForwardResponse {
  months: RollForwardMonthResult[];
}

export interface TransferRequest {
  from_account_id: number;
  to_account_id: number;
  amount: number;
  month: string;
}

export interface TransferResponse {
  from_balance: Balance;
  to_balance: Balance;
}

export const listBalancesFlat = () => client.get<Balance[]>("/balances");
export const listBalancesByMonth = (month: string) =>
  client.get<BalanceDetail[]>(`/balances?month=${month}`);
export const createBalance = (body: BalanceCreate) =>
  client.post<Balance>("/balances", body);
export const updateBalance = (id: number, body: BalanceUpdate) =>
  client.put<Balance>(`/balances/${id}`, body);
export const rollForward = (month: string) =>
  client.post<RollForwardResponse>("/balances/roll-forward", { month });
export const transfer = (body: TransferRequest) =>
  client.post<TransferResponse>("/balances/transfer", body);
