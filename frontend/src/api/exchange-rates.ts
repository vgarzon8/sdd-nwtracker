import { client } from "./client";

export interface ExchangeRate {
  id: number;
  currency_code: string;
  month: string;
  rate: number;
}

export const listExchangeRates = (month: string) =>
  client.get<ExchangeRate[]>(`/exchange-rates?month=${month}`);
