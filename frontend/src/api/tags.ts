import { client } from "./client";

export interface Tag {
  id: number;
  name: string;
}

export interface TagCreate {
  name: string;
}

export interface TagUpdate {
  name: string;
}

export const listTags = () => client.get<Tag[]>("/tags");
export const createTag = (body: TagCreate) => client.post<Tag>("/tags", body);
export const updateTag = (id: number, body: TagUpdate) =>
  client.put<Tag>(`/tags/${id}`, body);
export const deleteTag = (id: number) => client.del(`/tags/${id}`);
