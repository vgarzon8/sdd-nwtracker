import { client } from "./client";

export interface ExchangeRate {
  id: number;
  currency_code: string;
  month: string;
  rate: number;
}

export interface ExchangeRateCreate {
  currency_code: string;
  month: string;
  rate: number;
}

export interface ExchangeRateUpdate {
  rate: number;
}

export const listExchangeRates = (month: string) =>
  client.get<ExchangeRate[]>(`/exchange-rates?month=${month}`);

export const createExchangeRate = (body: ExchangeRateCreate) =>
  client.post<ExchangeRate>("/exchange-rates", body);

export const updateExchangeRate = (id: number, body: ExchangeRateUpdate) =>
  client.put<ExchangeRate>(`/exchange-rates/${id}`, body);

export const deleteExchangeRate = (id: number) =>
  client.del(`/exchange-rates/${id}`);
