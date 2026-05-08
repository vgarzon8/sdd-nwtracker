import { client } from "./client";

export interface Currency {
  code: string;
  name: string;
}

export interface CurrencyCreate {
  code: string;
  name: string;
}

export const listCurrencies = () => client.get<Currency[]>("/currencies");
export const createCurrency = (body: CurrencyCreate) =>
  client.post<Currency>("/currencies", body);
export const deleteCurrency = (code: string) =>
  client.del(`/currencies/${code}`);
