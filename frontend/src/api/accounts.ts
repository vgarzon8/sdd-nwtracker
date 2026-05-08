import { client } from "./client";

export type AccountSide = "asset" | "liability";
export type AccountStatus = "active" | "inactive";

export interface Account {
  id: number;
  name: string;
  institution_id: number;
  currency_code: string;
  side: AccountSide;
  status: AccountStatus;
  tag_ids: number[];
}

export interface AccountCreate {
  name: string;
  institution_id: number;
  currency_code: string;
  side: AccountSide;
  status: AccountStatus;
  tag_ids: number[];
}

export interface AccountUpdate {
  name?: string;
  institution_id?: number;
  currency_code?: string;
  side?: AccountSide;
  status?: AccountStatus;
  tag_ids?: number[];
}

export interface AccountDeletePreview {
  balances_to_delete: number;
}

export const listAccounts = () => client.get<Account[]>("/accounts");
export const createAccount = (body: AccountCreate) =>
  client.post<Account>("/accounts", body);
export const updateAccount = (id: number, body: AccountUpdate) =>
  client.put<Account>(`/accounts/${id}`, body);
export const deleteAccountPreview = (id: number) =>
  client.del_json<AccountDeletePreview>(`/accounts/${id}`);
export const deleteAccountConfirm = (id: number) =>
  client.del(`/accounts/${id}?confirm=true`);
