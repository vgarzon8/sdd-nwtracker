import { client } from "./client";

export interface Institution {
  id: number;
  name: string;
}

export interface InstitutionCreate {
  name: string;
}

export interface InstitutionUpdate {
  name: string;
}

export interface InstitutionDeletePreview {
  accounts_to_delete: number;
  balances_to_delete: number;
}

export const listInstitutions = () => client.get<Institution[]>("/institutions");
export const createInstitution = (body: InstitutionCreate) =>
  client.post<Institution>("/institutions", body);
export const updateInstitution = (id: number, body: InstitutionUpdate) =>
  client.put<Institution>(`/institutions/${id}`, body);
export const deleteInstitutionPreview = (id: number) =>
  client.del_json<InstitutionDeletePreview>(`/institutions/${id}`);
export const deleteInstitutionConfirm = (id: number) =>
  client.del(`/institutions/${id}?confirm=true`);
